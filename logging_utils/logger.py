# logging_utils/logger.py
# Centralized logging setup for the backup utility.
# Writes structured log entries to a file, and also prints to console.

import logging
import os

def get_logger():
    """Returns a configured logger instance for the backup tool."""
    os.makedirs('logs', exist_ok=True)

    logger = logging.getLogger('db_backup_utility')# gets (or creates) a named logger. Using a name (not the root logger) is best practice — it lets other parts of a bigger app have their own loggers without interfering with yours
    logger.setLevel(logging.INFO) #sets the minimum severity to record. Levels go DEBUG < INFO < WARNING < ERROR < CRITICAL. Setting INFO means DEBUG messages get ignored, but INFO and above get logged.

    # Avoid adding duplicate handlers if get_logger() is called multiple times
    if not logger.handlers:
        file_handler = logging.FileHandler('logs/backup_activity.log')
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
#Handlers — a logger can send output to multiple destinations. FileHandler writes to logs/backup_activity.log; StreamHandler prints to your terminal too. So you get both a permanent record and live feedback.
#Formatter — controls what each log line looks like: 2026-07-21 14:32:10 | INFO | Backup started for test.db
#The if not logger.handlers: guard prevents duplicate log lines if this function gets called more than once in the same run (a common gotcha with Python's logging module)