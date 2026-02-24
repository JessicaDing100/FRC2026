import tkinter as tk
from tkinter import messagebox

class ConfigGui:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FRC 2026 Node Configuration")
        self.root.geometry("350x350")
        
        # Storage for the inputs
        self.results = {"hubs": 0, "clients": 0, "winner_mode": "S"}
        
        # Options mapping for the dropdown
        self.options = {
            "Red Alliance (R)": "R",
            "Blue Alliance (B)": "B",
            "Highest Score (S)": "S"
        }
        
        self._build_ui()

    def _build_ui(self):
        tk.Label(self.root, text="System Configuration", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Hubs Input
        tk.Label(self.root, text="Number of Hubs:").pack()
        self.entry_hubs = tk.Entry(self.root)
        self.entry_hubs.insert(0, "1")
        self.entry_hubs.pack(pady=5)
        
        # Clients Input
        tk.Label(self.root, text="Number of Clients:").pack()
        self.entry_clients = tk.Entry(self.root)
        self.entry_clients.insert(0, "1")
        self.entry_clients.pack(pady=5)
        
        # Winner Selection Dropdown
        tk.Label(self.root, text="Winner Selection Mode:").pack(pady=5)
        self.mode_var = tk.StringVar(self.root)
        self.mode_var.set("Highest Score (S)") # Default visible value
        
        self.dropdown = tk.OptionMenu(self.root, self.mode_var, *self.options.keys())
        self.dropdown.pack(pady=5)
        
        # Submit
        tk.Button(self.root, text="Confirm & Start", command=self._on_submit, 
                  bg="#2ecc71", fg="white", width=20).pack(pady=25)

    def _on_submit(self):
        try:
            self.results["hubs"] = int(self.entry_hubs.get())
            self.results["clients"] = int(self.entry_clients.get())
            
            # Map the readable selection back to the single character code
            selected_text = self.mode_var.get()
            self.results["winner_mode"] = self.options[selected_text]
            
            self.root.destroy()
        except ValueError:
            messagebox.showerror("Input Error", "Please enter whole numbers for Hubs/Clients.")

    def get_config(self):
        self.root.mainloop()
        return self.results

