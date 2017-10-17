import itertools
import datetime
import json
import logging
import os.path
import tempfile
import unittest
from structlog import wrap_logger

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from transform.transformers.ImageTransformer import ImageTransformer
from transform.transformers.PDFTransformer import PDFTransformer


class ImageTransformTests(unittest.TestCase):

    def setUp(self):
        self.max_diff, self.maxDiff = self.maxDiff, None

    def tearDown(self):
        self.maxDiff = self.max_diff

    def test_mwss_index(self):
        log = wrap_logger(logging.getLogger(__name__))

        with open("tests/data/eq-mwss.json", "r") as fb:
            data = fb.read()
        reply = json.loads(data)

        with open("tests/data/134.0005.json", "r") as fb:
            survey_data = fb.read()
        survey = json.loads(survey_data)

        with open("tests/data/EDC_134_20170301_1000.csv", "r") as fb:
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
