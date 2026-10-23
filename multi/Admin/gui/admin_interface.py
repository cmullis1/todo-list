# gui/admin_interface.py

import tkinter as tk
from tkinter import ttk, messagebox
from utils.tooltip import ToolTip
import threading
import logging
from gui.task_management import TaskManagementFrame
import sys  # Import sys to exit the application

class AdminInterface:
    """
    Main admin interface window.
    """

    def __init__(self, master, api_client):
        """
        Initialize the AdminInterface.

        Args:
            master (tk.Tk): The root Tkinter window.
            api_client (APIClient): The API client instance.
        """
        self.master = master
        self.master.title("Admin Task Manager")
        self.master.geometry("800x600")
        self.master.resizable(True, True)

        self.api_client = api_client
        self.logger = logging.getLogger(self.__class__.__name__)

        # Setup GUI
        self.setup_admin_frame()

        # Initialize the refresh task ID to None
        self.refresh_task_id = None

        # Shutdown flag
        self.is_shutting_down = False

        # Start auto-refreshing tasks
        self.auto_refresh_tasks()
        self.logger.info("AdminInterface initialized")

        # Bind the window close event
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_admin_frame(self):
        """Set up the main admin frame without the Manage Users button."""
        self.admin_frame = ttk.Frame(self.master, padding=(5, 5, 5, 5))  # Reduced padding
        self.admin_frame.pack(fill='both', expand=True)

        # Task Management Frame
        self.task_management_frame = TaskManagementFrame(self.admin_frame, self.api_client)
        self.task_management_frame.pack(fill='both', expand=True, pady=(10, 0))

    def auto_refresh_tasks(self):
        """Automatically refresh tasks periodically."""
        if self.is_shutting_down:
            self.logger.info("Shutdown in progress. Auto-refresh not scheduled.")
            return
        try:
            self.logger.info("Starting auto-refresh of tasks every 60 seconds.")
            self.fetch_tasks_threaded()

            # Schedule the next refresh in 60 seconds (60000 milliseconds)
            self.refresh_task_id = self.master.after(60000, self.auto_refresh_tasks)
        except Exception as e:
            self.logger.error(f"Error in auto_refresh_tasks: {e}")

    def fetch_tasks_threaded(self):
        """Fetch tasks in a separate thread to keep the GUI responsive."""
        threading.Thread(target=self.fetch_tasks, daemon=True).start()

    def fetch_tasks(self):
        """Fetch tasks and update the task management frame."""
        if not self.master.winfo_exists():
            self.logger.warning("Master window does not exist. Skipping fetch_tasks.")
            return
        self.task_management_frame.fetch_tasks()
        
    def on_closing(self):
        """Handle the closing of the admin interface window."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.logger.info("Application is closing from AdminInterface.")
            self.is_shutting_down = True  # Set the shutdown flag
            try:
                if self.refresh_task_id is not None:
                    self.master.after_cancel(self.refresh_task_id)
                self.logger.debug("Auto-refresh task canceled.")
                self.master.quit()
                self.master.destroy()
            except Exception as e:
                self.logger.error(f"Error during application shutdown: {e}")
