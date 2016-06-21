import os
import glob
import subprocess
import zipfile
import datetime
import dateutil.parser
import settings
from .PDFTransformer import PDFTransformer
from image_filters import get_env, format_date


class ImageTransformer(object):
    def __init__(self, survey, response_data, sequence_no=1000):
        self.survey = survey
        self.response = response_data
        self.sequence_no = sequence_no

    def create_pdf(self):
        '''
        Create a pdf which will be used as the basis for images
        '''
        pdf_transformer = PDFTransformer(self.survey, self.response)

        self.pdf_file = pdf_transformer.render_to_file()
        self.path, self.base_name = os.path.split(self.pdf_file)
        self.rootname, _ = os.path.splitext(self.base_name)

    def extract_pdf_images(self):
        '''
        Extract all pdf pages as jpegs
        '''
        subprocess.run(["pdftoppm", "-jpeg", self.base_name, self.rootname], cwd=self.path)
        self.images = glob.glob("%s/%s-*.jpg" % (self.path, self.rootname))

        return self.images

    def create_image_sequence(self, start=1):
        '''
        Renumber the image sequence extracted from pdf
        '''
        new_images = []
        index = start

        for file in self.extract_pdf_images():
            new_name = "S%05d%04d.jpg" % (self.sequence_no, index)
            new_images.append(new_name)
            os.rename(os.path.join(self.path, file), os.path.join(self.path, new_name))
            index += 1

        self.images = new_images

        return self.images

    def create_image_index(self):
        '''
        Takes a list of images and creates a index csv from them
        '''
        env = get_env()
        template = env.get_template('csv.tmpl')

        current_time = datetime.datetime.now()
        submission_date = dateutil.parser.parse(self.response['submitted_at'])
        submission_date_str = format_date(submission_date, 'short')

        template_output = template.render(IMAGE_PATH=settings.IMAGE_PATH, images=self.images, response=self.response, creation_time=current_time)

        self.index_file = "EDC_%s_%s_%04d.csv" % (self.survey['survey_id'], submission_date_str, self.sequence_no)

        with open(os.path.join(self.path, self.index_file), "w") as fh:
            fh.write(template_output)

    def create_zip(self):
        '''
        Create a zip from a renumbered sequence
        '''
        zippath = os.path.join(self.path, '%s.zip' % self.rootname)
        zipf = zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED)

        for file in self.images:
            zipf.write(os.path.join(self.path, file), arcname=file)

        if self.index_file:
            zipf.write(os.path.join(self.path, self.index_file), arcname=self.index_file)

        zipf.close()

        return os.path.join(self.path, '%s.zip' % self.rootname)

    def cleanup(self):
        '''
        Remove all temporary files
        '''
        os.remove(os.path.join(self.path, self.pdf_file))

        for image in self.images:
            os.remove(os.path.join(self.path, image))

        if self.index_file:
            os.remove(os.path.join(self.path, self.index_file))