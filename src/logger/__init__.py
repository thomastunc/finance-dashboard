import logging
from logging.handlers import RotatingFileHandler


class Logger:
    def __init__(self, log_file_path, log_level=logging.INFO):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level)

        # Create a rotating file handler for log file
        file_handler = RotatingFileHandler(log_file_path, maxBytes=1024 * 1024, backupCount=5)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        self.log.addHandler(file_handler)

    def get_logger(self, name):
        return self.log.getChild(name)
