from flask import Flask
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

app = Flask(__name__)

from .views import main  # noqa

__version__ = "3.7.1"

# Configure the number of retries attempted before failing call
session = requests.Session()

retries = Retry(total=5, backoff_factor=0.1)

session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))
