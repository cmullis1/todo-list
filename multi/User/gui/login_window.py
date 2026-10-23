# gui/login_window.py

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from api_client import APIClient
from gui.user_interface import UserInterface
from config import get_config

class LoginWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("User Login")
        self.api_client = APIClient(get_config()["SERVER_URL"])
        self.logger = logging.getLogger(__name__)

        self.setup_login_frame()

    def setup_login_frame(self):
        self.login_frame = ttk.Frame(self.master, padding=20)
        self.login_frame.pack(expand=True, fill="both")

        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        login_button = ttk.Button(self.login_frame, text="Login", command=self.login)
        login_button.grid(row=2, column=0, columnspan=2, pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password.")
            return

        success, message = self.api_client.login(username, password)
        if success:
            self.logger.info(f"User '{username}' logged in successfully.")
            self.open_user_interface()
        else:
            self.logger.error(f"Login failed for user '{username}': {message}")
            messagebox.showerror("Login Failed", message)

    def open_user_interface(self):
        self.login_frame.pack_forget()
        UserInterface(self.master, self.api_client)