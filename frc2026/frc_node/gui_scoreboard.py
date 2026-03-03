import tkinter as tk
import time

class ScoreboardGUI:
    def __init__(self, node):
        self.node = node
        self.root = tk.Tk()
        self.root.title("FRC 2026 Simplified Scoreboard")
        self.root.geometry("800x220")
        self.root.configure(bg="black")

        self.COLOR_BLUE = "#0066A1"
        self.COLOR_RED = "#BE1423"
        self.COLOR_WHITE = "#FFFFFF"
        self.COLOR_GRAY = "#D9D9D9"

        self.canvas = tk.Canvas(self.root, width=800, height=220, bg="black", highlightthickness=0)
        self.canvas.pack(expand=True)

        self.update_gui_loop()

    def update_gui_loop(self):
        self.render_minimal_scoreboard()
        self.root.after(100, self.update_gui_loop)

    def render_minimal_scoreboard(self):
        self.canvas.delete("all")
        cx, cy = 400, 75

        # --- 1. Top Row (Scores & Main Timer) ---
        self.canvas.create_rectangle(cx-300, cy-50, cx-100, cy+50, fill=self.COLOR_BLUE, outline="")
        self.canvas.create_text(cx-200, cy, text=str(self.node.alliance_scores.get('B', 0)), fill="white", font=("Arial", 60, "bold"))

        # Timer Display Logic
        display_time = "0:20" 
        remaining = 0
        
        if hasattr(self.node, "current_period_end_time"):
            remaining = max(0, int(self.node.current_period_end_time - time.time()))

        if self.node.current_period == "AUTONOMOUS":
            display_time = f"0:{remaining:02d}"
        elif self.node.current_period == "TRANSITION":
            display_time = "2:20" 
        elif self.node.current_period == "TELEOP":
            display_time = f"{remaining // 60}:{remaining % 60:02d}"
        elif self.node.current_period == "POSTMATCH":
            display_time = "0:00"
        elif self.node.current_period == "PREMATCH":
            display_time = "0:20"
        
        self.canvas.create_rectangle(cx-100, cy-50, cx+100, cy+50, fill=self.COLOR_WHITE, outline="")
        self.canvas.create_text(cx, cy, text=display_time, fill="black", font=("Arial", 55, "bold"))

        self.canvas.create_rectangle(cx+100, cy-50, cx+300, cy+50, fill=self.COLOR_RED, outline="")
        self.canvas.create_text(cx+200, cy, text=str(self.node.alliance_scores.get('R', 0)), fill="white", font=("Arial", 60, "bold"))

        # --- 2. Sub-Period Box (ONLY visible during TELEOP) ---
        # Removed PREMATCH from this list so the box is hidden until Teleop begins
        if self.node.current_period == "TELEOP":
            sub_y = cy + 75
            self.canvas.create_rectangle(cx-100, sub_y-25, cx+100, sub_y+25, fill=self.COLOR_GRAY, outline="")
            self.canvas.create_line(cx+20, sub_y-25, cx+20, sub_y+25, fill="#AFAFAF", width=2)

            elapsed = 140 - remaining
            # Sub-period timing: 10, 25, 25, 25, 25, 30
            if elapsed < 10: current_phase, sub_rem = 1, 10 - elapsed
            elif elapsed < 35: current_phase, sub_rem = 2, 35 - elapsed
            elif elapsed < 60: current_phase, sub_rem = 3, 60 - elapsed
            elif elapsed < 85: current_phase, sub_rem = 4, 85 - elapsed
            elif elapsed < 110: current_phase, sub_rem = 5, 110 - elapsed
            else: current_phase, sub_rem = 6, 140 - elapsed

            self.canvas.create_text(cx-40, sub_y, text=f"{current_phase} / 6", fill="black", font=("Arial", 28, "bold"))
            self.canvas.create_text(cx+60, sub_y, text=f":{int(sub_rem):02d}", fill="black", font=("Arial", 28, "bold"))

    def run(self):
        self.root.mainloop()
