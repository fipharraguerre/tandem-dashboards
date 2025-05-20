import logging
from logging.handlers import RotatingFileHandler

log_file = "app.log"
logger = logging.getLogger("MyAppLogger")
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler(log_file, maxBytes=1 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
