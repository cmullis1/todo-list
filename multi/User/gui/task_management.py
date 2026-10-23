# gui/task_management.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging
from gui.task_details_window import TaskDetailsWindow

class TaskManagementFrame(ttk.Frame):
    """Shows the logged-in user's open tasks and lets them mark tasks completed."""

    def __init__(self, master, api_client):
        super().__init__(master)
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)

        self.tasks = {}
        self.setup_gui()
        self.fetch_tasks()

    def setup_gui(self):
        # Task Treeview, colored by priority like the Admin app
        columns = ("Task", "Due Date", "Time", "Priority")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("Task", text="Task")
        self.tree.column("Task", width=300, anchor="w")
        for column in ("Due Date", "Time", "Priority"):
            self.tree.heading(column, text=column)
            self.tree.column(column, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=5)

        self.tree.tag_configure("urgent", background="lightcoral")
        self.tree.tag_configure("normal", background="lightgreen")
        self.tree.tag_configure("low", background="lightblue")

        self.tree.bind("<Double-Button-1>", lambda event: self.show_details())

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=5)

        details_button = ttk.Button(button_frame, text="Details", command=self.show_details)
        details_button.pack(side="left", padx=5)

        complete_button = ttk.Button(button_frame, text="Mark Completed", command=self.mark_completed)
        complete_button.pack(side="left", padx=5)

        refresh_button = ttk.Button(button_frame, text="Refresh", command=self.fetch_tasks)
        refresh_button.pack(side="right", padx=5)

    def fetch_tasks(self):
        success, tasks_or_error = self.api_client.get_tasks()
        if not success:
            messagebox.showerror("Error", tasks_or_error)
            return
        self.tasks = {str(task["task_id"]): task for task in tasks_or_error}
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())

        # Sort by priority, then by due date and time
        priority_map = {"Urgent": 0, "Normal": 1, "Low": 2}
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: (
                priority_map.get(t.get("priority") or "Normal", 1),
                self.parse_date_time(t.get("due_date"), t.get("due_time"))
            )
        )

        for task in sorted_tasks:
            if task.get("completed"):
                continue  # Show only open tasks
            priority = task.get("priority") or "Normal"
            self.tree.insert(
                "",
                "end",
                iid=str(task["task_id"]),
                values=(task.get("task_name", ""), task.get("due_date") or "",
                        task.get("due_time") or "", priority),
                tags=(priority.lower(),)
            )

    def parse_date_time(self, due_date, due_time):
        """Turn MM/DD/YYYY and HH:MM AM/PM into a sortable tuple; tasks with no date sort last."""
        if not due_date:
            return (9999, 12, 31, 23, 59)
        try:
            if due_time:
                dt = datetime.strptime(f"{due_date} {due_time}", "%m/%d/%Y %I:%M %p")
            else:
                dt = datetime.strptime(due_date, "%m/%d/%Y")
            return (dt.year, dt.month, dt.day, dt.hour, dt.minute)
        except ValueError:
            return (9999, 12, 31, 23, 59)

    def selected_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No task selected.")
            return None
        return self.tasks.get(selected[0])

    def show_details(self):
        task = self.selected_task()
        if task:
            TaskDetailsWindow(self, task)

    def mark_completed(self):
        task = self.selected_task()
        if not task:
            return
        if not messagebox.askyesno("Confirm", f"Mark '{task.get('task_name', '')}' as completed?"):
            return

        success, message = self.api_client.mark_completed(task["task_id"])
        if success:
            self.logger.info(f"Task '{task['task_id']}' marked as completed.")
            self.fetch_tasks()
        else:
            self.logger.error(f"Failed to mark task '{task['task_id']}' as completed: {message}")
            messagebox.showerror("Error", message)
