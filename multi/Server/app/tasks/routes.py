# app/tasks/routes.py

import json  # Import the json module

from flask_restx import Namespace, Resource, fields, Api
from flask import Flask, request, jsonify
from ..models import User, Task
from ..utils.security import is_strong_password
from ..schemas import TaskSchema
from ..utils.decorators import token_required
from ..models import db
from marshmallow import ValidationError
import logging
import datetime

tasks_ns = Namespace('tasks', description='Task management operations')

task_model = tasks_ns.model('Task', {
    'task_name': fields.String(required=True, description='Name of the task'),
    'assigned_to': fields.String(required=True, description='Username of the assignee'),
    'completed': fields.Boolean(required=False, description='Completion status'),
    'due_date': fields.String(required=False, description='Due date in MM/DD/YYYY'),
    'due_time': fields.String(required=False, description='Due time in HH:MM AM/PM'),
    'priority': fields.String(required=False, description='Priority level', 
    enum=["Urgent", "Normal", "Low"]),
    'details': fields.String(required=False, description='Additional details'),
    'task_id': fields.Integer(required=False, description='ID of the task'),
})

delete_task_model = tasks_ns.model('DeleteTask', {
    'task_id': fields.Integer(required=True, description='ID of the task to delete')
})

class TaskEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Task):
            return {
                "task_id": o.id,
                "task_name": o.task_name,
                "assigned_to": o.assigned_to,
                "completed": o.completed,
                "due_date": self.format_datetime(o.due_date), 
                "due_time": self.format_datetime(o.due_time), 
                "priority": o.priority,
                "details": o.details,
            }
        return super().default(o)

    def format_datetime(self, dt):
        if isinstance(dt, datetime.datetime):  # Check if it's a datetime object
            return dt.isoformat()  # Or your preferred datetime format
        return dt

@tasks_ns.route('/')

class ManageTasks(Resource):
    @tasks_ns.doc('get_tasks')
    @tasks_ns.expect(tasks_ns.parser().add_argument('user', type=str, required=False, help='Filter tasks by user'))
    @tasks_ns.response(200, 'Success', model=tasks_ns.model('TaskList', {'tasks': fields.List(fields.Nested(task_model))}))
    @tasks_ns.marshal_list_with(task_model)
    @token_required
    def get(self):
        """Get All Tasks or Tasks Assigned to a Specific User"""
        user = request.user
        username = request.args.get('user')

        if username and username.lower() != "all":
            if not user.is_admin and user.username != username:
                return {"error": "Unauthorized access."}, 403
            tasks = Task.query.filter_by(assigned_to=username).all()
        else:
            if not user.is_admin:
                tasks = Task.query.filter_by(assigned_to=user.username).all()
            else:
                tasks = Task.query.all()

        tasks_list = []
        
        for task in tasks:
            task_dict = {
                "task_name": task.task_name,
                "assigned_to": task.assigned_to,
                "completed": task.completed,
                "due_date": task.due_date,
                "due_time": task.due_time,
                "priority": task.priority,
                "details": task.details,
                "task_id": task.id
            }
            tasks_list.append(task_dict)

        return tasks_list, 200

    @tasks_ns.doc('create_task')
    @tasks_ns.expect(task_model)
    @tasks_ns.response(201, 'Task Created')
    @tasks_ns.response(400, 'Validation Error')
    @tasks_ns.response(403, 'Forbidden')
    @tasks_ns.response(404, 'Not Found')
    @token_required
    def post(self):
        """Create a New Task (Admin or Assigned User)"""
        user = request.user

        try:
            data = request.get_json()
            task_data = TaskSchema().load(data)
        except ValidationError as err:
            return err.messages, 400

        task_name = task_data['task_name']
        assigned_to = task_data['assigned_to']
        completed = task_data.get('completed', False)
        due_date = task_data.get('due_date')
        due_time = task_data.get('due_time')
        priority = task_data.get('priority', "Normal")
        details = task_data.get('details', '')

        # Only admins can assign tasks to others
        if not user.is_admin and user.username != assigned_to:
            return {"error": "Unauthorized to assign tasks to other users."}, 403

        assignee = User.query.filter_by(username=assigned_to).first()
        if assignee is None:
            return {"error": f"Assigned user '{assigned_to}' does not exist."}, 404

        try:
            new_task = Task(
                task_name=task_name,
                assigned_to=assigned_to,
                completed=completed,
                due_date=due_date,
                due_time=due_time,
                priority=priority,
                details=details
            )
            db.session.add(new_task)
            db.session.commit()
            logging.info(f"Task '{task_name}' assigned to '{assigned_to}' by '{user.username}'.")
            return {"message": "Task created successfully."}, 201
        except Exception as e:
            db.session.rollback()
            logging.exception("An error occurred while creating a task.")
            return {"error": "An internal error occurred."}, 500

    @tasks_ns.doc('update_task')
    @tasks_ns.expect(task_model)
    @tasks_ns.response(200, 'Task Updated')
    @tasks_ns.response(400, 'Validation Error')
    @tasks_ns.response(403, 'Forbidden')
    @tasks_ns.response(404, 'Not Found')
    @token_required
    def put(self):
        """Update an Existing Task (Admin or Assigned User)"""
        user = request.user

        try:
            data = request.get_json()
            task_data = TaskSchema().load(data, partial=True)
        except ValidationError as err:
            return err.messages, 400

        task_id = task_data.get('task_id')
        if not task_id:
            return {"error": "Task ID is required for update."}, 400

        task = Task.query.filter_by(id=task_id).first()
        if task is None:
            return {"error": "Task does not exist."}, 404

        # Authorization: Admins can update any task; users can update their own tasks
        if not user.is_admin and user.username != task.assigned_to:
            return {"error": "Unauthorized to update this task."}, 403

        if 'task_name' in task_data:
            task.task_name = task_data['task_name']
        if 'assigned_to' in task_data:
            assignee = User.query.filter_by(username=task_data['assigned_to']).first()
            if assignee is None:
                return {"error": f"Assigned user '{task_data['assigned_to']}' does not exist."}, 404
            task.assigned_to = task_data['assigned_to']
        if 'completed' in task_data:
            task.completed = task_data['completed']
        if 'due_date' in task_data:
            task.due_date = task_data['due_date']
        if 'due_time' in task_data:
            task.due_time = task_data['due_time']
        if 'priority' in task_data:
            task.priority = task_data['priority']
        if 'details' in task_data:
            task.details = task_data['details']

        try:
            db.session.commit()
            logging.info(f"Task ID '{task_id}' updated by '{user.username}'.")
            return {"message": "Task updated successfully."}, 200
        except Exception as e:
            db.session.rollback()
            logging.exception("An error occurred while updating a task.")
            return {"error": "An internal error occurred."}, 500

    @tasks_ns.doc('delete_task')
    @tasks_ns.expect(delete_task_model)
    @tasks_ns.response(200, 'Task Deleted')
    @tasks_ns.response(400, 'Validation Error')
    @tasks_ns.response(403, 'Forbidden')
    @tasks_ns.response(404, 'Not Found')
    @token_required
    def delete(self):
        """Delete a Task (Admin or Assigned User)"""
        user = request.user
        data = request.get_json()
        task_id = data.get('task_id')

        if not task_id:
            return {"error": "Task ID is required for deletion."}, 400

        task = Task.query.filter_by(id=task_id).first()
        if task is None:
            return {"error": "Task does not exist."}, 404

        # Authorization: Admins can delete any task; users can delete their own tasks
        if not user.is_admin and user.username != task.assigned_to:
            return {"error": "Unauthorized to delete this task."}, 403

        try:
            db.session.delete(task)
            db.session.commit()
            logging.info(f"Task ID '{task_id}' deleted by '{user.username}'.")
            return {"message": "Task deleted successfully."}, 200
        except Exception as e:
            db.session.rollback()
            logging.exception("An error occurred while deleting a task.")
            return {"error": "An internal error occurred."}, 500

@tasks_ns.route('/<int:task_id>')
class ManageSingleTask(Resource):
    @token_required
    def get(self, task_id):
        """Get a single task by ID."""
        task = Task.query.get_or_404(task_id)  # Corrected line

        user = request.user
        if not user.is_admin and user.username != task.assigned_to:
            return {"error": "Unauthorized to view this task."}, 403

        # Serialize the task using the custom encoder
        task_data = json.dumps(task, cls=TaskEncoder)  

        # Return the serialized data with jsonify, ensuring it's parsed as a dictionary
        return jsonify(json.loads(task_data))