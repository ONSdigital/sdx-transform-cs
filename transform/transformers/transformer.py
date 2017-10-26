import io
import logging
import os
import tempfile
import zipfile
from collections import OrderedDict

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate
from transform.transformers.cs_formatter import CSFormatter
from transform.transformers.survey import Survey
from transform.transformers.ImageTransformer import ImageTransformer
from transform.transformers.PDFTransformer import PDFTransformer
from structlog import wrap_logger


class Transformer:

    """A base class for SDX transformers.

    Subclasses should define the contents of the following class variables:

        * :py:const:`defn`
        * :py:const:`package`
        * :py:const:`pattern`

    """
    #: Transformer subclasses declare their transforms in this class variable.
    #: Each element is a 3-tuple consisting of:
    #:
    #: #. An integer or range corresponding to one or more question ids.
    #: #. A default value for the question(s).
    #: #. A :ref:`Processing function <processors>`.
    #:
    #: Eg, to declare question ids 151, 152, 153 as unsigned integers with a default
    #: of 0::
    #:
    #:  defn = [
    #:   (range(151, 154, 1), 0, Processor.unsigned_integer),
    #:
    #:  ]
    #:
    defn = []

    #: Defines a search pattern for survey definitions based on identifiers.
    #: The path is relative to the location specified by :py:const:`package` above.
    pattern = "../surveys/{survey_id}.{inst_id}.json"

    @classmethod
    def ops(cls):
        """Publish the sequence of operations for the transform.

        Return an ordered mapping from question id to default value and processing function.

        """
        return OrderedDict([
            ("{0:02}".format(qNr), (dflt, fn))
            for rng, dflt, fn in cls.defn
            for qNr in (rng if isinstance(rng, range) else [rng])
        ])

    @classmethod
    def transform(cls, data, survey=None):
        """Perform a transform on survey data."""
        return OrderedDict(
            (qid, fn(qid, data, dflt, survey))
            for qid, (dflt, fn) in cls.ops().items()
        )

    @staticmethod
    def create_zip(locn, manifest):
        """Create a zip archive from a local directory and a manifest list.

        Return the contents of the zip as bytes.

        """
        zip_bytes = io.BytesIO()

        with zipfile.ZipFile(zip_bytes, "w", zipfile.ZIP_DEFLATED) as zip_obj:
            for dst, f_name in manifest:
                zip_obj.write(os.path.join(locn, f_name), arcname=os.path.join(dst, f_name))

        zip_bytes.seek(0)
        return zip_bytes

    def __init__(self, response, seq_nr=0, log=None):
        """Create a transformer object to process a survey response."""
        self.response = response
        self.ids = Survey.identifiers(response, seq_nr=seq_nr)

        if self.ids is None:
            raise UserWarning("Missing identifiers")

        if log is None:
            self.log = wrap_logger(logging.getLogger(__name__))
        else:
            self.log = Survey.bind_logger(log, self.ids)

        for attr in ("defn", "pattern"):
            if not hasattr(self.__class__, attr):
                raise UserWarning("Missing class attribute: {0}".format(attr))

    def pack(self, img_seq=None, tmp="tmp"):
        """Perform transformation on the survey data and pack the output into a zip file.

        Return the contents of the zip as bytes.
        The object maintains a temporary directory while the output is generated.

        """
        survey = Survey.load_survey(self.ids, self.pattern)
        manifest = []
        with tempfile.TemporaryDirectory(prefix="sdx_", dir=tmp) as locn:
            # Do transform and write PCK
            data = self.transform(self.response["data"], survey)
            f_name = CSFormatter.pck_name(**self.ids._asdict())
            with open(os.path.join(locn, f_name), "w") as pck:
                CSFormatter.write_pck(pck, data, **self.ids._asdict())
            manifest.append(("EDC_QData", f_name))

            # Create IDBR file
            f_name = CSFormatter.idbr_name(**self.ids._asdict())
            with open(os.path.join(locn, f_name), "w") as idbr:
                CSFormatter.write_idbr(idbr, **self.ids._asdict())
            manifest.append(("EDC_QReceipts", f_name))

            # Build PDF
            fp = os.path.join(locn, "pages.pdf")
            doc = SimpleDocTemplate(fp, pagesize=A4)
            pdf_transformer = PDFTransformer(survey, self.response)
            doc.build(pdf_transformer.get_elements())

            # Create page images from PDF
            img_tfr = ImageTransformer(
                self.log, survey, self.response, self.ids.seq_nr
            )
            images = list(img_tfr.create_image_sequence(fp, nmbr_seq=img_seq))
            for img in images:
                f_name = os.path.basename(img)
                manifest.append(("EDC_QImages/Images", f_name))

            # Write image index
            index = img_tfr.create_image_index(images)
            if index is not None:
                f_name = os.path.basename(index)
                manifest.append(("EDC_QImages/Index", f_name))

            return self.create_zip(locn, manifest)
