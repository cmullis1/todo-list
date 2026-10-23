# app/users/routes.py

from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from ..models import User
from ..utils.security import hash_password, is_strong_password
from ..schemas import UserSchema
from ..utils.decorators import token_required
from ..models import db
from marshmallow import ValidationError
import logging

users_ns = Namespace('users', description='User management operations')

user_model = users_ns.model('User', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=False, description='Password'),
    'is_admin': fields.Boolean(required=False, description='Admin status'),
})

delete_user_model = users_ns.model('DeleteUser', {
    'username': fields.String(required=True, description='Username to delete'),
})

@users_ns.route('/')
class ManageUsers(Resource):
    @users_ns.doc('get_users')
    @users_ns.response(200, 'Success', model=users_ns.model('UserList', {'users': fields.List(fields.Nested(user_model))}))
    @users_ns.response(403, 'Forbidden')
    @users_ns.marshal_list_with(user_model)
    @token_required
    def get(self):
        """Get All Users (Admin Only)"""
        user = request.user
        if not user.is_admin:
            return {"error": "Unauthorized access."}, 403

        users = User.query.all()

        users_list = [{"username": u.username, "is_admin": u.is_admin} for u in users]
        return users_list, 200

    @users_ns.doc('create_user')
    @users_ns.expect(user_model)
    @users_ns.response(201, 'User Created')
    @users_ns.response(400, 'Validation Error')
    @users_ns.response(403, 'Forbidden')
    @users_ns.response(409, 'Conflict')
    @token_required
    def post(self):
        """Create a New User (Admin Only)"""
        user = request.user
        if not user.is_admin:
            return {"error": "Unauthorized access."}, 403

        try:
            data = request.get_json()
            user_data = UserSchema().load(data)
        except ValidationError as err:
            return err.messages, 400

        new_username = user_data['username']
        new_password = user_data.get('password', '')
        is_admin = user_data.get('is_admin', False)

        # Enforce strong password policies
        if new_password and not is_strong_password(new_password):
            return {"error": "Password does not meet complexity requirements."}, 400

        hashed_pw = hash_password(new_password) if new_password else ''

        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user:
            return {"error": "Username already exists."}, 409

        try:
            new_user = User(username=new_username, password=hashed_pw, is_admin=is_admin)
            db.session.add(new_user)
            db.session.commit()
            logging.info(f"User '{new_username}' created by admin.")
            return {"message": "User created successfully."}, 201
        except Exception as e:
            db.session.rollback()
            logging.exception("An error occurred while creating a user.")
            return {"error": "An internal error occurred."}, 500

    @users_ns.doc('update_user')
    @users_ns.expect(user_model)
    @users_ns.response(200, 'User Updated')
    @users_ns.response(400, 'Validation Error')
    @users_ns.response(403, 'Forbidden')
    @users_ns.response(404, 'Not Found')
    @token_required
    def put(self):
        """Update an Existing User (Admin Only)"""
        user = request.user
        if not user.is_admin:
            return {"error": "Unauthorized access."}, 403

        try:
            data = request.get_json()
            user_data = UserSchema().load(data, partial=True)
        except ValidationError as err:
            return err.messages, 400

        username = user_data.get('username')
        if not username:
            return {"error": "Username is required for update."}, 400

        new_password = user_data.get('password')
        new_is_admin = user_data.get('is_admin')

        user_record = User.query.filter_by(username=username).first()
        if user_record is None:
            return {"error": "User does not exist."}, 404

        if new_password:
            user_record.password = hash_password(new_password)
        if new_is_admin is not None:
            user_record.is_admin = new_is_admin

        try:
            db.session.commit()
            logging.info(f"User '{username}' updated by admin.")
            return {"message": "User updated successfully."}, 200
        except Exception as e:
            db.session.rollback()
            logging.exception("An error occurred while updating a user.")
            return {"error": "An internal error occurred."}, 500

    @users_ns.doc('delete_user')
    @users_ns.expect(delete_user_model)
    @users_ns.response(200, 'User Deleted')
    @users_ns.response(400, 'Validation Error')
    @users_ns.response(403, 'Forbidden')
    @users_ns.response(404, 'Not Found')
    @token_required
    def delete(self):
        """Delete a User (Admin Only)"""
        user = request.user
        if not user.is_admin:
            return {"error": "Unauthorized access."}, 403

        data = request.get_json()
        username = data.get('username')

        if not username:
            return {"error": "Username is required for deletion."}, 400

        if username.lower() == "admin":
            return {"error": "Cannot delete the default admin user."}, 403

        user_to_delete = User.query.filter_by(username=username).first()
        if user_to_delete is None:
            return {"error": "User does not exist."}, 404

        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            logging.info(f"User '{username}' deleted by admin.")
            return {"message": "User deleted successfully."}, 200
        except Exception as e:
            db.session.rollback()
            logging.exception("An error occurred while deleting a user.")
            return {"error": "An internal error occurred."}, 500
