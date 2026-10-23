# gui/task_info_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from utils.tooltip import ToolTip
import threading
import logging
import re
from tkcalendar import DateEntry  # Import tkcalendar for date picker
from datetime import datetime  # Import datetime module
import webbrowser

class TaskInfoWindow:
    """
    Window to display detailed information about a task.
    Can be used for viewing or editing tasks.
    """

    def __init__(self, master, api_client, task_id=None, is_edit=False, is_completed_view=False, completed_tasks=None, refresh_callback=None):
        """
        Initialize the TaskInfoWindow.

        Args:
            master (tk.Tk): The root Tkinter window.
            api_client (APIClient): The API client instance.
            task_id (str, optional): The ID of the task to display/edit.
            is_edit (bool, optional): Whether the window is for editing the task.
            is_completed_view (bool, optional): Whether to display completed tasks.
            completed_tasks (list, optional): List of completed tasks to display.
            refresh_callback (function, optional): Callback to refresh tasks after editing.
        """
        self.master = tk.Toplevel(master)
        self.master.title("Edit Task" if is_edit else ("Completed Tasks" if is_completed_view else "Task Information"))
        self.master.geometry("485x650")
        self.master.resizable(True, True)

        self.api_client = api_client
        self.task_id = task_id
        self.is_edit = is_edit
        self.is_completed_view = is_completed_view
        self.completed_tasks = completed_tasks or []
        self.refresh_callback = refresh_callback

        self.logger = logging.getLogger(self.__class__.__name__)

        # Setup GUI
        self.setup_info_window()

    def setup_info_window(self):
        """Set up the task information window."""
        frame = ttk.Frame(self.master, padding=10)
        frame.pack(fill='both', expand=True)

        if self.is_completed_view and self.completed_tasks:
            # Display list of completed tasks
            ttk.Label(frame, text="Completed Tasks:", font=("Segoe UI Bold", 14)).pack(anchor='w', pady=5)
            self.completed_tree = ttk.Treeview(
                frame,
                columns=("User", "Task", "Due Date", "Time"),
                show="headings",
                selectmode="browse"
            )
            self.completed_tree.heading("User", text="User")
            self.completed_tree.column("User", width=100, anchor='center')
            self.completed_tree.heading("Task", text="Task")
            self.completed_tree.column("Task", width=200, anchor='w')
            self.completed_tree.heading("Due Date", text="Due Date")
            self.completed_tree.column("Due Date", width=80, anchor='center')
            self.completed_tree.heading("Time", text="Time")
            self.completed_tree.column("Time", width=80, anchor='center')
            self.completed_tree.pack(fill='both', expand=True, pady=5)

            # Configure row tags for priority coloring
            self.completed_tree.tag_configure("urgent", background="lightcoral")
            self.completed_tree.tag_configure("normal", background="lightgreen")
            self.completed_tree.tag_configure("low", background="lightblue")

            for task in self.completed_tasks:
                # Replace 'id' with 'task_id' to fix the KeyError
                task_id = str(task.get('task_id'))
                if not task_id:
                    self.logger.warning(f"Completed task without 'task_id': {task}")
                    continue  # Skip tasks without 'task_id'
                user = task.get("assigned_to", "")
                task_name = task.get("task_name", "")
                due_date = task.get("due_date", "")
                time_val = task.get("due_time", "")
                priority = task.get("priority", "Normal")
                tag = priority.lower()
                self.completed_tree.insert("", "end", iid=task_id, values=(
                    user,
                    task_name,
                    due_date,
                    time_val,
                    priority
                ), tags=(tag,))

            # Bind double-click to view task details
            self.completed_tree.bind("<Double-Button-1>", self.view_task_info)

            # Bind right-click for context menu
            self.completed_tree.bind("<Button-3>", self.show_context_menu_completed)

            # Buttons Frame
            buttons_frame = ttk.Frame(frame)
            buttons_frame.pack(fill='x', pady=10)

            # Edit Button
            edit_btn = ttk.Button(buttons_frame, text="Edit", command=self.edit_selected_completed_task)
            edit_btn.pack(side='left', padx=5)
            ToolTip(edit_btn, "Edit the selected completed task")

            # Mark Incomplete Button
            mark_incomplete_btn = ttk.Button(buttons_frame, text="Mark Incomplete", command=self.mark_selected_task_incomplete)
            mark_incomplete_btn.pack(side='left', padx=5)
            ToolTip(mark_incomplete_btn, "Mark the selected task as incomplete")
            
            # Delete Button
            delete_btn = ttk.Button(buttons_frame, text="Delete Task", command=self.delete_selected_completed_task)
            delete_btn.pack(side='left', padx=5)
            ToolTip(delete_btn, "Delete the selected completed task")

            # Refresh Button
            refresh_btn = ttk.Button(buttons_frame, text="↻", width=4, command=self.refresh_completed_tasks)
            refresh_btn.pack(side='right', padx=5)
            ToolTip(refresh_btn, "Refresh completed tasks list")

            # Context Menu for Completed Tasks
            self.completed_context_menu = tk.Menu(self.master, tearoff=0)
            self.completed_context_menu.add_command(label="Edit", command=self.edit_selected_completed_task)
            self.completed_context_menu.add_command(label="Delete", command=self.delete_selected_completed_task)
            self.completed_context_menu.add_command(label="Mark Incomplete", command=self.mark_selected_task_incomplete)

        elif self.task_id:
            # Display single task info
            success, task_or_error = self.api_client.get_task(self.task_id)
            if not success:
                messagebox.showerror("Error", f"Failed to fetch task details: {task_or_error}")
                self.master.destroy()
                return
            task = task_or_error

            # Initialize variables for editable fields
            self.task_name_var = tk.StringVar(value=task.get('task_name', ''))
            self.assigned_to_var = tk.StringVar(value=task.get('assigned_to', ''))
            self.due_date_var = tk.StringVar(value=task.get('due_date', ''))
            self.due_time_var = tk.StringVar(value=task.get('due_time', ''))
            self.priority_var = tk.StringVar(value=task.get('priority', 'Normal'))
            self.details_var = tk.StringVar(value=task.get('details', ''))
            self.completed_var = tk.BooleanVar(value=task.get('completed', False))

            # Task Name
            ttk.Label(frame, text="Task Name:", font=("Segoe UI", 10)).pack(anchor='w', pady=(5, 0))
            self.task_name_entry = ttk.Entry(frame, textvariable=self.task_name_var, state='normal' if self.is_edit else 'disabled')
            self.task_name_entry.pack(fill='x', pady=2)

            # Assigned To
            ttk.Label(frame, text="Assigned To:", font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 0))
            self.assigned_to_entry = ttk.Entry(frame, textvariable=self.assigned_to_var, state='normal' if self.is_edit else 'disabled')
            self.assigned_to_entry.pack(fill='x', pady=2)

            # ======================= Start of Date & Time Picker Integration =======================

            # Due Date and Time Frame using grid for side-by-side layout
            self.date_time_frame = ttk.Frame(frame)
            self.date_time_frame.pack(fill='x', pady=(10, 0))

            if self.is_edit:
                # "Select Date & Time" Button
                self.toggle_button = ttk.Button(self.date_time_frame, text="Select Date & Time", command=self.toggle_pickers)
                self.toggle_button.grid(row=0, column=0, sticky='w', pady=2)

                # Label to display Due Date & Time
                due_datetime = self.get_formatted_due_datetime()
                self.due_datetime_label = ttk.Label(self.date_time_frame, text=due_datetime, font=("Segoe UI", 10))
                self.due_datetime_label.grid(row=0, column=1, padx=10, sticky='w')

                # Frame to hold the date and time pickers (initially hidden)
                self.pickers_container = ttk.Frame(frame)

                # Date Picker
                ttk.Label(self.pickers_container, text="Due Date:", font=("Segoe UI", 10)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
                self.date_entry = DateEntry(
                    self.pickers_container,
                    width=12,
                    background='darkblue',
                    foreground='white',
                    borderwidth=2,
                    date_pattern='mm/dd/yyyy',
                    textvariable=self.due_date_var,
                    state='readonly'
                )
                self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

                # Time Picker Frame
                self.time_picker_frame = ttk.Frame(self.pickers_container)
                self.time_picker_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='w')

                ttk.Label(self.time_picker_frame, text="Due Time:", font=("Segoe UI", 10)).pack(side='left', padx=(0, 5))

                # Hour Combobox
                self.hour_var = tk.StringVar()
                self.hour_combo = ttk.Combobox(self.time_picker_frame, textvariable=self.hour_var, width=3, state='readonly')
                self.hour_combo['values'] = [f"{i:02d}" for i in range(1, 13)]  # 12-hour format
                self.hour_combo.current(0)
                self.hour_combo.pack(side='left')

                ttk.Label(self.time_picker_frame, text=":").pack(side='left')

                # Minute Combobox
                self.minute_var = tk.StringVar()
                self.minute_combo = ttk.Combobox(self.time_picker_frame, textvariable=self.minute_var, width=3, state='readonly')
                self.minute_combo['values'] = [f"{i:02d}" for i in range(0, 60, 5)]  # increments of 5 minutes
                self.minute_combo.current(0)
                self.minute_combo.pack(side='left', padx=(0, 5))

                # AM/PM Combobox
                self.am_pm_var = tk.StringVar()
                self.am_pm_combo = ttk.Combobox(self.time_picker_frame, textvariable=self.am_pm_var, width=3, state='readonly')
                self.am_pm_combo['values'] = ["AM", "PM"]
                self.am_pm_combo.current(0)
                self.am_pm_combo.pack(side='left')

                # Confirm Button for Date & Time Selection
                self.confirm_button = ttk.Button(self.pickers_container, text="Confirm", command=self.confirm_date_time)
                self.confirm_button.grid(row=2, column=0, columnspan=2, pady=5)

                # Variable to track visibility
                self.pickers_visible = False

                # Populate initial date and time if available
                self.populate_initial_date_time()
            else:
                # If not in edit mode, display Due Date and Due Time as labels
                ttk.Label(self.date_time_frame, text="Due Date & Time:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky='w')
                due_datetime = self.get_formatted_due_datetime()
                self.due_datetime_label = ttk.Label(self.date_time_frame, text=due_datetime, font=("Segoe UI", 10))
                self.due_datetime_label.grid(row=0, column=1, padx=10, sticky='w')

            # ======================= End of Date & Time Picker Integration =======================

            # Priority
            ttk.Label(frame, text="Priority:", font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 0))
            self.priority_dropdown = ttk.Combobox(
                frame,
                textvariable=self.priority_var,
                values=["Urgent", "Normal", "Low"],
                state="readonly" if self.is_edit else "disabled"
            )
            self.priority_dropdown.pack(fill='x', pady=2)

            # Completed
            ttk.Label(frame, text="Completed:", font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 0))
            self.completed_checkbox = ttk.Checkbutton(frame, variable=self.completed_var, state='normal' if self.is_edit else 'disabled')
            self.completed_checkbox.pack(anchor='w', pady=2)

            # Details
            ttk.Label(frame, text="Details:", font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 0))
            self.details_text = tk.Text(frame, wrap='word', height=10, state='normal')
            self.details_text.pack(fill='both', expand=True, pady=2)
            self.details_text.insert(tk.END, task.get("details", ""))
            self.make_hyperlinks_clickable(self.details_text)

            if not self.is_edit:
                # Configure the Text widget to be read-only and ensure text visibility
                # Removed bg=frame.cget('background') to fix the error
                self.details_text.config(state=tk.DISABLED, bg='white', fg='black')

            if self.is_edit:
                # Add buttons for saving or cancelling edits
                button_frame = ttk.Frame(frame)
                button_frame.pack(pady=10, anchor='e')

                save_btn = ttk.Button(button_frame, text="Save", command=self.save_edits)
                save_btn.pack(side='left', padx=5)
                ToolTip(save_btn, "Save the task changes")

                cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.master.destroy)
                cancel_btn.pack(side='left', padx=5)
                ToolTip(cancel_btn, "Cancel editing")
        else:
            messagebox.showerror("Error", "No task information available.")
            self.master.destroy()

    def get_formatted_due_datetime(self):
        """Return a formatted string of due date and time if available."""
        due_date = self.due_date_var.get().strip()
        due_time = self.due_time_var.get().strip()
        if due_date and due_time:
            return f"Due: {due_date} {due_time}"
        elif due_date:
            return f"Due: {due_date}"
        elif due_time:
            return f"Due: {due_time}"
        else:
            return "No Due Date/Time Set"

    def set_state_recursive(self, widget, state):
        """
        Recursively set the state of widgets that support the 'state' option.

        Args:
            widget (tk.Widget): The widget to configure.
            state (str): The state to set ('disabled' or 'normal').
        """
        # Check if the widget supports the 'state' option
        if 'state' in widget.keys():
            try:
                widget.configure(state=state)
                self.logger.debug(f"Set state='{state}' for widget: {widget}")
            except tk.TclError:
                self.logger.warning(f"Failed to set state='{state}' for widget: {widget}")

        # Recursively apply to all child widgets
        for child in widget.winfo_children():
            self.set_state_recursive(child, state)

    def disable_controls(self):
        """Disable all controls to prevent multiple clicks."""
        for widget in self.master.winfo_children():
            self.set_state_recursive(widget, 'disabled')

    def enable_controls(self):
        """Enable all controls after an operation."""
        for widget in self.master.winfo_children():
            self.set_state_recursive(widget, 'normal')

    def populate_initial_date_time(self):
        """Populate the date and time pickers with initial values if available."""
        # Handle Due Date
        if not self.due_date_var.get().strip():
            # If no due date is set, default to today's date
            today = datetime.today().strftime("%m/%d/%Y")
            self.due_date_var.set(today)

        try:
            month, day, year = map(int, self.due_date_var.get().split('/'))
            self.date_entry.set_date(datetime(year, month, day))
        except ValueError:
            # If parsing fails, default to today's date
            self.date_entry.set_date(datetime.today())

        # Handle Due Time
        if self.due_time_var.get().strip():
            match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', self.due_time_var.get(), re.IGNORECASE)
            if match:
                hour, minute, am_pm = match.groups()
                hour = int(hour)
                if am_pm.upper() == "PM" and hour != 12:
                    hour += 12
                elif am_pm.upper() == "AM" and hour == 12:
                    hour = 0
                # Convert back to 12-hour format for display
                display_hour = hour if hour <= 12 else hour - 12
                self.hour_combo.set(f"{display_hour:02d}")
                self.minute_combo.set(f"{int(minute):02d}")
                self.am_pm_combo.set(am_pm.upper())
        else:
            # If no due time is set, default to 12:00 AM
            self.hour_combo.set("12")
            self.minute_combo.set("00")
            self.am_pm_combo.set("AM")

    def toggle_pickers(self):
        """Toggle the visibility of the date and time pickers."""
        if self.pickers_visible:
            self.pickers_container.pack_forget()
            self.toggle_button.config(text="Select Date & Time")
        else:
            self.pickers_container.pack(fill='x', pady=5)
            self.toggle_button.config(text="Hide Date & Time")
        self.pickers_visible = not self.pickers_visible

    def confirm_date_time(self):
        """Confirm the selected date and time and update the variables."""
        selected_date = self.date_entry.get_date()
        selected_hour = self.hour_var.get()
        selected_minute = self.minute_var.get()
        selected_am_pm = self.am_pm_var.get()

        # Validate and format the date
        formatted_date = selected_date.strftime("%m/%d/%Y")
        self.due_date_var.set(formatted_date)

        # Format the time
        if selected_hour and selected_minute and selected_am_pm:
            formatted_time = f"{selected_hour}:{selected_minute} {selected_am_pm}"
            self.due_time_var.set(formatted_time)
        else:
            self.due_time_var.set("")

        # Update the due_datetime_label
        if hasattr(self, 'due_datetime_label'):
            self.due_datetime_label.config(text=self.get_formatted_due_datetime())

        # Optionally, hide the pickers after confirmation
        self.toggle_pickers()

    def view_task_info(self, event):
        """View detailed information about a selected completed task."""
        selected = self.completed_tree.selection()
        if not selected:
            return
        task_id = selected[0]
        task = self.api_client.get_task(task_id)[1]  # Assuming get_task returns (success, task)
        if not task:
            messagebox.showerror("Error", "Task not found.")
            return
        try:
            TaskInfoWindow(self.master, self.api_client, task_id, is_edit=False)
        except Exception as e:
            self.logger.error(f"Failed to open Task Info window: {e}")
            messagebox.showerror("Error", "Failed to open Task Info window.")

    def save_edits(self):
        """Save edits made to a task."""
        # Retrieve updated information from the widgets
        updated_task_name = self.task_name_var.get().strip()
        if not updated_task_name:
            messagebox.showwarning("Warning", "Task name cannot be empty.")
            return

        updated_assigned_to = self.assigned_to_var.get().strip()
        if not updated_assigned_to:
            messagebox.showwarning("Warning", "Assigned user cannot be empty.")
            return

        updated_due_date = self.due_date_var.get().strip()
        if updated_due_date and not self.validate_date(updated_due_date):
            messagebox.showerror("Error", "Invalid date format. Please use MM/DD/YYYY.")
            return

        updated_due_time = self.due_time_var.get().strip()
        if updated_due_time and not self.validate_time(updated_due_time):
            messagebox.showerror("Error", "Invalid time format. Please use HH:MM AM/PM.")
            return

        updated_priority = self.priority_var.get().strip()
        if updated_priority not in ["Urgent", "Normal", "Low"]:
            messagebox.showerror("Error", "Invalid priority level. Choose from Urgent, Normal, Low.")
            return

        updated_details = self.details_text.get("1.0", tk.END).strip()

        updated_completed = self.completed_var.get()

        updates = {
            "task_name": updated_task_name,
            "assigned_to": updated_assigned_to,
            "due_date": updated_due_date,
            "due_time": updated_due_time,
            "priority": updated_priority,
            "details": updated_details,
            "completed": updated_completed
        }

        # Disable controls to prevent multiple edits
        self.disable_controls()

        # Start a thread to handle task update
        threading.Thread(target=self.perform_save_edits, args=(self.task_id, updates), daemon=True).start()

    def perform_save_edits(self, task_id, updates):
        """Perform the task update operation."""
        success, message = self.api_client.update_task(task_id, updates)
        if success:
            self.logger.info(f"Task '{task_id}' updated successfully.")
            self.master.after(0, lambda: messagebox.showinfo("Success", message))
            if self.refresh_callback:
                self.master.after(0, self.refresh_callback)
            self.master.after(0, self.master.destroy)
        else:
            self.logger.error(f"Failed to update task '{task_id}': {message}")
            self.master.after(0, lambda: messagebox.showerror("Error", message))
        self.master.after(0, self.enable_controls)

    def make_hyperlinks_clickable(self, text_widget):
        """Make hyperlinks within a Text widget clickable."""
        pattern = r"(http[s]?://\S+)"
        text_widget.tag_remove("hyperlink", "1.0", tk.END)
        text_content = text_widget.get("1.0", tk.END)
        for match in re.finditer(pattern, text_content):
            start_index = f"1.0+{match.start()}c"
            end_index = f"1.0+{match.end()}c"
            text_widget.tag_add("hyperlink", start_index, end_index)

        text_widget.tag_configure("hyperlink", foreground="blue", underline=True)
        text_widget.tag_bind("hyperlink", "<Button-1>", self.open_link)

    def open_link(self, event):
        """Open the clicked hyperlink in the default web browser."""
        index = event.widget.index(f"@{event.x},{event.y}")
        hyperlink_ranges = event.widget.tag_ranges("hyperlink")
        for start, end in zip(hyperlink_ranges[0::2], hyperlink_ranges[1::2]):
            if event.widget.compare(start, "<=", index) and event.widget.compare(end, ">=", index):
                url = event.widget.get(start, end)
                webbrowser.open(url)
                break

    def validate_date(self, date_str):
        """Validate the date format MM/DD/YYYY."""
        try:
            datetime.strptime(date_str, "%m/%d/%Y")
            return True
        except ValueError:
            return False

    def validate_time(self, time_str):
        """Validate the time format HH:MM AM/PM."""
        try:
            datetime.strptime(time_str, "%I:%M %p")
            return True
        except ValueError:
            return False

    # ======================= New Functionalities for Completed Tasks =======================

    def edit_selected_completed_task(self):
        """Open the edit window for the selected completed task."""
        selected = self.completed_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No task selected.")
            return
        task_id = selected[0]
        try:
            TaskInfoWindow(
                self.master,
                self.api_client,
                task_id=task_id,
                is_edit=True,
                refresh_callback=self.refresh_completed_tasks
            )
        except Exception as e:
            self.logger.error(f"Failed to open Edit Task window: {e}")
            messagebox.showerror("Error", "Failed to open Edit Task window.")

    def delete_selected_completed_task(self):
        """Delete the selected completed task."""
        selected = self.completed_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No task selected.")
            return
        task_id = selected[0]
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected completed task?")
        if not confirm:
            return

        # Disable controls to prevent multiple clicks
        self.disable_controls()

        # Start a thread to handle task deletion
        threading.Thread(target=self.perform_delete_completed_task, args=(task_id,), daemon=True).start()

    def perform_delete_completed_task(self, task_id):
        """Perform the task deletion operation for completed tasks."""
        success, message = self.api_client.delete_task(task_id)
        if success:
            self.logger.info(f"Completed Task '{task_id}' deleted successfully.")
            self.master.after(0, lambda: messagebox.showinfo("Success", message))
            self.master.after(0, self.refresh_completed_tasks)
        else:
            self.logger.error(f"Failed to delete completed task '{task_id}': {message}")
            self.master.after(0, lambda: messagebox.showerror("Error", message))
        self.master.after(0, self.enable_controls)

    def mark_selected_task_incomplete(self):
        """Mark the selected completed task as incomplete."""
        selected = self.completed_tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No task selected.")
            return
        task_id = selected[0]
        confirm = messagebox.askyesno("Confirm", "Mark the selected task as incomplete?")
        if not confirm:
            return

        # Disable controls to prevent multiple clicks
        self.disable_controls()

        # Start a thread to handle marking as incomplete
        threading.Thread(target=self.perform_mark_task_incomplete, args=(task_id,), daemon=True).start()

    def perform_mark_task_incomplete(self, task_id):
        """Perform the mark as incomplete operation."""
        updates = {"completed": False}
        success, message = self.api_client.update_task(task_id, updates)
        if success:
            self.logger.info(f"Completed Task '{task_id}' marked as incomplete.")
            self.master.after(0, lambda: messagebox.showinfo("Success", message))
            self.master.after(0, self.refresh_completed_tasks)
        else:
            self.logger.error(f"Failed to mark completed task '{task_id}' as incomplete: {message}")
            self.master.after(0, lambda: messagebox.showerror("Error", message))
        self.master.after(0, self.enable_controls)

    def refresh_completed_tasks(self):
        """Refresh the list of completed tasks."""
        if self.refresh_callback:
            self.refresh_callback()
        # Optionally, destroy and recreate the window
        self.master.destroy()

    def show_context_menu_completed(self, event):
        """Display the context menu on right-click for completed tasks."""
        selected_item = self.completed_tree.identify_row(event.y)
        if selected_item:
            self.completed_tree.selection_set(selected_item)
            self.completed_context_menu.tk_popup(event.x_root, event.y_root)
        else:
            pass  # Optionally, handle clicks outside of items
