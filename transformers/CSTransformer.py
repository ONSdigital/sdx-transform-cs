import zipfile
import os
from .ImageTransformer import ImageTransformer
from jinja2 import Environment, PackageLoader
from .pcktransformer import form_ids, derive_answers
import dateutil.parser

env = Environment(loader=PackageLoader('transform', 'templates'))


class CSTransformer(object):
    def __init__(self, survey, response_data, batch_number=False, sequence_no=1000):
        self.survey = survey
        self.response = response_data
        self.path = ""
        # A list of (dest, file) tuples
        self.files_to_archive = []
        self.batch_number = batch_number
        self.sequence_no = sequence_no

    def create_formats(self):
        itransformer = ImageTransformer(self.survey, self.response, self.sequence_no)

        itransformer.create_pdf()
        itransformer.create_image_sequence()
        itransformer.create_image_index()

        self.path = itransformer.path
        self.rootname = itransformer.rootname
        self.itransformer = itransformer

        self.create_pck()
        self.create_idbr()

    def prepare_archive(self):
        '''
        Prepare a list of files to save
        '''
        self.files_to_archive.append(("EDC_QData", self.pck_file))
        self.files_to_archive.append(("EDC_QReceipts", self.idbr_file))

        for image in self.itransformer.images:
            self.files_to_archive.append(("EDC_QImages/Images", image))

        self.files_to_archive.append(("EDC_QImages/Index", self.itransformer.index_file))

    def create_pck(self):
        template = env.get_template('pck.tmpl')

        instrument_id = self.response['collection']['instrument_id']

        submission_date = dateutil.parser.parse(self.response['submitted_at'])
        submission_date_str = submission_date.strftime("%d/%m/%y")

        cs_form_id = form_ids[instrument_id]

        data = self.response['data'] if 'data' in self.response else {}

        answers = derive_answers(self.survey, data)

        template_output = template.render(response=self.response, submission_date=submission_date_str,
                                          batch_number=self.batch_number, form_id=cs_form_id,
                                          answers=answers)

        self.pck_file = "%s_%04d" % (self.survey['survey_id'], self.sequence_no)

        with open(os.path.join(self.path, self.pck_file), "w") as fh:
            fh.write(template_output)

    def create_idbr(self):
        template = env.get_template('idbr.tmpl')
        template_output = template.render(response=self.response)
        submission_date = dateutil.parser.parse(self.response['submitted_at'])
        submission_date_str = submission_date.strftime("%d%m")

        # Format is RECddMM_batchId.DAT
        # e.g. REC1001_30000.DAT for 10th January, batch 30000
        self.idbr_file = "REC%s_%d.DAT" % (submission_date_str, self.sequence_no)

        with open(os.path.join(self.path, self.idbr_file), "w") as fh:
            fh.write(template_output)

    def create_zip(self):
        '''
        Create a zip from a renumbered sequence
        '''
        zippath = os.path.join(self.path, '%s.zip' % self.rootname)
        zipf = zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED)

        for dest, file in self.files_to_archive:
            zipf.write(os.path.join(self.path, file), arcname="%s/%s" % (dest, file))

        zipf.close()

        return os.path.join(self.path, '%s.zip' % self.rootname)

    def cleanup(self):
        self.itransformer.cleanup()

        os.remove(os.path.join(self.path, self.pck_file))
        os.remove(os.path.join(self.path, self.idbr_file))
