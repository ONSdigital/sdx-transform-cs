import zipfile
import os
from io import BytesIO
from .ImageTransformer import ImageTransformer
from .PCKTransformer import PCKTransformer
from jinja2 import Environment, PackageLoader
import dateutil.parser
import shutil

env = Environment(loader=PackageLoader('transform', 'templates'))


class CSTransformer(object):
    def __init__(self, logger, survey, response_data, batch_number=False, sequence_no=1000):
        self.logger = logger
        self.survey = survey
        self.response = response_data
        self.path = ""
        # A list of (dest, file) tuples
        self.files_to_archive = []
        self.batch_number = batch_number
        self.sequence_no = sequence_no

    def create_formats(self):
        itransformer = ImageTransformer(self.logger, self.survey, self.response, sequence_no=self.sequence_no)

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

        pck_transformer = PCKTransformer(self.survey, self.response)
        answers = pck_transformer.derive_answers()
        cs_form_id = pck_transformer.get_cs_form_id()
        sub_date_str = pck_transformer.get_subdate_str()

        template_output = template.render(response=self.response, submission_date=sub_date_str,
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
        self.idbr_file = "REC%s_%04d.DAT" % (submission_date_str, self.sequence_no)

        with open(os.path.join(self.path, self.idbr_file), "w") as fh:
            fh.write(template_output)

    def create_zip(self):
        '''
        Create a in memory zip from a renumbered sequence
        '''
        in_memory_zip = BytesIO()

        with zipfile.ZipFile(in_memory_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for dest, file in self.files_to_archive:
                zipf.write(os.path.join(self.path, file), arcname="%s/%s" % (dest, file))

        # Return to beginning of file
        in_memory_zip.seek(0)

        return in_memory_zip

    def cleanup(self):
        shutil.rmtree(os.path.join(self.path))
