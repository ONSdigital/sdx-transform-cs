import logging
import os

logger = logging.getLogger(__name__)

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: %(message)s"
LOGGING_LOCATION = "logs/validate.log"
LOGGING_LEVEL = logging.DEBUG

# Default to true, cast to boolean
WRITE_BATCH_HEADER = os.getenv("WRITE_BATCH_HEADER", "true")
WRITE_BATCH_HEADER = (WRITE_BATCH_HEADER.lower() == "true")
