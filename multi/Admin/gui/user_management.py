# gui/user_management.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import logging
import re

class UserManagementWindow:
    """
    Window for managing users.
    """

    def __init__(self, master, api_client):
        """
        Initialize the UserManagementWindow.

        Args:
            master (tk.Tk): The root Tkinter window.
            api_client (APIClient): The API client instance.
        """
        self.master = tk.Toplevel(master)
        self.master.title("Manage Users")
        self.master.geometry("380x275")
        self.master.resizable(False, False)

        self.api_client = api_client
        self.logger = logging.getLogger(self.__class__.__name__)

        # Setup GUI
        self.setup_user_management_frame()

        # Fetch and display users
        self.fetch_users_threaded()

    def setup_user_management_frame(self):
        """Set up the user management frame."""
        frame = ttk.Frame(self.master, padding=10)
        frame.pack(fill='both', expand=True)

        # Buttons for User Management
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        create_user_btn = ttk.Button(button_frame, text="Create User", command=self.open_create_user_window)
        create_user_btn.pack(side='top', pady=2, fill='x')

        reset_pw_btn = ttk.Button(button_frame, text="Reset Password", command=self.reset_password)
        reset_pw_btn.pack(side='top', pady=2, fill='x')

        delete_user_btn = ttk.Button(button_frame, text="Delete User", command=self.delete_user)
        delete_user_btn.pack(side='top', pady=2, fill='x')

        toggle_admin_btn = ttk.Button(button_frame, text="Toggle Admin", command=self.toggle_admin_status)
        toggle_admin_btn.pack(side='top', pady=2, fill='x')

        # List of users
        ttk.Label(frame, text="Existing Users:").grid(row=0, column=0, padx=5, pady=5, sticky='nw')
        self.users_listbox = tk.Listbox(frame, height=15, width=40)
        self.users_listbox.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)

        # Scrollbar for Listbox
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.users_listbox.yview)
        scrollbar.grid(row=0, column=0, sticky='nse')
        self.users_listbox.config(yscrollcommand=scrollbar.set)

    def fetch_users_threaded(self):
        """Fetch users in a separate thread to keep the GUI responsive."""
        threading.Thread(target=self.fetch_users, daemon=True).start()

    def fetch_users(self):
        """Fetch the list of users from the server."""
        success, users_or_error = self.api_client.get_users()
        if success:
            # Sort the users list by is_admin in descending order
            self.users = sorted(users_or_error, key=lambda user: user.get('is_admin', False), reverse=True)
            self.logger.info(f"Fetched {len(self.users)} users from server.")
            self.master.after(0, self.update_users_listbox)
        else:
            self.logger.error(f"Failed to fetch users: {users_or_error}")
            self.master.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch users: {users_or_error}"))

    def update_users_listbox(self):
        """Update the listbox with fetched users."""
        self.users_listbox.delete(0, tk.END)
        for user in self.users:
            username = user.get('username', 'Unknown')
            is_admin = user.get('is_admin', False)
            display_name = f"{username} (Admin)" if is_admin else username
            self.users_listbox.insert(tk.END, display_name)

    def on_user_select(self, event):
        """Handle user selection from the listbox."""
        selection = self.users_listbox.curselection()
        if selection:
            selected_display = self.users_listbox.get(selection[0])
            selected_user = selected_display.replace(" (Admin)", "")
            # No need to set new_user_var here as it's in the create user window
        else:
            pass  # No action needed if no user is selected

    def open_create_user_window(self):
        """Open a new window for creating a new user."""
        self.create_user_window = tk.Toplevel(self.master)
        self.create_user_window.title("Create New User")
        self.create_user_window.geometry("265x180")  # Slightly taller to accommodate the checkbox
        self.create_user_window.resizable(False, False)

        # Username Entry
        ttk.Label(self.create_user_window, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.new_user_var = tk.StringVar()
        self.new_user_entry = ttk.Entry(self.create_user_window, textvariable=self.new_user_var)
        self.new_user_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Password Entry
        ttk.Label(self.create_user_window, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.new_password_var = tk.StringVar()
        self.new_password_entry = ttk.Entry(self.create_user_window, textvariable=self.new_password_var, show='*')
        self.new_password_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        # Confirm Password Entry
        ttk.Label(self.create_user_window, text="Confirm Password:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.confirm_password_var = tk.StringVar()
        self.confirm_password_entry = ttk.Entry(self.create_user_window, textvariable=self.confirm_password_var, show='*')
        self.confirm_password_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        # Admin Status Checkbox
        self.is_admin_var = tk.BooleanVar(value=False)  # Initially not an admin
        admin_checkbox = ttk.Checkbutton(self.create_user_window, text="Admin", variable=self.is_admin_var)
        admin_checkbox.grid(row=3, column=0, columnspan=2, padx=5, pady=5)  # Center the checkbox

        # Save Button
        save_button = ttk.Button(self.create_user_window, text="Save", command=self.create_user)
        save_button.grid(row=4, column=0, columnspan=2, pady=10)  # Centered in row 4

    def create_user(self):
        """Create a new user account on the server."""
        username = self.new_user_var.get()
        password = self.new_password_var.get()
        confirm_password = self.confirm_password_var.get()

        if not username or not password or not confirm_password:
            messagebox.showwarning("Warning", "Please fill in all fields.")
            return

        if not self.validate_username(username):
            messagebox.showwarning("Warning", "Invalid username format. Username must be between 3 and 20 characters and can only contain alphanumeric characters, underscores, and hyphens.")
            return

        if not self.validate_password(password):
            messagebox.showwarning("Warning", "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit.")
            return

        if password != confirm_password:
            messagebox.showwarning("Warning", "Passwords do not match.")
            return

        # Get the admin status from the checkbox
        is_admin = self.is_admin_var.get()

        self.disable_controls()

        success, response = self.api_client.create_user(username, password, is_admin)

        self.enable_controls()

        if success:
            self.create_user_window.destroy()
            self.fetch_users()  # Refresh the user list
            messagebox.showinfo("Success", f"User '{username}' created successfully.")
        else:
            messagebox.showerror("Error", f"Failed to create user: {response}")

    def reset_password(self):
        """Reset a user's password."""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user.")
            return

        selected_display = self.users_listbox.get(selection[0])
        selected_user = selected_display.replace(" (Admin)", "")

        new_password = simpledialog.askstring("Reset Password", f"Enter new password for '{selected_user}':", show='*')
        if new_password is None:
            return  # User canceled

        if not self.validate_password(new_password):
            messagebox.showwarning("Warning", "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit.")
            return

        confirm_password = simpledialog.askstring("Confirm Password", "Confirm new password:", show='*')
        if confirm_password is None:
            return  # User canceled

        if new_password != confirm_password:
            messagebox.showwarning("Warning", "Passwords do not match.")
            return

        self.disable_controls()
        success, response = self.api_client.reset_password(selected_user, new_password)
        self.enable_controls()

        if success:
            self.logger.info(f"Password reset for '{selected_user}' successful.")
            messagebox.showinfo("Success", f"Password reset for '{selected_user}' successful.")
        else:
            self.logger.error(f"Failed to reset password: {response}")
            messagebox.showerror("Error", f"Failed to reset password: {response}")

    def delete_user(self):
        """Delete a user from the server."""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user.")
            return

        selected_display = self.users_listbox.get(selection[0])
        selected_user = selected_display.replace(" (Admin)", "")

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{selected_user}'?"):
            self.disable_controls()
            success, response = self.api_client.delete_user(selected_user)
            self.enable_controls()

            if success:
                self.logger.info(f"User '{selected_user}' deleted successfully.")
                messagebox.showinfo("Success", f"User '{selected_user}' deleted successfully.")
                self.fetch_users_threaded()  # Refresh the user list
            else:
                self.logger.error(f"Failed to delete user: {response}")
                messagebox.showerror("Error", f"Failed to delete user: {response}")

    def toggle_admin_status(self):
        """Toggle admin status for the selected user."""
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user.")
            return

        selected_display = self.users_listbox.get(selection[0])
        selected_user = selected_display.replace(" (Admin)", "")

        # Determine the desired admin status (True for admin, False for not admin)
        desired_admin_status = not self.is_user_admin(selected_user)  # You'll need to implement the is_user_admin method

        self.disable_controls()
        success, response = self.api_client.toggle_admin_status(selected_user, desired_admin_status)
        self.enable_controls()

        if success:
            self.logger.info(f"Admin status for '{selected_user}' toggled successfully.")
            messagebox.showinfo("Success", f"Admin status for '{selected_user}' toggled successfully.")
            self.fetch_users_threaded()  # Refresh the user list
        else:
            self.logger.error(f"Failed to toggle admin status: {response}")
            messagebox.showerror("Error", f"Failed to toggle admin status: {response}")

    def is_user_admin(self, username):
        """Check if the given user is currently an admin."""
        for user in self.users:
            if user.get('username') == username:
                return user.get('is_admin', False)
        return False  # User not found or not an admin

    def validate_username(self, username):
        """Validate the username format."""
        pattern = r"^[a-zA-Z0-9_-]{3,20}$"
        return bool(re.match(pattern, username))

    def validate_password(self, password):
        """Validate the password complexity."""
        if len(password) < 8:
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[0-9]", password):
            return False
        return True

    def disable_controls(self):
        """Disable all buttons to prevent multiple clicks."""
        for widget in self.master.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state='disabled')

    def enable_controls(self):
        """Enable all buttons after an operation."""
        for widget in self.master.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state='normal')