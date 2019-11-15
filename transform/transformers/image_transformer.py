import datetime
import os.path
import requests
import subprocess

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.exceptions import MaxRetryError
from requests.packages.urllib3.util.retry import Retry

from transform import settings
from transform.transformers.in_memory_zip import InMemoryZip
from transform.transformers.index_file import IndexFile
from .pdf_transformer import PDFTransformer

# Configure the number of retries attempted before failing call
session = requests.Session()

retries = Retry(total=5, backoff_factor=0.1)

session.mount('http://', HTTPAdapter(max_retries=retries))
session.mount('https://', HTTPAdapter(max_retries=retries))


class ImageTransformer:
    """Transforms a survey and _response into a zip file
    """

    def __init__(self, logger, survey, response, current_time=None, sequence_no=1000,
                 base_image_path=""):

        if current_time is None:
            current_time = datetime.datetime.utcnow()

        self._page_count = -1
        self.current_time = current_time
        self.index_file = None
        self._pdf = None
        self._image_names = []
        self.zip = InMemoryZip()
        self.logger = logger
        self.survey = survey
        self.response = response
        self.sequence_no = sequence_no
        self.image_path = "" if base_image_path == "" else os.path.join(base_image_path, "Images")
        self.index_path = "" if base_image_path == "" else os.path.join(base_image_path, "Index")

    def get_zipped_images(self, num_sequence=None):
        """Builds the images and the index_file file into the zip file.
        It appends data to the zip , so any data in the zip
        prior to this executing is not deleted.
        """
        self._create_pdf(self.survey, self.response)
        self._build_image_names(num_sequence, self._page_count)
        self._create_index()
        self._build_zip()
        return self.zip

    def get_zip(self):
        """Get access to the in memory zip """
        self.zip.rewind()
        return self.zip.in_memory_zip

    @staticmethod
    def _get_image_name(i):
        return "S{0:09}.JPG".format(i)

    def _create_pdf(self, survey, response):
        """Create a pdf which will be used as the basis for images """
        pdf_transformer = PDFTransformer(survey, response)
        self._pdf, self._page_count = pdf_transformer.render_pages()
        return self._pdf

    def _build_image_names(self, num_sequence, image_count):
        """Build a collection of image names to use later"""
        if num_sequence is None:
            for image_sequence in self._get_image_sequence_list(image_count):
                self._image_names.append(ImageTransformer._get_image_name(image_sequence))
        else:
            for _ in range(0, image_count):
                name = ImageTransformer._get_image_name(next(num_sequence))
                self._image_names.append(name)

    def _create_index(self):
        self.index_file = IndexFile(self.logger, self.response, self._page_count, self._image_names,
                                    self.current_time, self.sequence_no)

    def _build_zip(self):
        i = 0
        for image in self._extract_pdf_images(self._pdf):
            self.zip.append(os.path.join(self.image_path, self._image_names[i]), image)
            i += 1
        self.zip.append(os.path.join(self.index_path, self.index_file.index_name), self.index_file.in_memory_index.getvalue())
        self.zip.rewind()

    @staticmethod
    def _extract_pdf_images(pdf_stream):
        """
        Extract pdf pages as jpegs
        """

        process = subprocess.Popen(["pdftoppm", "-jpeg"],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        result, errors = process.communicate(pdf_stream)

        if errors:
            raise IOError("images:Could not extract Images from pdf: {0}".format(repr(errors)))

        # FFD9 is an end of image marker in jpeg images
        for image in result.split(b'\xFF\xD9'):
            if len(image) > 11:  # we can get an end of file marker after the image and a jpeg header is 11 bytes long
                yield image

    def _response_ok(self, res):
        if res.status_code == 200:
            self.logger.info("Returned from sdx-sequence", request_url=res.url, status=res.status_code)
            return True
        else:
            self.logger.error("Returned from sdx-sequence", request_url=res.url, status=res.status_code)
            return False

    def _remote_call(self, request_url, json=None):
        try:
            self.logger.info("Calling sdx-sequence", request_url=request_url)
            if json:
                return session.post(request_url, json=json)

            return session.get(request_url)

        except MaxRetryError:
            self.logger.error("Max retries exceeded (5)", request_url=request_url)

    def _get_image_sequence_list(self, n):
        sequence_url = f"{settings.SDX_SEQUENCE_URL}/image-sequence?n={n}"

        r = self._remote_call(sequence_url)

        if not self._response_ok(r):
            return False

        result = r.json()
        return result['sequence_list']
