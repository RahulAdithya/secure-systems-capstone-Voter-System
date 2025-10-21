import logging
from logging.handlers import RotatingFileHandler

# Create logger
auth_logger = logging.getLogger("auth")
auth_logger.setLevel(logging.INFO)

# Prevent duplicate handlers
if not auth_logger.handlers:
    # Rotating file handler: max 5 MB per file, keep 3 backups
    file_handler = RotatingFileHandler("auth.log", maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    auth_logger.addHandler(file_handler)
    
