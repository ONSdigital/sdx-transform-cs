import json
import logging
import os

from structlog import wrap_logger

from transform.settings import SDX_FTP_IMAGE_PATH, SDX_FTP_DATA_PATH, SDX_FTP_RECEIPT_PATH, SDX_RESPONSE_JSON_PATH
from transform.transformers import ImageTransformer
from transform.transformers.survey import Survey
from transform.utilities.formatter import Formatter

logger = wrap_logger(logging.getLogger(__name__))


class Transformer:

    def __init__(self, response, sequence_no):
        self.response = response
        self.sequence_no = sequence_no
        self.logger = logger
        self.ids = Survey.identifiers(response, seq_nr=sequence_no)
        self.survey = Survey.load_survey(self.ids)
        self.image_transformer = ImageTransformer(self.logger, self.survey, self.response,
                                                  sequence_no=self.sequence_no, base_image_path=SDX_FTP_IMAGE_PATH)

    def create_pck(self):
        pass

    def create_receipt(self):
        pass

    def create_images(self, img_seq=None):
        self.image_transformer.get_zipped_images(img_seq)

    def get_zip(self, img_seq=None):

        pck_name, pck = self.create_pck()
        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)

        idbr_name, idbr = self.create_receipt()
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr)

        self.create_images(img_seq)

        response_json_name = Formatter.response_json_name(self.ids.survey_id, self.ids.seq_nr)
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
                                          json.dumps(self.response))

        return self.image_transformer.get_zip()
