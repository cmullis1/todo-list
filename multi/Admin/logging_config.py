# logging_config.py

import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Configure logging with module-specific loggers.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler with rotation
    file_handler = RotatingFileHandler("admin_app.log", maxBytes=10**6, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
