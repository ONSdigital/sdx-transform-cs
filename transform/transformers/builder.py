import json
import os

from transform.settings import SDX_FTP_IMAGE_PATH, SDX_FTP_DATA_PATH, SDX_FTP_RECEIPT_PATH, SDX_RESPONSE_JSON_PATH
from transform.transformers import ImageTransformer
from transform.transformers.survey import Survey
from transform.transformers.transformer import Transformer
from transform.utilities.formatter import Formatter


class Builder:

    def __init__(self, survey_response, logger, sequence_no) -> None:
        self.survey_response = survey_response
        self._logger = logger
        self.ids = Survey.identifiers(survey_response, seq_nr=sequence_no)
        pattern = "./transform/surveys/{survey_id}.{inst_id}.json"
        survey = Survey.load_survey(self.ids, pattern)
        self.image_transformer = ImageTransformer(self._logger, survey, self.survey_response,
                                                  sequence_no=sequence_no, base_image_path=SDX_FTP_IMAGE_PATH)
        self.transformer = Transformer()

    def create_zip(self, img_seq=None):

        pck_name, pck = self.transformer.create_pck()
        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)

        idbr_name, idbr = self.transformer.create_receipt()
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr)

        self.image_transformer.get_zipped_images(img_seq)

        response_json_name = Formatter.response_json_name(self.ids["survey_id"], self.ids["seq_nr"])
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
                                          json.dumps(self.response))

    '''
        #mbs
        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr)
        self.image_transformer.get_zipped_images(img_seq)
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
                                          json.dumps(self.response))


        mws
        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr)
        self.image_transformer.get_zipped_images(img_seq)
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
                                          json.dumps(self.response))


        ukis
        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr)
        self.create_image_files(img_seq)
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
                                          json.dumps(self.response))

        ecom
        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr)
        self.create_image_files(img_seq)
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
                                          json.dumps(self.response))

        cs
        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), self._pck.read())
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), self._idbr.read())
        self.image_transformer.get_zipped_images()
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_io_name),
                                          self._response_json.read())
        self.image_transformer.zip.rewind()
    '''

    def get_zip(self):
        return self.image_transformer.get_zip()
