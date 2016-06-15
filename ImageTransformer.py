import os
import glob
import subprocess
import zipfile
import datetime
import dateutil.parser
import re
import settings
from jinja2 import Environment, PackageLoader
from PDFTransformer import PDFTransformer

env = Environment(loader=PackageLoader('transform', 'templates'))

def format_date(value, style='long'):
    """convert a datetime to a different format."""

    date_format = '%Y%m%d' if style == 'short' else '%d/%m/%Y %H:%M:%S'
    return value.strftime(date_format)

def statistical_unit_id_filter(value):
    if len(value) == 12:
        return value[0:-1]

def scan_id_filter(value):
    scanfile, _ = os.path.splitext(value)

    return scanfile

def page_filter(value):
    page = str(value).zfill(3) if value else ''

    return "%s,0" % page if value == 1 else page

def format_period(value):
    if not value:
        return ''

    if len(value) < 6:
        return value.zfill(6)
    elif len(value) == 4:
        return "20%s" % value
    elif len(value) > 6:
        return value[0:6]

env.filters['format_date'] = format_date
env.filters['statistical_unit_id'] = statistical_unit_id_filter
env.filters['scan_id'] = scan_id_filter
env.filters['format_page'] = page_filter
env.filters['format_period'] = format_period

class ImageTransformer(object):
    def __init__(self, survey, response_data):
        self.survey = survey
        self.response = response_data

        # We need to generate a pdf first
        pdf_transformer = PDFTransformer(self.survey, self.response)

        self.pdf_file = pdf_transformer.render_to_file()
        self.path, self.base_name = os.path.split(self.pdf_file)
        self.rootname, _ = os.path.splitext(self.base_name)

    def extract_pdf_images(self):
        '''
        Extract all pdf pages as jpegs
        '''
        subprocess.run(["pdftoppm", "-jpeg", self.pdf_file, self.rootname])
        
        self.images = glob.glob("%s-*.jpg" % self.rootname)

        return self.images

    def create_image_sequence(self, start=1):
        '''
        Renumber the image sequence extracted from pdf
        '''
        new_images = []
        index = start

        for file in self.extract_pdf_images():
            new_name = "S%s.jpg" % str(index).zfill(9)
            new_images.append(new_name)
            os.rename(file, new_name)
            index += 1

        self.images = new_images

        return self.images

    def create_image_index(self, sequence_no=1000):
        '''
        Takes a list of images and creates a index csv from them
        '''
        template = env.get_template('csv.tmpl')

        current_time = datetime.datetime.now()
        submission_date = dateutil.parser.parse(self.response['submitted_at'])
        submission_date_str = format_date(submission_date, 'short')

        template_output = template.render(IMAGE_PATH=settings.IMAGE_PATH, images=self.images, response=self.response, creation_time=current_time)

        index_file = "EDC_%s_%s_%04d.csv" %(self.survey['survey_id'], submission_date_str, sequence_no)

        with open(index_file, "w") as fh:
            fh.write(template_output)

        return template_output

    def create_image_zip(self):
        '''
        Create a zip from a renumbered sequence
        '''
        zipf = zipfile.ZipFile('%s.zip' % self.rootname, 'w', zipfile.ZIP_DEFLATED)

        for file in self.create_image_sequence():
            zipf.write(os.path.join(self.path, file))

        zipf.close()

        return '%s.zip' % self.rootname

    def cleanup(self):
        '''
        Remove all temporary files
        '''
        os.remove(os.path.join(self.path, self.pdf_file))

        for image in self.images:
            os.remove(os.path.join(self.path, image))
