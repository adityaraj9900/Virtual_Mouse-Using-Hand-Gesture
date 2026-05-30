import threading
import queue
import time

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

VOICE_MAP = {
    "click": "left_click",
    "left click": "left_click",
    "right click": "right_click",
    "double click": "double_click",
    "scroll up": "scroll_up",
    "scroll down": "scroll_down",
    "screenshot": "screenshot",
    "take screenshot": "screenshot",
    "zoom in": "zoom_in",
    "zoom out": "zoom_out",
    "switch window": "switch_window",
    "select all": "select_all",
    "copy": "copy",
    "paste": "paste",
    "undo": "undo",
    "play": "media_play_pause",
    "pause": "media_play_pause",
    "stop listening": "stop_voice",
}


class VoiceCommandListener:
    def __init__(self, command_queue: queue.Queue = None):
        self.command_queue = command_queue or queue.Queue()
        self.running = False
        self._thread = None
        self._last_time = 0.0

    def start(self):
        if not SPEECH_AVAILABLE:
            print("[Voice] Install dependencies: pip install SpeechRecognition pyaudio")
            return False
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[Voice] Listening for commands...")
        return True

    def stop(self):
        self.running = False

    def _loop(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)

        while self.running:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
                text = recognizer.recognize_google(audio).lower().strip()
                action = VOICE_MAP.get(text)
                if action:
                    now = time.time()
                    if now - self._last_time > 0.8:  # debounce
                        self.command_queue.put(("voice", action))
                        self._last_time = now
                        print(f"[Voice] Heard: '{text}' → {action}")
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                pass
            except sr.RequestError as e:
                print(f"[Voice] Recognition service error: {e}")
            except Exception:
                pass

    def get_command(self):
        try:
            return self.command_queue.get_nowait()
        except queue.Empty:
            return None
