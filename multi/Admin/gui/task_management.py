# gui/task_management.py

import tkinter as tk
from tkinter import ttk, messagebox
from utils.tooltip import ToolTip
import threading
import logging
from gui.task_info_window import TaskInfoWindow
from gui.user_management import UserManagementWindow  # Import UserManagementWindow
from gui.add_task_window import AddTaskWindow  # Import AddTaskWindow

import re

class TaskManagementFrame(ttk.Frame):
    """
    Frame for managing tasks.
    """

    def __init__(self, master, api_client):
        """
        Initialize the TaskManagementFrame.

        Args:
            master (tk.Widget): The parent widget.
            api_client (APIClient): The API client instance.
        """
        super().__init__(master, padding=(5, 5, 5, 5))  # Reduced padding
        self.api_client = api_client
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize variables
        self.tasks = {}
        self.users = []

        # Setup GUI
        self.setup_task_management_gui()

    def setup_task_management_gui(self):
        """Set up the task management GUI components."""

        # Top Frame for Filter and Add Task Button
        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', pady=(0, 5))  # Reduced top padding

        # Filter by User Label and Dropdown
        filter_label = ttk.Label(top_frame, text="Filter by User:")
        filter_label.pack(side='left', padx=(0, 5))  # Reduced left padding

        self.user_filter_var = tk.StringVar(value="All")
        self.user_filter_dropdown = ttk.Combobox(
            top_frame,
            textvariable=self.user_filter_var,
            values=["All"],
            state="readonly",
            width=20  # Adjust width as needed
        )
        self.user_filter_dropdown.pack(side='left', padx=(0, 20))  # Reduced spacing between dropdown and button
        self.user_filter_dropdown.bind("<<ComboboxSelected>>", self.on_user_filter_selected)
        ToolTip(self.user_filter_dropdown, "Select a user or 'All' to filter tasks")

        # Add Task Button (moved to top)
        add_task_btn = ttk.Button(top_frame, text="Add Task", command=self.add_task)
        add_task_btn.pack(side='left', padx=(0, 5))
        ToolTip(add_task_btn, "Add a new task")
        
        # Logout button
        self.logout_button = ttk.Button(top_frame, text="Logout", command=self.prepare_logout)
        self.logout_button.pack(side='right', padx=(5, 0))  # Place to the right of "Manage Users"
        ToolTip(self.logout_button, "Log out and return to the login screen")

        # Manage Users Button (moved to top, right side)
        manage_users_btn = ttk.Button(top_frame, text="Manage Users", command=self.open_user_management)
        manage_users_btn.pack(side='right', padx=(5, 0))
        ToolTip(manage_users_btn, "Open the User Management window")

        # Task Treeview
        columns = ("User", "Task", "Due Date", "Time", "Priority")  # Ensure "Priority" is included
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("User", text="User")
        self.tree.column("User", width=100, anchor='center')
        self.tree.heading("Task", text="Task")
        self.tree.column("Task", width=300, anchor='w')
        self.tree.heading("Due Date", text="Due Date")
        self.tree.column("Due Date", width=100, anchor='center')
        self.tree.heading("Time", text="Time")
        self.tree.column("Time", width=100, anchor='center')
        self.tree.heading("Priority", text="Priority")  # Add heading for Priority
        self.tree.column("Priority", width=100, anchor='center')  # Set column properties
        self.tree.pack(fill='both', expand=True, pady=5)

        # Configure row tags for priority coloring
        self.tree.tag_configure("urgent", background="lightcoral")
        self.tree.tag_configure("normal", background="lightgreen")
        self.tree.tag_configure("low", background="lightblue")

        # Bind events
        self.tree.bind("<Double-Button-1>", self.show_task_info)
        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click for context menu

        # Bottom Button Frame
        bottom_button_frame = ttk.Frame(self)
        bottom_button_frame.pack(side='bottom', anchor='e', pady=5, fill='x')

        # Edit Button
        edit_btn = ttk.Button(bottom_button_frame, text="Edit", command=self.edit_selected_task)
        edit_btn.pack(side='left', padx=5)
        ToolTip(edit_btn, "Edit the selected task")

        # Mark Completed Button
        mark_comp_btn = ttk.Button(bottom_button_frame, text="Mark Completed", command=self.mark_completed)
        mark_comp_btn.pack(side='left', padx=5)
        ToolTip(mark_comp_btn, "Mark the selected task as completed")

        # Delete Task Button
        delete_btn = ttk.Button(bottom_button_frame, text="Delete Task", command=self.delete_task)
        delete_btn.pack(side='left', padx=5)
        ToolTip(delete_btn, "Delete the selected task")

        # Show Completed Button
        show_completed_btn = ttk.Button(bottom_button_frame, text="Show Completed", command=self.show_completed_window)
        show_completed_btn.pack(side='right', padx=5)
        ToolTip(show_completed_btn, "View completed tasks in a separate window")

        # Refresh Button
        refresh_btn = ttk.Button(bottom_button_frame, text="↻", width=4, command=self.fetch_tasks_threaded)  # Adjust width as needed
        refresh_btn.pack(side='right', padx=5)
        ToolTip(refresh_btn, "Refresh task list")

        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_selected_task)
        self.context_menu.add_command(label="Mark Completed", command=self.mark_completed)
        self.context_menu.add_command(label="Delete", command=self.delete_task)

    def on_user_filter_selected(self, event):
        """Handle user selection for task filtering."""
        self.fetch_tasks_threaded()

    def open_user_management(self):
        """Open the User Management Window."""
        try:
            UserManagementWindow(self.master, self.api_client)
        except Exception as e:
            self.logger.error(f"Failed to open User Management window: {e}")
            messagebox.showerror("Error", "Failed to open User Management window.")
            
    def prepare_logout(self):
        """Prepare for logout and schedule the restart."""
        try:
            # Perform logout actions (e.g., clear session data)
            self.api_client.logout()

            # Access the root window
            root = self.winfo_toplevel()

            # Ensure that AdminInterface is assigned to root.admin_interface
            if hasattr(root, 'admin_interface') and root.admin_interface.refresh_task_id is not None:
                root.after_cancel(root.admin_interface.refresh_task_id)
                self.logger.debug("Auto-refresh task canceled during logout.")

            # Set the shutdown flag
            if hasattr(root, 'admin_interface'):
                root.admin_interface.is_shutting_down = True

            # Schedule the restart after a short delay
            root.after(100, self.restart_app)  # 100 milliseconds delay
        except Exception as e:
            self.logger.error(f"Error during logout preparation: {e}")

    def restart_app(self):
        """Restart the application by calling the main function."""
        from main import main  # Import main here to avoid circular import

        # Get the root window and cancel the refresh task
        root = self.winfo_toplevel()

        # Ensure the AdminInterface is accessible and cancel the task
        if hasattr(root, 'admin_interface'):
            root.admin_interface.is_shutting_down = True  # Set the shutdown flag
            if root.admin_interface.refresh_task_id is not None:
                root.after_cancel(root.admin_interface.refresh_task_id)
            self.logger.debug("Auto-refresh task canceled during restart.")

        # Destroy the root window
        root.destroy()

        # Call the main function to restart the app
        main()

    def add_task(self, event=None):
        """Open the Add Task window."""
        assigned_user = self.user_filter_var.get()
        if assigned_user == "All":
            messagebox.showwarning("Warning", "Please select a specific user to assign the task to.")
            return
        try:
            AddTaskWindow(self, self.api_client, self.fetch_tasks_threaded, assigned_user)
        except Exception as e:
            self.logger.error(f"Failed to open Add Task window: {e}")
            messagebox.showerror("Error", "Failed to open Add Task window.")

    def fetch_tasks_threaded(self):
        """Fetch tasks in a separate thread to keep the GUI responsive."""
        threading.Thread(target=self.fetch_tasks, daemon=True).start()

    def fetch_tasks(self, initial=False):
        """Fetch tasks from the server and update the local store."""
        user_filter = self.user_filter_var.get()
        success, tasks_or_error = self.api_client.get_tasks(user_filter=user_filter)
        if success:
            self.logger.debug(f"Tasks fetched successfully: {tasks_or_error}")
            self.tasks = {}
            for t in tasks_or_error:
                if 'task_id' in t:
                    self.tasks[str(t['task_id'])] = t
                else:
                    self.logger.warning(f"Task without 'id' encountered: {t}")
            self.master.after(0, self.refresh_tree)
            self.master.after(0, self.populate_user_filter)
        else:
            self.logger.error(f"Failed to fetch tasks: {tasks_or_error}")
            if initial and not self.tasks:
                self.master.after(0, lambda: messagebox.showerror("Error", f"Unable to fetch tasks: {tasks_or_error}"))
            else:
                self.master.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch tasks: {tasks_or_error}"))

    def refresh_tree(self):
        """Refresh the Treeview to display current tasks."""
        self.tree.delete(*self.tree.get_children())

        # Define priority mapping for sorting and tagging
        priority_map = {"Urgent": 0, "Normal": 1, "Low": 2}

        # Sort tasks first by priority, then by due date and time
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: (
                priority_map.get(t.get("priority", "Normal"), 1),
                self.parse_date_time(t.get("due_date", ""), t.get("due_time", ""))
            )
        )

        for task in sorted_tasks:
            if task.get("completed", False):
                continue  # Show only incomplete tasks
            task_id = str(task.get("task_id"))
            user = task.get("assigned_to", "")
            task_name = task.get("task_name", "")
            due_date = task.get("due_date", "")
            time_val = task.get("due_time", "")
            priority = task.get("priority", "Normal")
            tag = priority.lower()  # Tags should match the configured tags: "urgent", "normal", "low"
            self.tree.insert(
                "",
                "end",
                iid=task_id,
                values=(user, task_name, due_date, time_val, priority),
                tags=(tag,)
            )

    def parse_date_time(self, due_date, time_str):
        """Parse due date and time into a sortable tuple."""
        from datetime import datetime
        if not due_date:
            return (9999, 12, 31, 23, 59)
        try:
            if time_str:
                dt = datetime.strptime(f"{due_date} {time_str}", "%m/%d/%Y %I:%M %p")
            else:
                dt = datetime.strptime(due_date, "%m/%d/%Y")
            return (dt.year, dt.month, dt.day, dt.hour, dt.minute)
        except ValueError:
            return (9999, 12, 31, 23, 59)

    def edit_selected_task(self):
        """Open the edit window for the selected task."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No task selected.")
            return
        task_id = selected[0]
        task = self.tasks.get(task_id)
        if not task:
            messagebox.showerror("Error", "Selected task not found.")
            return
        try:
            TaskInfoWindow(
                self.master,
                self.api_client,
                task_id=task_id,
                is_edit=True,  # Ensure this flag is set to True
                refresh_callback=self.fetch_tasks_threaded
            )
        except Exception as e:
            self.logger.error(f"Failed to open Edit Task window: {e}")
            messagebox.showerror("Error", "Failed to open Edit Task window.")

    def mark_completed(self):
        """Mark the selected task as completed."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No task selected.")
            return
        task_id = selected[0]
        confirm = messagebox.askyesno("Confirm", "Mark the selected task as completed?")
        if not confirm:
            return

        # Disable the mark completed button to prevent multiple clicks
        self.disable_controls()

        # Start a thread to handle marking as completed
        threading.Thread(target=self.perform_mark_completed, args=(task_id,), daemon=True).start()

    def perform_mark_completed(self, task_id):
        """Perform the mark as completed operation."""
        updates = {"completed": True}
        success, message = self.api_client.update_task(task_id, updates)
        if success:
            self.logger.info(f"Task '{task_id}' marked as completed.")
            self.master.after(0, lambda: messagebox.showinfo("Success", message))
            self.fetch_tasks()
        else:
            self.logger.error(f"Failed to mark task '{task_id}' as completed: {message}")
            self.master.after(0, lambda: messagebox.showerror("Error", message))
        self.master.after(0, self.enable_controls)

    def delete_task(self):
        """Delete the selected task."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "No task selected.")
            return
        task_id = selected[0]
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected task?")
        if not confirm:
            return

        # Disable the delete button to prevent multiple clicks
        self.disable_controls()

        # Start a thread to handle task deletion
        threading.Thread(target=self.perform_delete_task, args=(task_id,), daemon=True).start()

    def perform_delete_task(self, task_id):
        """Perform the task deletion operation."""
        success, message = self.api_client.delete_task(task_id)
        if success:
            self.logger.info(f"Task '{task_id}' deleted successfully.")
            self.master.after(0, lambda: messagebox.showinfo("Success", message))
            self.fetch_tasks()
        else:
            self.logger.error(f"Failed to delete task '{task_id}': {message}")
            self.master.after(0, lambda: messagebox.showerror("Error", message))
        self.master.after(0, self.enable_controls)

    def show_completed_window(self):
        """Display a window with all completed tasks."""
        completed_tasks = [t for t in self.tasks.values() if t.get("completed", False)]
        if not completed_tasks:
            messagebox.showinfo("Info", "No completed tasks.")
            return

        try:
            TaskInfoWindow(self.master, self.api_client, is_completed_view=True, completed_tasks=completed_tasks)
        except Exception as e:
            self.logger.error(f"Failed to open Completed Tasks window: {e}")
            messagebox.showerror("Error", "Failed to open Completed Tasks window.")

    def show_task_info(self, event):
        """Display detailed information about the selected task."""
        selected = self.tree.selection()
        if not selected:
            return
        task_id = selected[0]
        task = self.tasks.get(task_id)
        if not task:
            messagebox.showerror("Error", "Task not found.")
            return
        try:
            TaskInfoWindow(self.master, self.api_client, task_id, is_edit=False)
        except Exception as e:
            self.logger.error(f"Failed to open Task Info window: {e}")
            messagebox.showerror("Error", "Failed to open Task Info window.")

    def show_context_menu(self, event):
        """Display the context menu on right-click."""
        selected_item = self.tree.identify_row(event.y)
        if selected_item:
            self.tree.selection_set(selected_item)
            self.context_menu.tk_popup(event.x_root, event.y_root)
        else:
            pass  # Optionally, handle clicks outside of items

    def populate_user_filter(self):
        """Populate the user filter dropdown with existing users."""
        threading.Thread(target=self.perform_populate_user_filter, daemon=True).start()

    def perform_populate_user_filter(self):
        """Fetch users and update the filter dropdown."""
        success, users_or_error = self.api_client.get_users()
        if success:
            users = [user['username'] for user in users_or_error]
            self.master.after(0, lambda: self.user_filter_dropdown.configure(values=["All"] + users))
        else:
            self.logger.error(f"Failed to populate user filter: {users_or_error}")
            self.master.after(0, lambda: messagebox.showerror("Error", f"Failed to populate user filter: {users_or_error}"))

    def disable_controls(self):
        """Disable all buttons to prevent multiple clicks."""
        # Iterate over all children in the bottom_button_frame
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, ttk.Button):
                        btn.configure(state='disabled')

    def enable_controls(self):
        """Enable all buttons after an operation."""
        # Iterate over all children in the bottom_button_frame
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, ttk.Button):
                        btn.configure(state='normal')
