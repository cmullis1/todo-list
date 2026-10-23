# app/__init__.py

from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from configparser import ConfigParser

from .models import db
from .auth.routes import auth_ns
from .users.routes import users_ns
from .tasks.routes import tasks_ns

def create_app():
    """Factory to create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    config = ConfigParser()
    config.read('config.ini')

    app.config['SECRET_KEY'] = config['DEFAULT']['SECRET_KEY']
    app.config['SQLALCHEMY_DATABASE_URI'] = config['DEFAULT']['DATABASE_URL']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ACCESS_TOKEN_EXPIRATION_DAYS'] = config.getint('SETTINGS', 'ACCESS_TOKEN_EXPIRATION_DAYS', fallback=7)

    # Initialize extensions
    db.init_app(app)

    # Setup CORS with specified origins
    cors_origins = [origin.strip() for origin in config['CORS']['origins'].split(',')]
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # Initialize Rate Limiter
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=config['SETTINGS']['RATE_LIMIT_DEFAULT'].split(';')
    )

    # Initialize Flask-RESTX API
    api = Api(app, version='1.0', title='Task Manager API',
              description='A simple Task Manager API',
              )

    # Register Namespaces
    api.add_namespace(auth_ns, path='/api/v1/auth')
    api.add_namespace(users_ns, path='/api/v1/users')
    api.add_namespace(tasks_ns, path='/api/v1/tasks')

    # Login gets its own, stricter limit on top of the default one
    login_limit = config.get('SETTINGS', 'RATE_LIMIT_LOGIN', fallback='50 per minute')
    app.view_functions['auth_login'] = limiter.limit(login_limit)(app.view_functions['auth_login'])

    return app
