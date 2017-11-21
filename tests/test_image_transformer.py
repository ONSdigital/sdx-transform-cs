import datetime
import itertools
import json
import logging
import time
import unittest
from structlog import wrap_logger
from transform.transformers.image_transformer import ImageTransformer


class ImageTransformTests(unittest.TestCase):

    def setUp(self):
        with open("./tests/data/eq-mwss.json") as fb:
            data = fb.read()
        self.reply = json.loads(data)

        with open("./tests/data/134.0005.json") as fb:
            survey_data = fb.read()
        self.survey = json.loads(survey_data)

        with open("./tests/data/EDC_134_20170301_1000.csv", "rb") as fb:
            self.check = fb.read()
        self.log = wrap_logger(logging.getLogger(__name__))

    def test_image_index(self):

        # Create page images from PDF
        img_tfr = ImageTransformer(self.log, self.survey, self.reply, current_time=datetime.datetime(2017, 3, 7, 9, 45, 4))

        img_tfr.get_zipped_images(itertools.count())

        with img_tfr.index_file.in_memory_index as f:
            csv = f.read()

        self.assertEqual(self.check.splitlines(), csv.splitlines())

    def test_current_time_not_set_at_initialisation(self):

        img_tfr1 = ImageTransformer(self.log, self.survey, self.reply)
        time.sleep(0.01)
        img_tfr2 = ImageTransformer(self.log, self.survey, self.reply)

        self.assertNotEqual(img_tfr1.current_time, img_tfr2.current_time)
