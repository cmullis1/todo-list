# app/utils/decorators.py

from functools import wraps
from flask import request, jsonify
from ..models import User
from ..utils.security import verify_password
from datetime import datetime
from ..models import db

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing."}), 401

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return jsonify({"error": "Token missing."}), 401

        user = User.query.filter_by(token=token).first()
        if user is None:
            return jsonify({"error": "Invalid or expired token."}), 401

        # Check token expiration
        if user.token_expiration:
            token_expiration = datetime.fromisoformat(user.token_expiration)
            if datetime.utcnow() > token_expiration:
                # Token expired
                user.token = None
                user.token_expiration = None
                db.session.commit()
                return jsonify({"error": "Token has expired."}), 401

        # Attach user to request context
        request.user = user
        return f(*args, **kwargs)
    return decorated
