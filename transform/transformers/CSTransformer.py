import dateutil.parser
from io import StringIO
import os.path
from jinja2 import Environment, PackageLoader
from .ImageTransformer import ImageTransformer
from .PCKTransformer import PCKTransformer

env = Environment(loader=PackageLoader('transform', 'templates'))


class CSTransformer(object):

    receipt_path = os.getenv("SDX_FTP_RECEIPT_PATH")
    data_path = os.getenv("SDX_FTP_DATA_PATH")
    image_path = os.getenv("SDX_FTP_IMAGE_PATH")

    def __init__(self, logger, survey, response_data, batch_number=False, sequence_no=1000):
        self._logger = logger
        self._survey = survey
        self._response = response_data
        self._batch_number = batch_number
        self._sequence_no = sequence_no
        self._idbr = StringIO()
        self._pck = StringIO()
        self.image_transformer = ImageTransformer(self._logger, self._survey, self._response,
                                                  sequence_no=self._sequence_no, base_image_path=self.image_path)
        self._setup_logger()

    def create_zip(self):
        """
        Create a in memory zip
        """
        # add pck , idbr then images and index
        pck_name = self._create_pck()
        idbr_name = self._create_idbr()
        self.image_transformer.zip.append(os.path.join(self.data_path, pck_name), self._pck.read())
        self.image_transformer.zip.append(os.path.join(self.receipt_path, idbr_name), self._idbr.read())

        self.image_transformer.get_zipped_images()
        self.image_transformer.zip.rewind()

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

        template_output = template.render(response=self._response, submission_date=sub_date_str,
                                          batch_number=self._batch_number, form_id=cs_form_id,
                                          answers=answers)
        self._pck.write(template_output)
        self._pck.seek(0)
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
