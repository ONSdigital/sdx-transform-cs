import logging

from flask import Flask
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from . import settings
from .views.logger_config import logger_initial_config

app = Flask(__name__)

from .views import main  # noqa
__version__ = "4.3.0"

logger_initial_config(service_name='sdx-transform-cs',
                      log_level=settings.LOGGING_LEVEL)

logging.info("Starting server: version='{}'".format(__version__))

# Configure the number of retries attempted before failing call
session = requests.Session()

retries = Retry(total=5, backoff_factor=0.1)

session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))
