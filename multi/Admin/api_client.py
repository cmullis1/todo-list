# api_client.py

import requests
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

class APIClient:
    """
    Client to interact with the Server App's API.
    """

    def __init__(self, config):
        """
        Initialize the API client.

        Args:
            config (dict): Configuration dictionary containing SERVER_URL.
        """
        self.server_url = config.get("SERVER_URL", "http://127.0.0.1:5000/api/v1")
        self.session = requests.Session()
        self.token = None  # Store authentication token
        self.username = None  # Store logged-in username
        self.is_admin = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self.executor = ThreadPoolExecutor(max_workers=5)  # Limit concurrent threads

        # Caches
        self.users_cache = None
        self.tasks_cache = {}  # Initialize as an empty dictionary
        self.cache_timestamp = {
            "users": 0,
            "tasks": {}
        }
        self.cache_duration = 300  # Cache duration in seconds (5 minutes)

    def login(self, username, password):
        """
        Authenticate with the server using username and password.

        Args:
            username (str): The username.
            password (str): The password.

        Returns:
            tuple: (success: bool, message: str or None)
        """
        url = f"{self.server_url}/auth/login"
        data = {"username": username, "password": password}
        try:
            self.logger.info(f"Attempting to log in user '{username}'.")
            response = self.session.post(url, json=data, timeout=5)
            if response.status_code == 200:
                res = response.json()
                if res.get("login_success"):
                    self.username = username
                    self.is_admin = res.get("is_admin", False)  # Ensure this line correctly sets is_admin
                    self.token = res.get("token")  # Store the token
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})  # Update headers with token
                    self.logger.info(f"User '{username}' logged in successfully. Admin status: {self.is_admin}")
                    return True, None
                else:
                    self.logger.warning(f"Login failed for user '{username}': {res}")
                    return False, "Login failed: Check your credentials."
            elif response.status_code == 401:
                res = response.json()
                if not res.get("exists"):
                    return False, "User does not exist."
                elif not res.get("password_set"):
                    return False, "Password not set for this user."
                else:
                    return False, "Invalid credentials."
            elif response.status_code == 404:
                return False, "Endpoint not found."
            else:
                self.logger.error(f"Login failed with status code {response.status_code}: {response.text}")
                return False, f"Login failed: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Login request failed: {e}")
            return False, str(e)
    
    def logout(self):
        """
        Log out the current user by clearing the session and resetting user data.
        """
        self.session.headers.pop("Authorization", None)  # Remove Authorization header
        self.token = None
        self.username = None
        self.is_admin = False
        self.users_cache = None  # Clear cache
        self.tasks_cache = {}
        self.cache_timestamp = {
            "users": 0,
            "tasks": {}
        }
        self.logger.info(f"User '{self.username}' logged out.")
    
    def get_headers(self):
        """
        Get the headers for authenticated requests.

        Returns:
            dict: Headers dictionary with Authorization.
        """
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def get_users(self, force_refresh=False):
        """
        Fetch all users from the server. Only admin can perform this action.

        Args:
            force_refresh (bool): If True, bypass the cache and fetch fresh data.

        Returns:
            tuple: (success: bool, users: list or error message: str)
        """
        current_time = datetime.now().timestamp()
        if self.users_cache and not force_refresh and (current_time - self.cache_timestamp["users"] < self.cache_duration):
            return True, self.users_cache

        return self._fetch_users_from_server()

    def _fetch_users_from_server(self):
        """
        Internal method to fetch users from the server.

        Returns:
            tuple: (success: bool, users: list or error message: str)
        """
        url = f"{self.server_url}/users"
        headers = self.get_headers()
        try:
            self.logger.info("Fetching users from server.")
            response = self.session.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                users = response.json()  # Assuming the server returns a list
                self.users_cache = users
                self.cache_timestamp["users"] = datetime.now().timestamp()
                return True, users
            elif response.status_code == 403:
                self.logger.warning("Unauthorized access when fetching users.")
                return False, "Admin privileges required."
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when fetching users.")
                return False, "Unauthorized access."
            else:
                self.logger.error(f"Failed to fetch users: {response.status_code} - {response.text}")
                return False, f"Failed to fetch users: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while fetching users: {e}")
            return False, str(e)

    def get_tasks(self, user_filter="All", force_refresh=False):
        """
        Fetch tasks, optionally filtered by a specific user.

        Args:
            user_filter (str): The username to filter tasks by, or "All".
            force_refresh (bool): If True, bypass the cache and fetch fresh data.

        Returns:
            tuple: (success: bool, tasks: list or error message: str)
        """
        current_time = datetime.now().timestamp()
        cache_key = f"tasks_{user_filter}"
        if (cache_key in self.tasks_cache and
            not force_refresh and
            (current_time - self.cache_timestamp["tasks"].get(cache_key, 0) < self.cache_duration)):
            self.logger.debug(f"Using cached tasks for '{user_filter}'.")
            return True, self.tasks_cache[cache_key]

        return self._fetch_tasks_from_server(user_filter, cache_key)

    def _fetch_tasks_from_server(self, user_filter, cache_key):
        """
        Internal method to fetch tasks from the server.

        Args:
            user_filter (str): The username to filter tasks by, or "All".
            cache_key (str): The cache key for storing tasks.

        Returns:
            tuple: (success: bool, tasks: list or error message: str)
        """
        url = f"{self.server_url}/tasks"
        headers = self.get_headers()
        params = {}
        if user_filter.lower() != "all":
            params['user'] = user_filter
        try:
            self.logger.info(f"Fetching tasks from server with filter: {user_filter}.")
            response = self.session.get(url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                tasks = response.json()  # Assuming the server returns a list
                self.tasks_cache[cache_key] = tasks if tasks else []
                self.cache_timestamp["tasks"][cache_key] = datetime.now().timestamp()
                if tasks:
                    self.logger.info(f"Fetched {len(tasks)} tasks for '{user_filter}'.")
                else:
                    self.logger.info(f"No tasks found for '{user_filter}'.")
                return True, tasks
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when fetching tasks.")
                return False, "Unauthorized access."
            else:
                self.logger.error(f"Failed to fetch tasks: {response.status_code} - {response.text}")
                return False, f"Failed to fetch tasks: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while fetching tasks: {e}")
            return False, str(e)

    def create_user(self, username, password, is_admin=False):
        """
        Create a new user.

        Args:
            username (str): The username for the new user.
            password (str): The password for the new user.
            is_admin (bool): Whether the new user has admin privileges.

        Returns:
            tuple: (success: bool, message: str)
        """
        url = f"{self.server_url}/users"
        headers = self.get_headers()
        data = {
            "username": username,
            "password": password,
            "is_admin": is_admin
        }
        try:
            self.logger.info(f"Creating user '{username}' with admin status: {is_admin}.")
            response = self.session.post(url, headers=headers, json=data, timeout=5)
            if response.status_code == 201:
                self.logger.info(f"User '{username}' created successfully.")
                # Invalidate the users cache
                self.users_cache = None
                return True, "User created successfully."
            elif response.status_code == 409:
                self.logger.warning(f"User '{username}' already exists.")
                return False, "Username already exists."
            elif response.status_code == 400:
                self.logger.warning(f"Bad request when creating user '{username}': {response.json().get('message')}")
                return False, response.json().get("message", "Bad request.")
            elif response.status_code == 403:
                self.logger.warning("Unauthorized access when creating a user.")
                return False, "Admin privileges required."
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when creating a user.")
                return False, "Unauthorized access."
            else:
                self.logger.error(f"Failed to create user: {response.status_code} - {response.text}")
                return False, f"Failed to create user: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while creating user: {e}")
            return False, str(e)

    def reset_password(self, username, new_password):
        """
        Reset a user's password.

        Args:
            username (str): The username whose password is to be reset.
            new_password (str): The new password.

        Returns:
            tuple: (success: bool, message: str)
        """
        url = f"{self.server_url}/users"
        headers = self.get_headers()
        data = {
            "username": username,
            "password": new_password
        }
        try:
            self.logger.info(f"Resetting password for user '{username}'.")
            response = self.session.put(url, headers=headers, json=data, timeout=5)
            if response.status_code == 200:
                self.logger.info(f"Password for user '{username}' reset successfully.")
                # Optionally, invalidate specific caches if necessary
                return True, "Password reset successfully."
            elif response.status_code == 404:
                self.logger.warning(f"User '{username}' not found for password reset.")
                return False, "User does not exist."
            elif response.status_code == 400:
                self.logger.warning(f"Bad request when resetting password for '{username}': {response.json().get('message')}")
                return False, response.json().get("message", "Bad request.")
            elif response.status_code == 403:
                self.logger.warning("Unauthorized access when resetting a user's password.")
                return False, "Admin privileges required."
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when resetting a user's password.")
                return False, "Unauthorized access."
            else:
                self.logger.error(f"Failed to reset password: {response.status_code} - {response.text}")
                return False, f"Failed to reset password: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while resetting password: {e}")
            return False, str(e)

    def delete_user(self, username):
        """
        Delete a user.

        Args:
            username (str): The username to delete.

        Returns:
            tuple: (success: bool, message: str)
        """
        url = f"{self.server_url}/users"
        headers = self.get_headers()
        data = {
            "username": username
        }
        try:
            self.logger.info(f"Deleting user '{username}'.")
            response = self.session.delete(url, headers=headers, json=data, timeout=5)
            if response.status_code == 200:
                self.logger.info(f"User '{username}' deleted successfully.")
                # Invalidate the users cache
                self.users_cache = None
                return True, "User deleted successfully."
            elif response.status_code == 404:
                self.logger.warning(f"User '{username}' not found for deletion.")
                return False, "User does not exist."
            elif response.status_code == 403:
                self.logger.warning(f"Attempted to delete protected user '{username}'.")
                return False, "Cannot delete the default admin user."
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when deleting a user.")
                return False, "Unauthorized access."
            else:
                self.logger.error(f"Failed to delete user: {response.status_code} - {response.text}")
                return False, f"Failed to delete user: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while deleting user: {e}")
            return False, str(e)

    def toggle_admin_status(self, username, is_admin):
        """
        Toggle a user's admin status.

        Args:
            username (str): The username whose admin status is to be toggled.
            is_admin (bool): The new admin status.

        Returns:
            tuple: (success: bool, message: str)
        """
        url = f"{self.server_url}/users"
        headers = self.get_headers()
        data = {
            "username": username,
            "is_admin": is_admin
        }
        try:
            action = "Promoted" if is_admin else "Demoted"
            self.logger.info(f"{action} user '{username}' to admin status: {is_admin}.")
            response = self.session.put(url, headers=headers, json=data, timeout=5)
            if response.status_code == 200:
                self.logger.info(f"User '{username}' {action.lower()} successfully.")
                # Invalidate the users cache
                self.users_cache = None
                return True, f"User '{username}' {action.lower()} successfully."
            elif response.status_code == 404:
                self.logger.warning(f"User '{username}' not found for admin status toggle.")
                return False, "User does not exist."
            elif response.status_code == 403:
                self.logger.warning(f"Attempted to modify admin status for protected user '{username}'.")
                return False, "Cannot modify the default admin user."
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when toggling admin status.")
                return False, "Unauthorized access."
            else:
                self.logger.error(f"Failed to toggle admin status: {response.status_code} - {response.text}")
                return False, f"Failed to toggle admin status: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while toggling admin status: {e}")
            return False, str(e)

    def create_task(self, task_data):
        """
        Create a new task.

        Args:
            task_data (dict): The task data.

        Returns:
            tuple: (success: bool, message: str)
        """
        url = f"{self.server_url}/tasks"
        headers = self.get_headers()
        try:
            self.logger.info(f"Creating task '{task_data.get('task_name')}' assigned to '{task_data.get('assigned_to')}'.")
            response = self.session.post(url, headers=headers, json=task_data, timeout=5)
            if response.status_code == 201:
                self.logger.info("Task created successfully.")
                # Invalidate the tasks cache
                self.tasks_cache = {}
                self.cache_timestamp["tasks"] = {}
                return True, "Task created successfully."
            elif response.status_code == 404:
                self.logger.warning(f"Assigned user '{task_data.get('assigned_to')}' does not exist.")
                return False, f"Assigned user '{task_data.get('assigned_to')}' does not exist."
            elif response.status_code == 400:
                self.logger.warning(f"Bad request when creating task: {response.json().get('message')}")
                return False, response.json().get("message", "Bad request.")
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when creating a task.")
                return False, "Unauthorized access."
            else:
                self.logger.error(f"Failed to create task: {response.status_code} - {response.text}")
                return False, f"Failed to create task: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while creating task: {e}")
            return False, str(e)

    def update_task(self, task_id, updates):
        """
        Update an existing task.

        Args:
            task_id (str): The ID of the task to update.
            updates (dict): The updates to apply.

        Returns:
            tuple: (success: bool, message: str)
        """
        url = f"{self.server_url}/tasks"
        headers = self.get_headers()
        data = {"task_id": task_id}
        data.update(updates)
        try:
            self.logger.info(f"Updating task '{task_id}'.")
            response = self.session.put(url, headers=headers, json=data, timeout=5)
            if response.status_code == 200:
                self.logger.info(f"Task '{task_id}' updated successfully.")
                # Invalidate the tasks cache
                self.tasks_cache = {}
                self.cache_timestamp["tasks"] = {}
                return True, "Task updated successfully."
            elif response.status_code == 403:
                self.logger.warning(f"Unauthorized attempt to update task '{task_id}'.")
                return False, "Unauthorized to update this task."
            elif response.status_code == 404:
                self.logger.warning(f"Task '{task_id}' does not exist.")
                return False, "Task does not exist."
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when updating a task.")
                return False, "Unauthorized access."
            else:
                self.logger.error(f"Failed to update task: {response.status_code} - {response.text}")
                return False, f"Failed to update task: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while updating task: {e}")
            return False, str(e)

    def delete_task(self, task_id):
        """
        Delete a task.

        Args:
            task_id (str): The ID of the task to delete.

        Returns:
            tuple: (success: bool, message: str)
        """
        url = f"{self.server_url}/tasks"
        headers = self.get_headers()
        data = {"task_id": task_id}
        try:
            self.logger.info(f"Deleting task '{task_id}'.")
            response = self.session.delete(url, headers=headers, json=data, timeout=5)
            if response.status_code == 200:
                self.logger.info(f"Task '{task_id}' deleted successfully.")
                # Invalidate the tasks cache
                self.tasks_cache = {}
                self.cache_timestamp["tasks"] = {}
                return True, "Task deleted successfully."
            elif response.status_code == 403:
                self.logger.warning(f"Unauthorized attempt to delete task '{task_id}'.")
                return False, "Unauthorized to delete this task."
            elif response.status_code == 404:
                self.logger.warning(f"Task '{task_id}' does not exist.")
                return False, "Task does not exist."
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when deleting a task.")
                return False, "Unauthorized access."
            else:
                self.logger.error(f"Failed to delete task: {response.status_code} - {response.text}")
                return False, f"Failed to delete task: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while deleting task: {e}")
            return False, str(e)

    def get_task(self, task_id):
        """
        Fetch a single task's details.

        Args:
            task_id (str): The ID of the task.

        Returns:
            tuple: (success: bool, task: dict or error message: str)
        """
        url = f"{self.server_url}/tasks/{task_id}"
        headers = self.get_headers()
        try:
            self.logger.info(f"Fetching details for task '{task_id}'.")
            response = self.session.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                task = response.json()
                if task:
                    return True, task
                else:
                    self.logger.warning(f"Task '{task_id}' not found.")
                    return False, "Task does not exist."
            elif response.status_code == 401:
                self.logger.warning("Unauthorized access when fetching task details.")
                return False, "Unauthorized access."
            elif response.status_code == 404:
                self.logger.warning(f"Task '{task_id}' not found.")
                return False, "Task does not exist."
            else:
                self.logger.error(f"Failed to fetch task details: {response.status_code} - {response.text}")
                return False, f"Failed to fetch task details: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed while fetching task details: {e}")
            return False, str(e)
