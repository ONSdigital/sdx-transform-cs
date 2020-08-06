import json
import logging
import os

from structlog import wrap_logger

from transform.settings import SDX_FTP_IMAGE_PATH, SDX_FTP_DATA_PATH, SDX_FTP_RECEIPT_PATH, SDX_RESPONSE_JSON_PATH
from transform.transformers import ImageTransformer
from transform.transformers.common_software import MBSTransformer, MWSSTransformer, CSTransformer
from transform.transformers.cora import UKISTransformer
from transform.transformers.cord import Ecommerce2019Transformer, EcommerceTransformer
from transform.transformers.survey import Survey
from transform.utilities.formatter import Formatter

logger = wrap_logger(logging.getLogger(__name__))


class Builder:

    def __init__(self, survey_response, sequence_no=0) -> None:
        self.survey_response = survey_response
        self.logger = logger
        self.sequence_no = sequence_no
        self.ids = Survey.identifiers(survey_response, seq_nr=sequence_no)
        pattern = "./transform/surveys/{survey_id}.{inst_id}.json"
        self.survey = Survey.load_survey(self.ids, pattern)
        self.image_transformer = ImageTransformer(self.logger, self.survey, self.survey_response,
                                                  sequence_no=self.sequence_no, base_image_path=SDX_FTP_IMAGE_PATH)
        self.transformer = self._select_transformer()

    def _select_transformer(self):
        survey_id = self.ids.survey_id

        # CORA
        if survey_id == "144":
            transformer = UKISTransformer(self.survey_response, self.sequence_no)

        # CORD
        elif survey_id == "187":
            if self.survey_response['collection']['instrument_id'] in ['0001', '0002']:
                transformer = Ecommerce2019Transformer(self.survey_response, self.sequence_no)
            else:
                transformer = EcommerceTransformer(self.survey_response, self.sequence_no)

        # COMMON SOFTWARE
        elif survey_id == "009":
            transformer = MBSTransformer(self.survey_response, self.sequence_no)
        elif survey_id == "134":
            transformer = MWSSTransformer(self.survey_response, self.sequence_no, log=self.logger)
        else:
            transformer = CSTransformer(self.logger, self.survey, self.survey_response, sequence_no=self.sequence_no)

        return transformer

    def create_zip(self, img_seq=None):

        pck_name, pck = self.transformer.create_pck()
        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)

        idbr_name, idbr = self.transformer.create_receipt()
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr)

        self.image_transformer.get_zipped_images(img_seq)

        response_json_name = Formatter.response_json_name(self.ids.survey_id, self.ids.seq_nr)
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
                                          json.dumps(self.survey_response))

    def get_zip(self):
        return self.image_transformer.get_zip()
