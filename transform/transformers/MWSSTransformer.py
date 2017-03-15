from decimal import Decimal, InvalidOperation
from collections import namedtuple
from collections import OrderedDict
import datetime
from functools import partial
from functools import reduce
import io
import itertools
import json
import logging
import operator
import os
import re
import sys
import tempfile
import zipfile

import pkg_resources
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import A4

from transform.transformers.ImageTransformer import ImageTransformer
from transform.transformers.PDFTransformer import PDFTransformer

__doc__ = """Transform MWSS survey data into formats required downstream.

The class API is used by the SDX transform service.
Additionally this module will run as a script from the command line:

python -m transform.transformers.MWSSTransformer \
< tests/replies/eq-mwss.json > test-output.zip

"""


class Survey:
    """Provide operations and accessors to survey data."""

    Identifiers = namedtuple("Identifiers", [
        "batch_nr", "seq_nr", "ts", "tx_id", "survey_id", "inst_id",
        "user_ts", "user_id", "ru_ref", "ru_check", "period"
    ])

    @staticmethod
    def load_survey(ids):
        """Find the survey definition by id."""
        try:
            content = pkg_resources.resource_string(
                __name__, "../surveys/{survey_id}.{inst_id}.json".format(**ids._asdict())
            )
        except FileNotFoundError:
            return None
        else:
            return json.loads(content.decode("utf-8"))

    @staticmethod
    def bind_logger(log, ids):
        """Bind a structured logger with survey metadata identifiers."""
        return log.bind(
            ru_ref=ids.ru_ref,
            tx_id=ids.tx_id,
            user_id=ids.user_id,
        )

    @staticmethod
    def parse_timestamp(text):
        """Parse a text field for a date or timestamp.

        Date and time formats vary across surveys.
        This method knows how to read them.

        """

        cls = datetime.datetime

        if text.endswith("Z"):
            return cls.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=datetime.timezone.utc
            )

        try:
            return cls.strptime(text, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            pass

        try:
            return cls.strptime(text.partition(".")[0], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass

        try:
            return cls.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            pass

        try:
            return cls.strptime(text, "%d/%m/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def identifiers(data, batch_nr=0, seq_nr=0, log=None):
        """Parse common metadata from the survey.

        Return a named tuple which code can use to access ids, etc.

        """
        log = log or logging.getLogger(__name__)
        ru_ref = data.get("metadata", {}).get("ru_ref", "")
        ts = datetime.datetime.now(datetime.timezone.utc)
        rv = Survey.Identifiers(
            batch_nr, seq_nr, ts,
            data.get("tx_id"),
            data.get("survey_id"),
            data.get("collection", {}).get("instrument_id"),
            Survey.parse_timestamp(data.get("submitted_at", ts.isoformat())),
            data.get("metadata", {}).get("user_id"),
            ''.join(i for i in ru_ref if i.isdigit()),
            ru_ref[-1] if ru_ref and ru_ref[-1].isalpha() else "",
            data.get("collection", {}).get("period")
        )
        if any(i is None for i in rv):
            log.warning("Missing an id from {0}".format(rv))
            return None
        else:
            return rv


class Processor:
    """Apply operations to data.

    These methods are used to perform business logic on survey data.
    They are mostly concerned with combining multiple fields into a
    single field for output.

    Principles for processor methods:

    * Method is responsible for range check according to own logic.
    * Parametrisation is possible; use functools.partial to bind arguments.
    * Return data of the same type as the supplied default.
    * On any error, return the default.

    """

    @staticmethod
    def aggregate(qid, data, default, *args, weights=[], **kwargs):
        """Calculate the weighted sum of a question group."""
        try:
            return type(default)(
                Decimal(data.get(qid, 0)) +
                sum(Decimal(scale) * Decimal(data.get(q, 0)) for q, scale in weights)
            )
        except (InvalidOperation, ValueError):
            return default

    @staticmethod
    def evaluate(qid, data, default, *args, group=[], convert=bool, op=operator.or_, **kwargs):
        """Perform a map/reduce evaluation of a question group."""
        try:
            group_vals = [data.get(qid, None)] + [data.get(q, None) for q in group]
            data = [convert(i) for i in group_vals if i is not None]
            return type(default)(reduce(op, data))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def mean(qid, data, default, *args, group=[], **kwargs):
        """Calculate the mean of all fields in a question group."""
        try:
            group_vals = [data.get(qid, None)] + [data.get(q, None) for q in group]
            data = [Decimal(i) for i in group_vals if i is not None]
            divisor = len(data) or 1
            rv = sum(data) / divisor
            return type(default)(rv)
        except (AttributeError, InvalidOperation, TypeError, ValueError):
            return default

    @staticmethod
    def events(qid, data, default, *args, group=[], **kwargs):
        """Return a sequence of time events from a question group."""
        try:
            group_vals = [data.get(qid, None)] + [data.get(q, None) for q in group]
            data = sorted(filter(
                None, (Survey.parse_timestamp(i) for i in group_vals if i is not None)
            ))
            if all(isinstance(i, type(default)) for i in data):
                return data
            else:
                return type(default)(data)
        except (AttributeError, TypeError, ValueError):
            return default

    @staticmethod
    def survey_string(qid, data, default, *args, survey=None, **kwargs):
        """Accept a string as an option for a question.

        This method provides an opportunity for validating the string against
        the survey definition, though this has not been a requirement so far.

        """
        try:
            return type(default)(data[qid])
        except (KeyError, ValueError):
            return default

    @staticmethod
    def unsigned_integer(qid, data, default, *args, **kwargs):
        """Process a string as an unsigned integer."""
        try:
            rv = int(data.get(qid, default))
        except ValueError:
            return default
        else:
            return type(default)(rv) if rv >= 0 else default

    @staticmethod
    def percentage(qid, data, default, *args, **kwargs):
        """Process a string as a percentage."""
        try:
            rv = int(data.get(qid, default))
        except ValueError:
            return default
        else:
            return type(default)(rv) if 0 <= rv <= 100 else default


class CSFormatter:
    """Formatter for common software systems.

    Serialises standard data types to PCK format.
    Creates a receipt in IDBR format.

    """

    form_ids = {
        "134": "0004",
    }

    @staticmethod
    def pck_name(survey_id, seq_nr, **kwargs):
        """Generate the name of a PCK file."""
        return "{0}_{1:04}".format(survey_id, int(seq_nr))

    @staticmethod
    def pck_batch_header(batch_nr, ts):
        """Generate a batch header for a PCK file."""
        return "{0}{1:06}{2}".format("FBFV", batch_nr, ts.strftime("%d/%m/%y"))

    @staticmethod
    def pck_form_header(form_id, ru_ref, ru_check, period):
        """Generate a form header for PCK data."""
        form_id = "{0:04}".format(form_id) if isinstance(form_id, int) else form_id
        return "{0}:{1}{2}:{3}".format(form_id, ru_ref, ru_check, period)

    @staticmethod
    def pck_value(qid, val, survey_id=None):
        """Format a value as PCK data."""
        if isinstance(val, list):
            val = bool(val)

        if isinstance(val, bool):
            return 1 if val else 2
        elif isinstance(val, str):
            return 1 if val else 0
        else:
            return val

    @staticmethod
    def pck_item(q, a):
        """Return a PCK line item."""
        try:
            return "{0:04} {1:011}".format(int(q), CSFormatter.pck_value(q, a))
        except TypeError:
            return "{0} ???????????".format(q)

    @staticmethod
    def pck_lines(data, batch_nr, ts, survey_id, inst_id, ru_ref, ru_check, period, **kwargs):
        """Return a list of lines in a PCK file."""
        return [
            "FV",
            CSFormatter.pck_form_header(inst_id, ru_ref, ru_check, period),
        ] + [
            CSFormatter.pck_item(q, a) for q, a in data.items()
        ]

    @staticmethod
    def write_pck(f_obj, data, **kwargs):
        """Write a PCK file."""
        output = CSFormatter.pck_lines(data, **kwargs)
        f_obj.write("\n".join(output))
        f_obj.write("\n")

    @staticmethod
    def idbr_name(user_ts, seq_nr, **kwargs):
        """Generate the name of an IDBR file."""
        return "REC{0}_{1:04}.DAT".format(user_ts.strftime("%d%m"), int(seq_nr))

    @staticmethod
    def idbr_receipt(survey_id, ru_ref, ru_check, period, **kwargs):
        """Format a receipt in IDBR format."""
        return "{ru_ref}:{ru_check}:{survey_id:03}:{period}".format(
            survey_id=int(survey_id), ru_ref=ru_ref, ru_check=ru_check, period=period
        )

    @staticmethod
    def write_idbr(f_obj, **kwargs):
        """Write an IDBR file."""
        output = CSFormatter.idbr_receipt(**kwargs)
        f_obj.write(output)
        f_obj.write("\n")


class MWSSTransformer:
    """Perform the transforms and formatting for the MWSS survey."""

    defn = [
        (40, 0, partial(Processor.aggregate, weights=[("40f", 1)])),
        (50, 0, partial(Processor.aggregate, weights=[("50f", 0.5)])),
        (60, 0, partial(Processor.aggregate, weights=[("60f", 0.5)])),
        (70, 0, partial(Processor.aggregate, weights=[("70f", 0.5)])),
        (80, 0, partial(Processor.aggregate, weights=[("80f", 0.5)])),
        (90, False, partial(
            Processor.evaluate,
            group=[
                "90w", "91w", "92w", "93w", "94w", "95w", "96w", "97w",
                "90f", "91f", "92f", "93f", "94f", "95f", "96f", "97f",
            ],
            convert=re.compile("^((?!No).)+$").search, op=lambda x, y: x or y)),
        (100, False, partial(Processor.mean, group=["100f"])),
        (110, [], partial(Processor.events, group=["110f"])),
        (120, False, partial(Processor.mean, group=["120f"])),
        (range(130, 133, 1), False, Processor.survey_string),
        (140, 0, partial(
            Processor.aggregate,
            weights=[
                ("140m", 1), ("140w4", 1), ("140w5", 1)
            ])),
        (range(151, 154, 1), 0, Processor.unsigned_integer),
        (range(171, 174, 1), 0, Processor.unsigned_integer),
        (range(181, 184, 1), 0, Processor.unsigned_integer),
        (190, False, partial(
            Processor.evaluate,
            group=[
                "190w4", "191w4", "192w4", "193w4", "194w4", "195w4", "196w4", "197w4",
                "190m", "191m", "192m", "193m", "194m", "195m", "196m", "197m",
                "190w5", "191w5", "192w5", "193w5", "194w5", "195w5", "196w5", "197w5",
            ],
            convert=re.compile("^((?!No).)+$").search, op=lambda x, y: x or y)),
        (200, False, partial(Processor.mean, group=["200w4", "200w5"])),
        (210, [], partial(Processor.events, group=["210w4", "210w5"])),
        (220, False, partial(Processor.mean, group=["220w4", "220w5"])),
        (300, False, partial(
            Processor.evaluate,
            group=[
                "300w", "300f", "300m", "300w4", "300w5",
            ],
            convert=str, op=lambda x, y: x + "\n" + y)),
    ]

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

    @staticmethod
    def transform(data, survey=None):
        """Perform a transform on survey data."""
        return OrderedDict(
            (qid, fn(qid, data, dflt, survey))
            for qid, (dflt, fn) in MWSSTransformer.ops().items()
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
            self.log = logging.getLogger(__name__)
        else:
            self.log = Survey.bind_logger(log, self.ids)

    def pack(self, img_seq=None):
        """Perform transformation on the survey data and pack the output into a zip file.

        Return the contents of the zip as bytes.
        The object maintains a temporary directory while the output is generated.

        """
        survey = Survey.load_survey(self.ids)
        manifest = []
        with tempfile.TemporaryDirectory(prefix="mwss_", dir="tmp") as locn:
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
            doc.build(PDFTransformer.get_elements(survey, self.response))

            # Create page images from PDF
            img_tfr = ImageTransformer(self.log, survey, self.response)
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


def run():
    reply = json.load(sys.stdin)
    tfr = MWSSTransformer(reply)
    zipfile = tfr.pack(img_seq=itertools.count())
    sys.stdout.buffer.write(zipfile.read())

if __name__ == "__main__":
    run()
