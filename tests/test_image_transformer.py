import datetime
import itertools
import json
import logging
import unittest
from structlog import wrap_logger
from transform.transformers.ImageTransformer import ImageTransformer


class ImageTransformTests(unittest.TestCase):

    # repeat the same test as the in file based image transformer
    def test_mwss_index(self):
        log = wrap_logger(logging.getLogger(__name__))

        with open("./tests/data/eq-mwss.json") as fb:
            data = fb.read()
        reply = json.loads(data)

        with open("./tests/data/134.0005.json") as fb:
            survey_data = fb.read()
        survey = json.loads(survey_data)

        with open("./tests/data/EDC_134_20170301_1000.csv", "rb") as fb:
            check = fb.read()

        # Create page images from PDF
        img_tfr = ImageTransformer(log, survey, reply, current_time=datetime.datetime(2017, 3, 7, 9, 45, 4))

        img_tfr.get_zipped_images(itertools.count())

        with img_tfr.index.in_memory_index as f:
            csv = f.read()

        self.assertEqual(check.splitlines(), csv.splitlines())
