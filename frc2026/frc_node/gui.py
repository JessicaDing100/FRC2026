import tkinter as tk
from tkinter import ttk
import time

class ScoreboardGUI:
    def __init__(self,node):
        self.node=node
        self.root=tk.Tk()
        self.root.title("FRC 2026 Scoreboard")
        self.root.geometry("400x300")
        self.root.resizable(False,False)

        self.period_label=ttk.Label(self.root,text="Period: PREMATCH",font=("Helvetica",16))
        self.period_label.pack(pady=10)
        self.time_label=ttk.Label(self.root,text="Time Remaining: 0",font=("Helvetica",14))
        self.time_label.pack(pady=5)

        self.scores_frame=ttk.Frame(self.root)
        self.scores_frame.pack(pady=10)
        self.score_labels={}

        self.update_gui_loop()

    def update_gui_loop(self):
        self.period_label.config(text=f"Period: {self.node.current_period}")
        if hasattr(self.node,"current_period_end_time"):
            remaining=int(self.node.current_period_end_time - time.time())
            if remaining<0: remaining=0
            self.time_label.config(text=f"Time Remaining: {remaining}s")
        with self.node.score_lock:
            for addr,score in self.node.scores.items():
                if addr not in self.score_labels:
                    lbl=ttk.Label(self.scores_frame,text=f"Client {addr}: {score}",font=("Helvetica",14))
                    lbl.pack()
                    self.score_labels[addr]=lbl
                else:
                    self.score_labels[addr].config(text=f"Client {addr}: {score}")
        self.root.after(500,self.update_gui_loop)

    def run(self):
        self.root.mainloop()
