"""
Multi-User Collaboration Server
=================================
Allows two users to share one virtual mouse session over a network.
User A controls cursor; User B sees the cursor in real time (or vice-versa).

Start the server:
    python -m src.collaboration_server            # default port 8765
    python -m src.collaboration_server --port 9000

Connect from main.py by setting in config/settings.json:
    "collaboration_enabled": true,
    "collaboration_host": "ws://SERVER_IP:8765",
    "collaboration_role": "host"   # or "guest"

Protocol (JSON over WebSocket):
  client → server:  {"type":"cursor","x":0.5,"y":0.4,"gesture":"MOVE","room":"abc"}
  server → others:  {"type":"cursor","x":0.5,"y":0.4,"gesture":"MOVE","from":"host"}
  client → server:  {"type":"click","button":"left","room":"abc"}
  server → others:  {"type":"click","button":"left","from":"host"}

Requirements:
    pip install websockets
"""

import asyncio
import json
import logging
import argparse
from collections import defaultdict
from typing import Dict, Set

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="[Collab] %(message)s")
log = logging.getLogger(__name__)


class CollaborationServer:
    def __init__(self):
        # room_id → set of (websocket, role) tuples
        self.rooms: Dict[str, Set] = defaultdict(set)

    async def handler(self, ws: "WebSocketServerProtocol"):
        room_id = None
        role = "unknown"
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type")

                # ── Join room ──────────────────────────────────────────────
                if msg_type == "join":
                    room_id = msg.get("room", "default")
                    role = msg.get("role", "guest")
                    self.rooms[room_id].add((ws, role))
                    log.info(f"'{role}' joined room '{room_id}' "
                             f"({len(self.rooms[room_id])} users)")
                    await ws.send(json.dumps({
                        "type": "joined",
                        "room": room_id,
                        "users": len(self.rooms[room_id]),
                    }))
                    # Notify others
                    await self._broadcast(room_id, ws, {
                        "type": "peer_joined", "role": role,
                        "users": len(self.rooms[room_id]),
                    })

                # ── Cursor / gesture update ────────────────────────────────
                elif msg_type in ("cursor", "click", "gesture"):
                    if room_id:
                        relay = {**msg, "from": role}
                        relay.pop("room", None)
                        await self._broadcast(room_id, ws, relay)

                # ── Ping ──────────────────────────────────────────────────
                elif msg_type == "ping":
                    await ws.send(json.dumps({"type": "pong"}))

        except websockets.exceptions.ConnectionClosedOK:
            pass
        except websockets.exceptions.ConnectionClosedError:
            pass
        finally:
            if room_id:
                self.rooms[room_id].discard((ws, role))
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
                else:
                    await self._broadcast(room_id, ws, {
                        "type": "peer_left", "role": role,
                        "users": len(self.rooms[room_id]),
                    })
                log.info(f"'{role}' left room '{room_id}'")

    async def _broadcast(self, room_id: str, sender, message: dict):
        raw = json.dumps(message)
        targets = [ws for ws, _ in self.rooms.get(room_id, set()) if ws is not sender]
        if targets:
            await asyncio.gather(*(t.send(raw) for t in targets), return_exceptions=True)

    async def serve(self, host: str = "0.0.0.0", port: int = 8765):
        if not WS_AVAILABLE:
            raise RuntimeError("websockets not installed. Run: pip install websockets")
        log.info(f"Starting server on ws://{host}:{port}")
        log.info("Share your LAN IP with the other user.")
        async with websockets.serve(self.handler, host, port):
            await asyncio.Future()  # run forever


# ── Client mixin for main.py ───────────────────────────────────────────────────
class CollaborationClient:
    """Thin async client that sends cursor/gesture events and receives peer events."""

    def __init__(self, uri: str, room: str, role: str, on_peer_event=None):
        self.uri = uri
        self.room = room
        self.role = role
        self.on_peer_event = on_peer_event  # callback(msg_dict)
        self._ws = None
        self._task = None
        self.connected = False

    def start(self):
        import threading
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_loop, daemon=True).start()

    def _run_loop(self):
        self._loop.run_until_complete(self._connect())

    async def _connect(self):
        if not WS_AVAILABLE:
            log.warning("websockets not installed — collaboration disabled.")
            return
        try:
            async with websockets.connect(self.uri) as ws:
                self._ws = ws
                await ws.send(json.dumps({"type": "join", "room": self.room, "role": self.role}))
                self.connected = True
                log.info(f"Connected to collaboration server as '{self.role}'")
                async for raw in ws:
                    msg = json.loads(raw)
                    if self.on_peer_event:
                        self.on_peer_event(msg)
        except Exception as e:
            log.warning(f"Collaboration connection failed: {e}")
            self.connected = False

    def send_cursor(self, x: float, y: float, gesture: str):
        if self._ws and self.connected:
            asyncio.run_coroutine_threadsafe(
                self._ws.send(json.dumps({
                    "type": "cursor", "x": round(x, 4), "y": round(y, 4),
                    "gesture": gesture, "room": self.room,
                })),
                self._loop,
            )

    def send_click(self, button: str = "left"):
        if self._ws and self.connected:
            asyncio.run_coroutine_threadsafe(
                self._ws.send(json.dumps({
                    "type": "click", "button": button, "room": self.room,
                })),
                self._loop,
            )


# ── CLI entry point ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Virtual Mouse Collaboration Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = CollaborationServer()
    try:
        asyncio.run(server.serve(args.host, args.port))
    except KeyboardInterrupt:
        log.info("Server stopped.")


if __name__ == "__main__":
    main()
