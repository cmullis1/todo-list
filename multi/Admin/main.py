# main.py

import tkinter as tk
from tkinter import ttk
from logging_config import setup_logging
from gui.login_window import LoginWindow
import logging

def main():
    """Main function to run the Admin Task Manager application."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Admin Task Manager application.")

    root = tk.Tk()
    root.title("Login")
    root.geometry("250x150")
    root.resizable(False, False)

    style = ttk.Style(root)
    style.theme_use('clam')

    app = LoginWindow(root)  # Use root as the parent

    # Bind root's close event to app's on_closing method
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    root.mainloop()

if __name__ == "__main__":
    main()
