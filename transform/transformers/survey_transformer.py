import json
import logging
import os

from structlog import wrap_logger

from transform.settings import SDX_FTP_IMAGE_PATH, SDX_FTP_DATA_PATH, SDX_FTP_RECEIPT_PATH, SDX_RESPONSE_JSON_PATH
from transform.transformers import ImageTransformer
from transform.transformers.survey import Survey
from transform.utilities.formatter import Formatter

logger = wrap_logger(logging.getLogger(__name__))


class SurveyTransformer:
    """Superclass for specific survey transformers.

    Common functionality for transformer classes.
    Subclasses must provide their own implementations for create_pck() and create_receipt().

    """

    def __init__(self, response, sequence_no):
        self.response = response
        self.sequence_no = sequence_no
        self.logger = logger
        self.ids = Survey.identifiers(response, seq_nr=sequence_no)
        self.survey = Survey.load_survey(self.ids)
        self.image_transformer = ImageTransformer(self.logger, self.survey, self.response,
                                                  sequence_no=self.sequence_no, base_image_path=SDX_FTP_IMAGE_PATH)

    def create_pck(self):
        """
        Returns a tuple containing the pck name, and the pck itself as string.
        """
        pck_name = ""
        pck = None
        return pck_name, pck

    def create_receipt(self):
        """
        Returns a tuple containing the pck name, and the pck itself as string.
        """
        receipt_name = ""
        receipt = None
        return receipt_name, receipt

    def create_images(self, img_seq=None):
        """
        Create the image files within the zip.
        """
        self.image_transformer.get_zipped_images(img_seq)

    def get_zip(self, img_seq=None):

        pck_name, pck = self.create_pck()
        if pck is not None:
            self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)

        receipt_name, receipt = self.create_receipt()
        if receipt is not None:
            self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, receipt_name), receipt)

        self.create_images(img_seq)

        response_json_name = Formatter.response_json_name(self.ids.survey_id, self.ids.seq_nr)
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
                                          json.dumps(self.response))

        return self.image_transformer.get_zip()
