# gui/add_task_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import threading
import logging
from utils.tooltip import ToolTip  # Ensure ToolTip is imported

class AddTaskWindow(tk.Toplevel):
    """
    A modal window for adding a new task.
    """

    def __init__(self, master, api_client, refresh_callback, assigned_user):
        """
        Initialize the AddTaskWindow.

        Args:
            master (tk.Widget): The parent widget.
            api_client (APIClient): The API client instance.
            refresh_callback (function): Function to refresh tasks after adding.
            assigned_user (str): The user to whom the task will be assigned.
        """
        super().__init__(master)
        self.title("Add New Task")
        self.geometry("400x665")  # Increased height to accommodate Task Name and other fields
        self.resizable(False, False)
        self.api_client = api_client
        self.refresh_callback = refresh_callback
        self.assigned_user = assigned_user
        self.logger = logging.getLogger(self.__class__.__name__)

        # Make the window modal
        self.grab_set()

        # Setup GUI
        self.setup_gui()

    def setup_gui(self):
        """Set up all input fields and buttons."""
        padding_options = {'padx': 10, 'pady': 5}

        # Task Name
        ttk.Label(self, text="Task Name:").pack(anchor='w', **padding_options)
        self.task_name_var = tk.StringVar()
        self.task_name_entry = ttk.Entry(self, textvariable=self.task_name_var)
        self.task_name_entry.pack(fill='x', **padding_options)
        ToolTip(self.task_name_entry, "Enter the name of the task")  # Added tooltip

        # Due Date
        ttk.Label(self, text="Due Date:").pack(anchor='w', **padding_options)
        self.due_date_cal = Calendar(self, selectmode='day', date_pattern='mm/dd/yyyy')
        self.due_date_cal.pack(fill='x', **padding_options)

        # Due Time
        ttk.Label(self, text="Due Time:").pack(anchor='w', **padding_options)
        time_frame = ttk.Frame(self)
        time_frame.pack(fill='x', **padding_options)

        # Hour Dropdown
        self.hour_var = tk.StringVar()
        self.hour_dropdown = ttk.Combobox(
            time_frame,
            textvariable=self.hour_var,
            values=[f"{h}" for h in range(1, 13)],
            state="readonly",
            width=5
        )
        self.hour_dropdown.pack(side='left', padx=(0, 5))
        self.hour_dropdown.current(0)

        # Minute Dropdown
        self.minute_var = tk.StringVar()
        self.minute_dropdown = ttk.Combobox(
            time_frame,
            textvariable=self.minute_var,
            values=["00", "30"],
            state="readonly",
            width=5
        )
        self.minute_dropdown.pack(side='left', padx=(0, 5))
        self.minute_dropdown.current(0)

        # AM/PM Dropdown
        self.am_pm_var = tk.StringVar()
        self.am_pm_dropdown = ttk.Combobox(
            time_frame,
            textvariable=self.am_pm_var,
            values=["AM", "PM"],
            state="readonly",
            width=5
        )
        self.am_pm_dropdown.pack(side='left', padx=(0, 5))
        self.am_pm_dropdown.current(0)

        # Priority
        ttk.Label(self, text="Priority:").pack(anchor='w', **padding_options)
        self.priority_var = tk.StringVar(value="Normal")
        self.priority_dropdown = ttk.Combobox(
            self,
            textvariable=self.priority_var,
            values=["Urgent", "Normal", "Low"],
            state="readonly"
        )
        self.priority_dropdown.pack(fill='x', **padding_options)
        self.priority_dropdown.current(1)  # Default to Normal

        # Details
        ttk.Label(self, text="Details:").pack(anchor='w', **padding_options)
        self.details_text = tk.Text(self, height=10)  # Adjusted height for more details
        self.details_text.pack(fill='x', **padding_options)
        ToolTip(self.details_text, "Enter additional details about the task")  # Added tooltip

        # Button Frame
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        # Submit Button
        submit_btn = ttk.Button(button_frame, text="Add Task", command=self.submit_task)
        submit_btn.pack(side='left', padx=5)
        ToolTip(submit_btn, "Add the task and close the window")  # Applied ToolTip

    def submit_task(self):
        """Validate inputs and submit the new task to the server."""
        task_name = self.task_name_var.get().strip()
        due_date = self.due_date_cal.get_date()
        hour = self.hour_var.get()
        minute = self.minute_var.get()
        am_pm = self.am_pm_var.get()
        priority = self.priority_var.get()
        details = self.details_text.get("1.0", tk.END).strip()

        # Validate Task Name
        if not task_name:
            messagebox.showwarning("Validation Error", "Task name cannot be empty.")
            return

        # Validate Due Date
        if not due_date:
            messagebox.showwarning("Validation Error", "Please select a due date.")
            return

        # Construct Time
        due_time = f"{hour}:{minute} {am_pm}"

        # Prepare Task Data
        task_data = {
            "task_name": task_name,
            "assigned_to": self.assigned_user,
            "completed": False,
            "due_date": due_date,
            "due_time": due_time,
            "priority": priority,
            "details": details
        }

        # Disable the submit button to prevent multiple submissions
        self.disable_controls()

        # Start a thread to handle task creation
        threading.Thread(target=self.perform_add_task, args=(task_data, True), daemon=True).start()

    def perform_add_task(self, task_data, close_after):
        """Send the task data to the server and handle the response."""
        success, message = self.api_client.create_task(task_data)
        if success:
            task_name = task_data.get('task_name', 'No Name')  # Handle missing task_name gracefully
            self.logger.info(f"Task '{task_name}' created successfully.")
            if close_after:
                self.master.after(0, lambda: messagebox.showinfo("Success", message))
                self.master.after(0, self.refresh_callback)  # Refresh the task list
                self.master.after(0, self.destroy)  # Close the AddTaskWindow
        else:
            self.logger.error(f"Failed to create task: {message}")
            self.master.after(0, lambda: messagebox.showerror("Error", message))
            self.master.after(0, self.enable_controls)

    def disable_controls(self):
        """Disable all input fields and buttons."""
        self.task_name_entry.configure(state='disabled')
        self.due_date_cal.configure(state='disabled')
        self.hour_dropdown.configure(state='disabled')
        self.minute_dropdown.configure(state='disabled')
        self.am_pm_dropdown.configure(state='disabled')
        self.priority_dropdown.configure(state='disabled')
        self.details_text.configure(state='disabled')
        # Disable Submit button
        for child in self.children.values():
            if isinstance(child, ttk.Frame):
                for widget in child.winfo_children():  # Changed btn to widget
                    if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox, tk.Text)):  # Check widget type
                        widget.configure(state='disabled')

    def enable_controls(self):
        """Enable all input fields and buttons."""
        self.task_name_entry.configure(state='normal')
        self.due_date_cal.configure(state='normal')
        self.hour_dropdown.configure(state='readonly')
        self.minute_dropdown.configure(state='readonly')
        self.am_pm_dropdown.configure(state='readonly')
        self.priority_dropdown.configure(state='readonly')
        self.details_text.configure(state='normal')
        # Enable Submit button
        for child in self.children.values():
            if isinstance(child, ttk.Frame):
                for btn in child.winfo_children():
                    btn.configure(state='normal')
