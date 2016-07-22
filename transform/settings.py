import logging
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)

LOGGING_FORMAT = "%(asctime)s|%(levelname)s: sdx-transform-cs: %(message)s"
LOGGING_LEVEL = logging.DEBUG

IMAGE_PATH = "\\\\NP3RVWAPXX370\SDX_preprod\EDC_QImages\Images"

# Configure the number of retries attempted before failing call
session = requests.Session()

retries = Retry(total=5, backoff_factor=0.1)

session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))
