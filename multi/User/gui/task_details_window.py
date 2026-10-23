# gui/task_details_window.py

import tkinter as tk
from tkinter import ttk

class TaskDetailsWindow:
    """A read-only window with everything about one task."""

    def __init__(self, master, task):
        self.window = tk.Toplevel(master)
        self.window.title("Task Details")
        self.window.geometry("400x320")
        self.window.transient(master.winfo_toplevel())

        frame = ttk.Frame(self.window, padding=10)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        fields = [
            ("Task:", task.get("task_name", "")),
            ("Due Date:", task.get("due_date") or "None"),
            ("Time:", task.get("due_time") or "None"),
            ("Priority:", task.get("priority") or "Normal"),
            ("Status:", "Completed" if task.get("completed") else "Open"),
        ]
        for row, (label, value) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="ne", padx=5, pady=3)
            ttk.Label(frame, text=value, wraplength=280).grid(row=row, column=1, sticky="w", padx=5, pady=3)

        ttk.Label(frame, text="Details:").grid(row=len(fields), column=0, sticky="ne", padx=5, pady=3)
        details = tk.Text(frame, height=6, wrap="word", font="TkDefaultFont")
        details.insert("1.0", task.get("details") or "")
        details.configure(state="disabled")
        details.grid(row=len(fields), column=1, sticky="nsew", padx=5, pady=3)
        frame.rowconfigure(len(fields), weight=1)

        ttk.Button(frame, text="Close", command=self.window.destroy).grid(
            row=len(fields) + 1, column=0, columnspan=2, pady=10)
