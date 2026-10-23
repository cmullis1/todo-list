# gui/user_interface.py

import tkinter as tk
from tkinter import ttk
import logging
from gui.task_management import TaskManagementFrame

class UserInterface:
    def __init__(self, master, api_client):
        self.master = master
        self.master.title(f"My Tasks - {api_client.username}")
        self.master.geometry("640x420")
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)

        self.setup_user_frame()
        self.logger.info("UserInterface initialized")

    def setup_user_frame(self):
        self.user_frame = ttk.Frame(self.master, padding=10)
        self.user_frame.pack(fill="both", expand=True)

        # Task Management Frame
        self.task_management_frame = TaskManagementFrame(self.user_frame, self.api_client)
        self.task_management_frame.pack(fill="both", expand=True)