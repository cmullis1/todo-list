# gui/login_window.py

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from utils.tooltip import ToolTip  # Ensure ToolTip is imported if used
from api_client import APIClient
import logging
from gui.admin_interface import AdminInterface
from config import get_config
import sys  # Import sys to exit the application

class LoginWindow:
    """
    Handles the login interface.
    """

    def __init__(self, master):
        """
        Initialize the LoginWindow.

        Args:
            master (tk.Tk): The root Tkinter window.
        """
        self.master = master
        self.master.title("Login")
        self.master.geometry("250x150")
        self.master.resizable(False, False)

        self.config = get_config()
        self.api_client = APIClient(self.config)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Setup GUI
        self.setup_login_frame()
        self.logger.info("LoginWindow initialized")

        # Bind the window close event
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_login_frame(self):
        """Set up the login frame."""
        self.login_frame = ttk.Frame(self.master, padding=20)
        self.login_frame.pack(expand=True, fill='both')

        # Username Label and Entry
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.login_username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.login_frame, textvariable=self.login_username_var)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.username_entry.bind("<Return>", self.attempt_login)

        # Password Label and Entry
        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.login_password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self.login_frame, textvariable=self.login_password_var, show='*')
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.password_entry.bind("<Return>", self.attempt_login)

        # Login Button
        login_btn = ttk.Button(self.login_frame, text="Login", command=self.login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=10)
        ToolTip(login_btn, "Log in with admin credentials")  # Added tooltip

    def attempt_login(self, event=None):
        """Handle the Return key press for login."""
        self.login()

    def login(self):
        """Handle admin login by sending credentials to the server."""
        username = self.login_username_var.get().strip()
        password = self.login_password_var.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password.")
            return

        # Disable the login controls to prevent multiple clicks
        self.disable_controls()

        # Start a thread to handle login to keep the GUI responsive
        threading.Thread(target=self.perform_login, args=(username, password), daemon=True).start()

    def perform_login(self, username, password):
        """Perform the login operation."""
        success, message = self.api_client.login(username, password)
        if success:
            # Removed the admin check here
            self.logger.info(f"User '{username}' logged in successfully.")
            # Open the user interface on the main thread
            self.master.after(0, self.open_user_interface)
        else:
            self.logger.warning(f"Login failed for user '{username}': {message}")
            # Re-enable the login controls and show error message
            self.master.after(0, lambda: self.login_failed(message))

    def login_failed(self, message):
        """Handle failed login attempts."""
        # Re-enable the login controls
        self.enable_controls()
        messagebox.showerror("Login Failed", message)
        self.logger.info("Re-enabling login controls after failed attempt.")

    def open_user_interface(self):
        """Open the user interface using the root window."""
        self.login_frame.pack_forget()  # Hide the login frame
        AdminInterface(self.master, self.api_client)  # Initialize admin interface
        self.logger.info("UserInterface opened successfully.")

    def disable_controls(self):
        """Disable all input fields and the login button."""
        for child in self.login_frame.winfo_children():
            child.configure(state='disabled')
        self.logger.debug("Login controls disabled.")

    def enable_controls(self):
        """Enable all input fields and the login button."""
        for child in self.login_frame.winfo_children():
            child.configure(state='normal')
        self.logger.debug("Login controls enabled.")

    def on_closing(self):
        """Handle the closing of the login window."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.logger.info("Application is closing from LoginWindow.")
            try:
                self.master.quit()      # Stop the Tkinter mainloop
                self.master.destroy()   # Destroy all Tkinter widgets
                # Removed sys.exit() to rely on master.destroy() for termination
            except Exception as e:
                self.logger.error(f"Error during application shutdown: {e}")
                # Optionally, handle exceptions or perform additional cleanup here