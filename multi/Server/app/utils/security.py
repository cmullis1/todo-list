# app/utils/security.py

import bcrypt
import uuid
from datetime import datetime, timedelta

def hash_password(password):
    """Hash a password using bcrypt."""
    if not password:
        return ''
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(hashed_password, provided_password):
    """Verify a password against the hashed version."""
    if not hashed_password or not provided_password:
        return False
    return bcrypt.checkpw(provided_password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_token():
    """Generate a unique UUID4 token."""
    return str(uuid.uuid4())

def is_strong_password(password):
    """Check if the password meets complexity requirements."""
    if len(password) < 8:
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for c in password):
        return False
    return True

def get_token_expiration(days=7):
    """Get token expiration datetime."""
    return datetime.utcnow() + timedelta(days=days)
