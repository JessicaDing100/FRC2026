import tkinter as tk
import time

class ScoreboardGUI:
    def __init__(self, node):
        self.node = node
        self.root = tk.Tk()
        self.root.title("FRC 2026 Simplified Scoreboard")
        self.root.geometry("800x220")
        self.root.configure(bg="black")

        # Constants
        self.COLOR_BLUE = "#0066A1"
        self.COLOR_RED = "#BE1423"
        self.COLOR_WHITE = "#FFFFFF"
        self.COLOR_GRAY = "#D9D9D9"
        self.COLOR_ABORT = "#FF0000"

        # Setup Canvas
        self.canvas = tk.Canvas(self.root, width=800, height=220, bg="black", highlightthickness=0)
        self.canvas.pack(expand=True)

        # Coordinate Helpers
        self.cx, self.cy = 400, 75

        # --- Initialize Static Elements & Save IDs ---
        
        # Blue Score Box
        self.canvas.create_rectangle(self.cx-300, self.cy-50, self.cx-100, self.cy+50, fill=self.COLOR_BLUE, outline="")
        self.blue_score_text = self.canvas.create_text(self.cx-200, self.cy, text="0", fill="white", font=("Arial", 60, "bold"))

        # Timer Box
        self.timer_rect = self.canvas.create_rectangle(self.cx-100, self.cy-50, self.cx+100, self.cy+50, fill=self.COLOR_WHITE, outline="")
        self.timer_text = self.canvas.create_text(self.cx, self.cy, text="0:20", fill="black", font=("Arial", 55, "bold"))

        # Red Score Box
        self.canvas.create_rectangle(self.cx+100, self.cy-50, self.cx+300, self.cy+50, fill=self.COLOR_RED, outline="")
        self.red_score_text = self.canvas.create_text(self.cx+200, self.cy, text="0", fill="white", font=("Arial", 60, "bold"))

        # Sub-Period Elements (Grouped for easy hiding/showing)
        sub_y = self.cy + 75
        self.sub_rect = self.canvas.create_rectangle(self.cx-100, sub_y-25, self.cx+100, sub_y+25, fill=self.COLOR_GRAY, outline="", state='hidden')
        self.sub_line = self.canvas.create_line(self.cx+20, sub_y-25, self.cx+20, sub_y+25, fill="#AFAFAF", width=2, state='hidden')
        self.sub_phase_text = self.canvas.create_text(self.cx-40, sub_y, text="", fill="black", font=("Arial", 28, "bold"), state='hidden')
        self.sub_timer_text = self.canvas.create_text(self.cx+60, sub_y, text="", fill="black", font=("Arial", 28, "bold"), state='hidden')

        # Start the update loop
        self.update_gui_loop()

    def update_gui_loop(self):
        try:
            self.refresh_data()
        except Exception as e:
            print(f"[GUI ERROR] {e}")
        
        # Schedule next update in 100ms
        self.root.after(100, self.update_gui_loop)

    def refresh_data(self):
        # 1. Update Scores
        self.canvas.itemconfig(self.blue_score_text, text=str(self.node.alliance_scores.get('B', 0)))
        self.canvas.itemconfig(self.red_score_text, text=str(self.node.alliance_scores.get('R', 0)))

        # 2. Timer & Period Logic
        display_time = "0:20"
        remaining = 0
        if hasattr(self.node, "current_period_end_time"):
            remaining = max(0, int(self.node.current_period_end_time - time.time()))

        # Determine Main Timer String
        if self.node.current_period == "AUTONOMOUS":
            display_time = f"0:{remaining:02d}"
            self.canvas.itemconfig(self.timer_rect, fill=self.COLOR_WHITE)
        elif self.node.current_period == "TRANSITION":
            display_time = "2:20"
        elif self.node.current_period == "TELEOP":
            display_time = f"{remaining // 60}:{remaining % 60:02d}"
        elif self.node.current_period == "POSTMATCH":
            display_time = "0:00"
        elif self.node.current_period == "ABORTED":
            display_time = "STOP" # what to display?
            self.canvas.itemconfig(self.timer_rect, fill=self.COLOR_ABORT)
        else: # PREMATCH
            display_time = "0:20"
            self.canvas.itemconfig(self.timer_rect, fill=self.COLOR_WHITE)

        self.canvas.itemconfig(self.timer_text, text=display_time, fill="black" if self.node.current_period != "ABORTED" else "white")

        # 3. Sub-Period Logic (Only TELEOP)
        if self.node.current_period == "TELEOP":
            # Show Sub-period items
            self.canvas.itemconfig(self.sub_rect, state='normal')
            self.canvas.itemconfig(self.sub_line, state='normal')
            self.canvas.itemconfig(self.sub_phase_text, state='normal')
            self.canvas.itemconfig(self.sub_timer_text, state='normal')

            elapsed = 140 - remaining
            # Calculate Shift (10, 25, 25, 25, 25, 30)
            if elapsed < 10: phase, sub_rem = 1, 10 - elapsed
            elif elapsed < 35: phase, sub_rem = 2, 35 - elapsed
            elif elapsed < 60: phase, sub_rem = 3, 60 - elapsed
            elif elapsed < 85: phase, sub_rem = 4, 85 - elapsed
            elif elapsed < 110: phase, sub_rem = 5, 110 - elapsed
            else: phase, sub_rem = 6, 140 - elapsed

            self.canvas.itemconfig(self.sub_phase_text, text=f"{phase} / 6")
            self.canvas.itemconfig(self.sub_timer_text, text=f":{int(sub_rem):02d}")
        else:
            # Hide Sub-period items
            self.canvas.itemconfig(self.sub_rect, state='hidden')
            self.canvas.itemconfig(self.sub_line, state='hidden')
            self.canvas.itemconfig(self.sub_phase_text, state='hidden')
            self.canvas.itemconfig(self.sub_timer_text, state='hidden')

    def run(self):
        self.root.mainloop()
