import logging
import os

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: sdx-transform-cs: %(message)s"
LOGGING_LEVEL = logging.getLevelName(os.getenv('LOGGING_LEVEL', 'DEBUG'))

logger = logging.getLogger(__name__)


def _get_value(key, default_value=None):
    """Gets a value from an environment variable , will use default if present else raise a value Error
    """
    value = os.getenv(key, default_value)
    if not value:
        logger.error("No value set for {}".format(key))
        raise ValueError()
    return value


SDX_SEQUENCE_URL = _get_value("SDX_SEQUENCE_URL", "http://sdx-sequence:5000")
FTP_PATH = _get_value("FTP_PATH", "\\\\NP3RVWAPXX370\\SDX_preprod\\")
SDX_FTP_IMAGE_PATH = _get_value("SDX_FTP_IMAGES_PATH", "EDC_QImages")

SDX_FTP_DATA_PATH = "EDC_QData"
SDX_FTP_RECEIPT_PATH = "EDC_QReceipts"
