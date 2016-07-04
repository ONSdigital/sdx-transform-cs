import logging
import logging.handlers
import os
import errno

logger = logging.getLogger(__name__)

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: sdx-transform-cs: %(message)s"
LOGGING_LOCATION = "logs/transform.log"
LOGGING_LEVEL = logging.DEBUG

IMAGE_PATH = "\\\\NP3RVWAPXX370\SDX_preprod\EDC_QImages\Images"


def mkdir_p(path):
    """http://stackoverflow.com/a/600612/190597 (tzot)"""
    try:
        os.makedirs(path, exist_ok=True)
    except TypeError:
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


class MakeFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename, **kwargs):
        mkdir_p(os.path.dirname(filename))
        logging.handlers.RotatingFileHandler.__init__(self, filename, **kwargs)
