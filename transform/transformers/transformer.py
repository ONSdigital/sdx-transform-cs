import logging
import json
import os.path

from collections import OrderedDict
from structlog import wrap_logger

from transform.settings import SDX_FTP_DATA_PATH, SDX_FTP_IMAGE_PATH, SDX_FTP_RECEIPT_PATH, SDX_RESPONSE_JSON_PATH
from transform.transformers.cs_formatter import CSFormatter
from transform.transformers.image_transformer import ImageTransformer
from transform.transformers.survey import Survey


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

    receipt_path = os.getenv("SDX_FTP_RECEIPT_PATH", "EDC_QReceipts")
    data_path = os.getenv("SDX_FTP_DATA_PATH", "EDC_QData")

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

        # Enforce that child classes have defn and pattern attributes
        for attr in ("defn", "pattern"):
            if not hasattr(self.__class__, attr):
                raise UserWarning("Missing class attribute: {0}".format(attr))

        self.survey = Survey.load_survey(self.ids, self.pattern)
        self.image_transformer = ImageTransformer(self.log, self.survey, self.response,
                                                  sequence_no=self.ids.seq_nr, base_image_path=SDX_FTP_IMAGE_PATH)

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

    def create_zip(self, img_seq=None):
        """Perform transformation on the survey data
        and pack the output into a zip file exposed by the image transformer
        """

        data = self.transform(self.response["data"], self.survey)

        id_dict = self.ids._asdict()

        pck_name = CSFormatter.pck_name(id_dict["survey_id"], id_dict["seq_nr"])

        pck = CSFormatter.get_pck(data, id_dict["inst_id"], id_dict["ru_ref"], id_dict["ru_check"], id_dict["period"])

        idbr_name = CSFormatter.idbr_name(id_dict["user_ts"], id_dict["seq_nr"])

        idbr = CSFormatter.get_idbr(id_dict["survey_id"], id_dict["ru_ref"], id_dict["ru_check"], id_dict["period"])

        response_json_name = CSFormatter.response_json_name(id_dict["survey_id"], id_dict["seq_nr"])

        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr)

        self.image_transformer.get_zipped_images(img_seq)

        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
                                          json.dumps(self.response))

    def get_zip(self):
        self.image_transformer.zip.rewind()
        return self.image_transformer.zip.in_memory_zip
