import datetime
import re
import subprocess
from io import BytesIO
import dateutil.parser
from transform import settings
from transform.transformers.InMemoryZip import InMemoryZip
from transform.transformers.ImageTransformerBase import ImageTransformerBase
from transform.transformers.ImageTransformer import ImageTransformer
from transform.views.image_filters import get_env, format_date
from .PDFTransformer import PDFTransformer


class InMemoryImageTransformer(ImageTransformer):
    """Transforms a survey and response into a zip file
    useage:

    transformer = InMemoryImageTransformer(survey_json, response_json)
    zip = transformer.get_zip(number_sequence_iterator)
    return send_file(zip.in_memory_zip,attachment_filename='image.zip',mimetype='application/zip')

    Note: Inherits from Image transformer only to get access to existing code to call out to get
    image sequence numbers . There is a case to refactor ImageTransformer to get a common base class
    """

    def __init__(self, logger, survey, response, current_time=datetime.datetime.utcnow(), sequence_no=1000):
        self._page_count = -1
        self._current_time = current_time
        self._index = None
        self._pdf = None
        self._image_names = []
        self.zip = InMemoryZip()
        super().__init__(logger, survey, response, sequence_no)

    def get_zip(self, num_sequence=None):
        self._create_pdf(self.survey, self.response)
        self._build_image_names(num_sequence, self._page_count)
        self._create_index()
        self._build_zip()
        return self.zip

    @staticmethod
    def get_image_name(i):
        return "S{0:09}.JPG".format(i)

    def _create_pdf(self, survey, response):
        """Create a pdf which will be used as the basis for images """
        pdf_transformer = PDFTransformer(survey, response)
        self._pdf, self._page_count = pdf_transformer.render_pages()
        return self._pdf

    def _build_image_names(self, num_sequence, image_count):
        if num_sequence is None:
            for image_sequence in self.get_image_sequence_list(image_count):
                self._image_names.append(InMemoryImageTransformer.get_image_name(image_sequence))
        else:
            for _ in range(0, image_count):
                name = InMemoryImageTransformer.get_image_name(next(num_sequence))
                self._image_names.append(name)

    def _create_index(self):
        """Create the in memory index"""

        self._index = InMemoryIndex(self.logger, self.response, self._page_count, self._image_names,
                                    self._current_time, self.sequence_no)

    def _build_zip(self):
        i = 0
        for image in self._extract_pdf_images(self._pdf):
            self.zip.append(self._image_names[i], image)
            i += 1
        self.zip.append(self._index.index_name, self._index.index.getvalue())
        self.zip.rewind()

    @staticmethod
    def _extract_pdf_images(pdf_stream):
        """
        Extract pdf pages as mpps labelled as jpegs
        ppm format consists of a header followed by image bytes . In this feed we may have multiple
        images in one stream . These appear without a delimiter between images. So the only delimiter we
        have is the header .
        The header is of the format P6\n<width>space<height>\n<maximum pixel count>
        We need to cope with 0 , 1 or many images in a stream .
        Note- the ppm format leads to large amounts of data as its bitmapped . 11 pages may be 13KB
        in the input pdf stream , but that can lead to 72.8MB in memory (6.5MB per page !) .
        Hence memory may become an issue.
        """

        process = subprocess.Popen(executable="pdftoppm",
                                   args=["-jpeg"],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        result, errors = process.communicate(pdf_stream)

        if errors:
            raise IOError("IMAGES:Could not extract Images from pdf: {0}".format(repr(errors)))

        header_regex = re.compile(b'P6\n[0-9 ]+[0-9]+\n[0-9]+\n')

        start_pos = 0
        while start_pos < len(result):
            header = header_regex.match(result[start_pos:start_pos+25])  # Header length is less than 25
            ppm_header = PpmHeader(header.group(0))
            end_pos = start_pos + ppm_header.size

            yield result[start_pos:end_pos]

            start_pos = end_pos


class PpmHeader(object):
    """Takes a byte array that contains a ppm format header and extract file info """
    def __init__(self, source):
        self.source = source.split()
        self.type = self.source[0]
        if self.type != b'P6':  # 'P6' is the identifier for PPM file types
            raise TypeError("IMAGES: Non ppm file type detected")
        self.width = int(self.source[1])
        self.height = int(self.source[2])
        self.size = len(source) + (3*self.height*self.width)   # 3 bytes per pixel (rgb)


class InMemoryIndex:
    """Class for creating in memory index object using StringIO."""
    def __init__(self, logger, response_data, image_count, image_names,
                 current_time=datetime.datetime.utcnow(), sequence_no=1000):
        self.index = BytesIO()
        self.logger = logger
        self._response = response_data
        self._image_count = image_count
        self._creation_time = {
            'short': format_date(current_time, 'short'),
            'long': format_date(current_time)
        }
        self.index_name = self._get_index_name(self._response, sequence_no)

        self._build_index(image_names)

    def rewind(self):
        """Rewinds the read-write position of the in-memory index to the start."""
        self.index.seek(0)

    def _build_index(self, image_names):
        """Builds the index file contents into self.index"""
        env = get_env()
        template = env.get_template('csv.tmpl')

        image_path = settings.FTP_PATH + settings.SDX_FTP_IMAGE_PATH + "\\Images"
        template_output = template.render(
            SDX_FTP_IMAGES_PATH=image_path,
            images=image_names,
            response=self._response,
            creation_time=self._creation_time
        )

        msg = "Adding image to index"
        [self.logger.info(msg, file=image_name) for image_name in image_names]
        self.index.write(template_output.encode())
        self.rewind()

    @staticmethod
    def _get_index_name(response, sequence_no):
        submission_date = dateutil.parser.parse(response['submitted_at'])
        submission_date_str = format_date(submission_date, 'short')
        return "EDC_{}_{}_{:04d}.csv".format(response['survey_id'], submission_date_str, sequence_no)
