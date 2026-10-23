# main.py

import tkinter as tk
from tkinter import ttk
from gui.login_window import LoginWindow
import logging

def main():
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    root.title("User App")
    ttk.Style(root).theme_use("clam")
    LoginWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()