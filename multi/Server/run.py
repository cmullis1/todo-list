# run.py

from app import create_app, db
import logging

def initialize_logging():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("server.log"),
            logging.StreamHandler()
        ]
    )

if __name__ == '__main__':
    initialize_logging()
    app = create_app()
    with app.app_context():
        db.create_all()
        # Create default admin user if not exists
        from app.models import User
        from app.utils.security import hash_password
        import os

        default_admin_username = 'admin'
        default_admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'Admin1!')  # Change this immediately in production

        if not User.query.filter_by(username=default_admin_username).first():
            hashed_pw = hash_password(default_admin_password)
            admin_user = User(username=default_admin_username, password=hashed_pw, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            logging.info(f"Default admin user '{default_admin_username}' created with provided password.")
        else:
            logging.info(f"Default admin user '{default_admin_username}' already exists.")

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
