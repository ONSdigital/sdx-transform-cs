#!/usr/bin/env python
#   coding: UTF-8

import argparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.exceptions import MaxRetryError
from requests.packages.urllib3.util.retry import Retry

from transform import settings

# Configure the number of retries attempted before failing call
session = requests.Session()

retries = Retry(total=5, backoff_factor=0.1)

session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))


class ImageTransformerBase(object):

    def __init__(self, logger, survey, response_data, sequence_no):
        self.logger = logger
        self.survey = survey
        self.response = response_data
        self.sequence_no = sequence_no

    def response_ok(self, res):

        if res.status_code == 200:
            self.logger.info("Returned from sdx-sequence",
                             request_url=res.url, status=res.status_code)
            return True
        else:
            self.logger.error("Returned from sdx-sequence",
                              request_url=res.url, status=res.status_code)
            return False

    def remote_call(self, request_url, json=None):
        try:
            self.logger.info("Calling sdx-sequence", request_url=request_url)

            r = None

            if json:
                r = session.post(request_url, json=json)
            else:
                r = session.get(request_url)

            return r
        except MaxRetryError:
            self.logger.error("Max retries exceeded (5)", request_url=request_url)

    def get_image_sequence_list(self, n):
        sequence_url = "{0}/image-sequence?n={1}".format(settings.SDX_SEQUENCE_URL, n)

        r = self.remote_call(sequence_url)

        if not self.response_ok(r):
            return False

        result = r.json()
        return result['sequence_list']


def parser(description=__doc__):
    rv = argparse.ArgumentParser(
        description,
    )
    rv.add_argument(
        "--survey", required=True,
        help="Set a path to the survey JSON file.")
    return rv


