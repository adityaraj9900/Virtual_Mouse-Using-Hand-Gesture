import tkinter as tk
from tkinter import ttk
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.analytics import AnalyticsTracker

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False

BG = "#1e1e2e"
SURFACE = "#313244"
ACCENT = "#89b4fa"
GREEN = "#a6e3a1"
MUTED = "#6c7086"
YELLOW = "#f9e2af"


class AnalyticsDashboard:
    def __init__(self, analytics: AnalyticsTracker):
        self.analytics = analytics

    def launch(self):
        threading.Thread(target=self._build, daemon=True).start()

    def _build(self):
        root = tk.Tk()
        root.title("Virtual Mouse — Analytics")
        root.geometry("820x580")
        root.configure(bg=BG)

        stats = self.analytics.get_session_stats()

        # Stat tiles
        tiles_frame = tk.Frame(root, bg=SURFACE)
        tiles_frame.pack(fill=tk.X, padx=12, pady=10)

        for label, value in [
            ("Duration", f"{stats['duration_seconds']}s"),
            ("Gestures", str(stats['total_gestures'])),
            ("Clicks", str(stats['total_clicks'])),
            ("Avg FPS", str(stats['average_fps'])),
            ("Confidence", f"{stats['average_confidence']:.0%}"),
        ]:
            col = tk.Frame(tiles_frame, bg=SURFACE)
            col.pack(side=tk.LEFT, padx=18, pady=10)
            tk.Label(col, text=value, bg=SURFACE, fg=ACCENT,
                     font=("Helvetica", 17, "bold")).pack()
            tk.Label(col, text=label, bg=SURFACE, fg=MUTED,
                     font=("Helvetica", 9)).pack()

        if not MATPLOTLIB_OK:
            tk.Label(root, text="Install matplotlib for charts:  pip install matplotlib",
                     bg=BG, fg=YELLOW, font=("Helvetica", 11)).pack(pady=30)
            root.mainloop()
            return

        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
        fig.patch.set_facecolor(BG)

        # Gesture bar chart
        ax1 = axes[0]
        ax1.set_facecolor(SURFACE)
        gesture_data = stats.get("gesture_breakdown", {})
        if gesture_data:
            palette = ["#89b4fa", "#a6e3a1", "#f38ba8", "#fab387",
                       "#f9e2af", "#cba6f7", "#74c7ec", "#94e2d5"]
            labels = list(gesture_data.keys())
            values = list(gesture_data.values())
            ax1.bar(labels, values, color=palette[:len(labels)])
            ax1.tick_params(colors=MUTED, labelrotation=25, labelsize=8)
            ax1.set_ylabel("Count", color=MUTED)
        else:
            ax1.text(0.5, 0.5, "No gesture data yet",
                     transform=ax1.transAxes, ha="center", color=MUTED)
        ax1.set_title("Gesture Usage", color="#cdd6f4", pad=8)
        for spine in ax1.spines.values():
            spine.set_color(SURFACE)

        # Click heatmap
        ax2 = axes[1]
        ax2.set_facecolor(SURFACE)
        clicks = self.analytics.click_positions
        if len(clicks) >= 3:
            xs = [c["x"] for c in clicks]
            ys = [c["y"] for c in clicks]
            hb = ax2.hexbin(xs, ys, gridsize=18, cmap="Blues", mincnt=1)
            fig.colorbar(hb, ax=ax2).ax.tick_params(colors=MUTED, labelsize=8)
            ax2.invert_yaxis()
        else:
            ax2.text(0.5, 0.5, "Need more clicks\nfor heatmap",
                     transform=ax2.transAxes, ha="center", color=MUTED, va="center")
        ax2.set_title("Click Heatmap", color="#cdd6f4", pad=8)
        ax2.tick_params(colors=MUTED)
        for spine in ax2.spines.values():
            spine.set_color(SURFACE)

        plt.tight_layout(pad=2.0)
        canvas = FigureCanvasTkAgg(fig, master=root)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        # Gesture breakdown text
        breakdown = "  |  ".join(f"{k}: {v}" for k, v in gesture_data.items())
        tk.Label(root, text=breakdown or "No gestures recorded",
                 bg=BG, fg=MUTED, font=("Helvetica", 9)).pack(pady=(0, 6))

        root.mainloop()
