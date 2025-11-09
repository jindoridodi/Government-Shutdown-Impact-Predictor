"""
Centralized logging configuration for the application.
Provides a configured logger instance that can be imported across modules.
"""

import logging
import sys
from pathlib import Path


def setup_logger(name='predictor', log_file='predictor.log', level=logging.INFO, 
                 filemode='w', format_string=None):
    """
    Set up and configure a logger instance.
    
    Args:
        name: Logger name (default: 'predictor')
        log_file: Path to log file (default: 'predictor.log')
        level: Logging level (default: logging.INFO)
        filemode: File mode - 'w' to overwrite, 'a' to append (default: 'w')
        format_string: Custom format string (default: '%(asctime)s:%(levelname)s:%(message)s')
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if logger already exists
    if logger.handlers:
        return logger
    
    # Default format
    if format_string is None:
        format_string = '%(asctime)s:%(levelname)s:%(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # File handler - write to log file
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, mode=filemode, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler - also log to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Create default logger instance for predictor
# This can be imported directly: from utils.logger import logger
logger = setup_logger(name='predictor', log_file='predictor.log', 
                     level=logging.INFO, filemode='w')

