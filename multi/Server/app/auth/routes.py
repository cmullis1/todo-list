from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from ..models import User
from ..utils.security import hash_password, verify_password, generate_token, is_strong_password, get_token_expiration
from ..schemas import UserSchema
from ..utils.decorators import token_required
from ..models import db
from marshmallow import ValidationError
import logging

auth_ns = Namespace('auth', description='Authentication operations')

login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='The user\'s username'),
    'password': fields.String(required=True, description='The user\'s password'),
})

refresh_model = auth_ns.model('Refresh', {
    'token': fields.String(required=True, description='Current authentication token'),
})

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Success')
    @auth_ns.response(400, 'Validation Error')
    @auth_ns.response(401, 'Unauthorized')
    def post(self):
        """User Login and Token Generation"""
        try:
            data = request.get_json()
            if not data:
                return {"error": "Invalid JSON payload."}, 400

            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return {"error": "Username and password are required."}, 400

            user = User.query.filter_by(username=username).first()

            if user is None:
                return {"exists": False, "login_success": False, "password_set": False}, 404

            password_set = bool(user.password)

            if not password_set:
                return {"exists": True, "login_success": False, "password_set": False, 
                        "message": "Password has not been set, please set a password."}, 401  

            if verify_password(user.password, password):
                # Generate token and set expiration
                token = generate_token()
                token_expiration = get_token_expiration(days=7)  # Token valid for 7 days
                user.token = token
                user.token_expiration = token_expiration.isoformat()
                db.session.commit()
                return {
                    "exists": True,
                    "login_success": True,
                    "is_admin": user.is_admin,
                    "password_set": password_set,
                    "token": token
                }, 200
            else:
                return {
                    "exists": True,
                    "login_success": False,
                    "password_set": password_set, "message": "Invalid username or password"
                }, 401

        except Exception as e:
            logging.exception("An error occurred during login.")
            return {"error": "An internal error occurred."}, 500

@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @auth_ns.expect(refresh_model)
    @auth_ns.response(200, 'Success')
    @auth_ns.response(400, 'Validation Error')
    @auth_ns.response(401, 'Unauthorized')
    def post(self):
        """Refresh Authentication Token"""
        try:
            data = request.get_json()
            if not data or 'token' not in data:
                return {"error": "Token is missing."}, 400

            token = data['token']

            user = User.query.filter_by(token=token).first()

            if user is None:
                return {"error": "Invalid token."}, 401

            # Check token expiration
            if user.token_expiration:
                token_expiration = datetime.fromisoformat(user.token_expiration)
                if datetime.utcnow() > token_expiration:
                    # Token expired
                    user.token = None
                    user.token_expiration = None
                    db.session.commit()
                    return {"error": "Token has expired."}, 401

            # Generate new token and update expiration
            new_token = generate_token()
            new_token_expiration = get_token_expiration(days=7)
            user.token = new_token
            user.token_expiration = new_token_expiration.isoformat()
            db.session.commit()

            return {"token": new_token}, 200

        except Exception as e:
            logging.exception("An error occurred during token refresh.")
            return {"error": "An internal error occurred."}, 500