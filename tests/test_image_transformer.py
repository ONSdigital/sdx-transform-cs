import itertools
import datetime
import json
import logging
import os.path
import time
import tempfile
import unittest
from structlog import wrap_logger

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from transform.transformers.ImageTransformer import ImageTransformer
from transform.transformers.PDFTransformer import PDFTransformer

log = wrap_logger(logging.getLogger(__name__))


class ImageTransformTests(unittest.TestCase):

    def setUp(self):
        self.max_diff, self.maxDiff = self.maxDiff, None

    def tearDown(self):
        self.maxDiff = self.max_diff

    def test_image_index_date(self):

        with open("./tests/csv/valid.023.0205.json") as fb:
            data = fb.read()
        reply = json.loads(data)

        with open("./transform/surveys/023.0205.json") as fb:
            survey_data = fb.read()
        survey = json.loads(survey_data)

        with tempfile.TemporaryDirectory(prefix="sdx_") as location:
            # Build PDF
            fp = os.path.join(location, "pages.pdf")
            doc = SimpleDocTemplate(fp, pagesize=A4)
            pdf_transformer = PDFTransformer(survey, reply)
            doc.build(pdf_transformer.get_elements())

            # Create page images from PDF
            img_tfr = ImageTransformer(log, survey, reply)
            images = list(img_tfr.create_image_sequence(fp, nmbr_seq=itertools.count()))

            image_transformer = ImageTransformer(log, survey, reply)

            # create the index file and capture creation date
            with open(image_transformer.create_image_index(images), "r") as fh:
                csv = fh.read()
                date1 = csv.split(',')[0]

            time.sleep(1)

            # create the index file again and make sure the date is different
            with open(image_transformer.create_image_index(images), "r") as fh:
                csv = fh.read()
                date2 = csv.split(',')[0]

            self.assertNotEqual(date1, date2, "Image index dates should not be equal")

    def test_mwss_index(self):

        with open("./tests/data/eq-mwss.json") as fb:
            data = fb.read()
        reply = json.loads(data)

        with open("./tests/data/134.0005.json") as fb:
            survey_data = fb.read()
        survey = json.loads(survey_data)

        with open("./tests/data/EDC_134_20170301_1000.csv") as fb:
            check = fb.read()

        with tempfile.TemporaryDirectory(prefix="sdx_") as locn:

            # Build PDF
            fp = os.path.join(locn, "pages.pdf")
            doc = SimpleDocTemplate(fp, pagesize=A4)
            pdf_transformer = PDFTransformer(survey, reply)
            doc.build(pdf_transformer.get_elements())

            # Create page images from PDF
            img_tfr = ImageTransformer(log, survey, reply)
            images = list(img_tfr.create_image_sequence(fp, nmbr_seq=itertools.count()))

            with open(img_tfr.create_image_index(images, current_time=datetime.datetime(2017, 3, 7, 9, 45, 4)), "r") as fh:
                csv = fh.read()

            self.assertEqual(check.splitlines(), csv.splitlines())
