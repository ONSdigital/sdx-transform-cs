import json
from io import StringIO

import dateutil.parser
from jinja2 import Environment, PackageLoader

from transform.settings import SDX_FTP_IMAGE_PATH
from transform.transformers import ImageTransformer
from transform.transformers.common_software.pck_transformer import PCKTransformer
from transform.transformers.transformer import Transformer

env = Environment(loader=PackageLoader('transform', 'templates'))


class CSTransformer(Transformer):

    def __init__(self, logger, survey, response_data, batch_number=False, sequence_no=1000):
        self._logger = logger
        self._survey = survey
        self._response = response_data
        self._batch_number = batch_number
        self._sequence_no = sequence_no
        self._idbr = StringIO()
        self._pck = StringIO()
        self._response_json = StringIO()
        self.image_transformer = ImageTransformer(self._logger, self._survey, self._response,
                                                  sequence_no=self._sequence_no, base_image_path=SDX_FTP_IMAGE_PATH)
        self._setup_logger()

    def _setup_logger(self):
        if self._survey:
            if 'metadata' in self._survey:
                metadata = self._survey['metadata']
                self._logger = self._logger.bind(user_id=metadata['user_id'], ru_ref=metadata['ru_ref'])

            if 'tx_id' in self._survey:
                self.tx_id = self._survey['tx_id']
                self._logger = self._logger.bind(tx_id=self.tx_id)

    def _create_pck(self):
        template = env.get_template('pck.tmpl')
        pck_transformer = PCKTransformer(self._survey, self._response)
        answers = pck_transformer.derive_answers()
        cs_form_id = pck_transformer.get_cs_form_id()
        sub_date_str = pck_transformer.get_subdate_str()

        template_output = template.render(response=self._response,
                                          submission_date=sub_date_str,
                                          batch_number=self._batch_number,
                                          form_id=cs_form_id,
                                          answers=answers)
        self._pck.write(template_output)
        self._pck.seek(0)

        # Vacancy surveys have a requirement to go to common software as survey_id 181.
        # We only change the filename as the survey_id isn't included in the content of
        # the pck file.
        vacancies_surveys = ["182", "183", "184", "185"]
        if self._survey['survey_id'] in vacancies_surveys:
            pck_name = "%s_%04d" % ('181', self._sequence_no)
        else:
            pck_name = "%s_%04d" % (self._survey['survey_id'], self._sequence_no)

        return pck_name

    def _create_idbr(self):
        template = env.get_template('idbr.tmpl')
        template_output = template.render(response=self._response)
        submission_date = dateutil.parser.parse(self._response['submitted_at'])
        submission_date_str = submission_date.strftime("%d%m")

        # Format is RECddMM_batchId.DAT
        # e.g. REC1001_30000.DAT for 10th January, batch 30000
        idbr_name = "REC%s_%04d.DAT" % (submission_date_str, self._sequence_no)
        self._idbr.write(template_output)
        self._idbr.seek(0)
        return idbr_name

    def _create_response_json(self):
        original_json_name = "%s_%04d.json" % (self._survey['survey_id'], self._sequence_no)
        self._response_json.write(json.dumps(self._response))
        self._response_json.seek(0)
        return original_json_name

    def create_pck(self):
        pck_name = self._create_pck()
        pck = self._pck.read()
        return pck_name, pck

    def create_receipt(self):
        idbr_name = self._create_idbr()
        idbr = self._idbr.read()
        return idbr_name, idbr
