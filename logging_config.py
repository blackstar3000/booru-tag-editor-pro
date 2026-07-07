import logging
import logging.handlers
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "logs" / "booru_editor.log"

def setup_logging():
    LOG_PATH.parent.mkdir(exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # file handler (rotating)
    fh = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=10*1024*1024, backupCount=5)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger