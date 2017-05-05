import logging
import requests
import os
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: sdx-transform-cs: %(message)s"
LOGGING_LEVEL = logging.getLevelName(os.getenv('LOGGING_LEVEL', 'DEBUG'))

SDX_SEQUENCE_URL = os.getenv("SDX_SEQUENCE_URL")

FTP_HOST = os.getenv("FTP_PATH")
SDX_FTP_IMAGE_PATH = os.getenv("SDX_FTP_IMAGES_PATH")
SDX_FTP_DATA_PATH = os.getenv("SDX_FTP_DATA_PATH")
SDX_FTP_RECEIPT_PATH = os.getenv("SDX_FTP_RECEIPT_PATH")

# Configure the number of retries attempted before failing call
session = requests.Session()

retries = Retry(total=5, backoff_factor=0.1)

session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))
