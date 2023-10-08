import logging


class Logger:
    def __init__(self, level=logging.INFO):
        logging.basicConfig(
            filename='app.log',
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def get_logger(self, name):
        return logging.getLogger(name)
