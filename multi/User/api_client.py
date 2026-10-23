# api_client.py

import requests
import logging

class APIClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.session = requests.Session()
        self.token = None
        self.username = None
        self.logger = logging.getLogger(__name__)

    def login(self, username, password):
        url = f"{self.server_url}/auth/login"
        data = {"username": username, "password": password}
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get("login_success"):
                    self.token = result.get("token")
                    self.username = username
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    return True, None
                else:
                    return False, "Invalid username or password"
            elif response.status_code in (401, 404):
                return False, "Invalid username or password"
            else:
                return False, f"Login failed: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Login request failed: {e}"

    def get_tasks(self):
        """Fetch the tasks assigned to the logged-in user. Returns (success, tasks or error)."""
        url = f"{self.server_url}/tasks/"
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return True, response.json()
            else:
                self.logger.error(f"Failed to fetch tasks: {response.status_code} - {response.text}")
                return False, f"Failed to fetch tasks: {response.text}"
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch tasks: {e}")
            return False, f"Failed to fetch tasks: {e}"

    def mark_completed(self, task_id):
        """Mark one of the user's tasks as completed. Returns (success, message)."""
        url = f"{self.server_url}/tasks/"
        data = {"task_id": task_id, "completed": True}
        try:
            response = self.session.put(url, json=data)
            if response.status_code == 200:
                return True, "Task marked as completed."
            else:
                return False, f"Failed to update task: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"Task update request failed: {e}"
