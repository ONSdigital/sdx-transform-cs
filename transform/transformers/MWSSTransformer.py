from collections import namedtuple
from collections import OrderedDict
import datetime
import io
import json
import logging
import os
import sys
import tempfile
import zipfile

import pkg_resources
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import A4

try:
    from transform.transformers.ImageTransformer import ImageTransformer
    from transform.transformers.PDFTransformer import PDFTransformer
except ImportError:
    # CLI operation
    from ImageTransformer import ImageTransformer
    from PDFTransformer import PDFTransformer


class Survey:

    Identifiers = namedtuple("Identifiers", [
        "batchNr", "seqNr", "ts", "txId", "surveyId", "instId",
        "userTs", "userId", "ruRef", "ruChk", "period"
    ])

    @staticmethod
    def parse_timestamp(text):
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
    def identifiers(data, batchNr=0, seqNr=0, log=None):
        """
        Parse common metadata from the survey. Return a
        defined type which all code can use to access
        ids.

        """
        log = log or logging.getLogger(__name__)
        ruRef = data.get("metadata", {}).get("ru_ref", "")
        ts = datetime.datetime.now(datetime.timezone.utc)
        rv = Survey.Identifiers(
            batchNr, seqNr, ts,
            data.get("tx_id"),
            data.get("survey_id"),
            data.get("collection", {}).get("instrument_id"),
            Survey.parse_timestamp(data.get("submitted_at", ts.isoformat())),
            data.get("metadata", {}).get("user_id"),
            ''.join(i for i in ruRef if i.isdigit()),
            ruRef[-1] if ruRef and ruRef[-1].isalpha() else "",
            data.get("collection", {}).get("period")
        )
        if any(i is None for i in rv):
            log.warning("Missing an id from {0}".format(rv))
            return None
        else:
            return rv


class Processor:
    """
    Principles for processors:

    * method is responsible for range check according to own logic.
    * parametrisation is possible; use functools.partial
    * returns data of the same type as the supplied default. 

    """

    @staticmethod
    def comment(qId, data, default, *args, **kwargs):
        try:
            return type(default)(data.get(qId, default))
        except ValueError:
            return default

    @staticmethod
    def diarydate(qId, data, default, *args, **kwargs):
        try:
            rv = Survey.parse_timestamp(data[qId])
            if isinstance(rv, datetime.datetime):
                return rv.date()
            else:
                return rv
        except KeyError:
            return default

    @staticmethod
    def match_type(qId, data, default, *args, **kwargs):
        try:
            return type(default)(data.get(qId, default))
        except ValueError:
            return default

    @staticmethod
    def single(qId, data, default, *args, survey=None, **kwargs):
        if survey is not None:
            # TODO: Look up valid option
            pass
        try:
            return type(default)(data.get(qId, default))
        except ValueError:
            return default

    @staticmethod
    def multiple(qId, data, default, *args, survey=None, **kwargs):
        if survey is not None:
            # TODO: Look up valid options
            pass
        try:
            return type(default)(data.get(qId, default))
        except ValueError:
            return default

    @staticmethod
    def unsigned_integer(qId, data, default, *args, **kwargs):
        rv = int(data.get(qId, default))
        return rv if rv >= 0 else default

    @staticmethod
    def percentage(qId, data, default, *args, **kwargs):
        typ = type(default)
        rv = int(data.get(qId, default))
        return typ(rv) if 0 <= rv >= 100 else default


class CSFormatter:
    """
    Formatter for common software systems.

    Serialises standard data types to PCK format.

    """

    formIds = {
        "134": "0004",
    }

    @staticmethod
    def pck_batch_header(batchNr, ts):
        return "{0}{1:06}{2}".format("FBFV", batchNr, ts.strftime("%d/%m/%y"))

    @staticmethod
    def pck_form_header(formId, ruRef, ruChk, period):
        formId = "{0:04}".format(formId) if isinstance(formId, int) else formId
        return "{0}:{1}{2}:{3}".format(formId, ruRef, ruChk, period)

    @staticmethod
    def pck_value(qNr, val, surveyId=None):
        if isinstance(val, bool):
            return 1 if val else 2
        elif isinstance(val, str):
            return 1 if val else 0
        else:
            return val

    @staticmethod
    def pck_item(q, a):
        return "{0} {1:011}".format(q, CSFormatter.pck_value(q, a))

    @staticmethod
    def pck_lines(data, batchNr, ts, surveyId, ruRef, ruChk, period, **kwargs):
        formId = CSFormatter.formIds[surveyId]
        return [
            CSFormatter.pck_batch_header(batchNr, ts),
            "FV",
            CSFormatter.pck_form_header(formId, ruRef, ruChk, period),
        ] + [
            CSFormatter.pck_item(q, a) for q, a in data.items()
        ]

    @staticmethod
    def idbr_receipt(surveyId, ruRef, ruChk, period, **kwargs):
        return "{ruRef}:{ruChk}:{surveyId:03}:{period}".format(
            surveyId=int(surveyId), ruRef=ruRef, ruChk=ruChk, period=period
        )


class MWSSTransformer:

    defn = [
        (range(40, 90, 10), 0, Processor.unsigned_integer),
        (90, False, Processor.multiple),
        (100, False, Processor.percentage),
        (110, False, Processor.diarydate),
        (120, False, Processor.percentage),
        (range(130, 133, 1), False, Processor.single),
        (140, 0, Processor.unsigned_integer),
        # 150; how generated?
        (range(151, 154, 1), 0, Processor.unsigned_integer),
        # 170; how generated?
        (range(171, 174, 1), 0, Processor.unsigned_integer),
        # 180; how generated?
        (range(181, 184, 1), 0, Processor.unsigned_integer),
        (190, False, Processor.multiple),
        (200, False, Processor.percentage),
        (210, False, Processor.diarydate),
        (220, False, Processor.percentage),
        (300, False, Processor.comment),
    ]

    @staticmethod
    def load_survey(ids):
        try:
            content = pkg_resources.resource_string(
                __name__, "../surveys/{surveyId}.{instId}.json".format(**ids._asdict())
            )
        except FileNotFoundError:
            return None
        else:
            return json.loads(content.decode("utf-8"))

    @staticmethod
    def bind_logger(log, ids):
        return log.bind(
            ru_ref=ids.ruRef,
            tx_id=ids.txId,
            user_id=ids.userId,
        )

    @classmethod
    def ops(cls):
        """
        A mapping from question id to default value and operator.

        """
        return OrderedDict([
            ("{0:04}".format(qNr), (dflt, fn))
            for rng, dflt, fn in cls.defn
            for qNr in (rng if isinstance(rng, range) else [rng])
        ])

    @staticmethod
    def transform(data, survey=None):
        """
        Normalise the document so that it contains all items required by downstream
        systems. Validate those items and apply business logic.

        """
        return OrderedDict(
            (qId, fn(qId, data, dflt, survey))
            for qId, (dflt, fn) in MWSSTransformer.ops().items()
        )

    @staticmethod
    def idbr_name(userTs, seqNr, **kwargs):
        return "REC{0}_{1:04}.DAT".format(userTs.strftime("%d%m"), int(seqNr))

    @staticmethod
    def pck_name(surveyId, seqNr, **kwargs):
        return "{0}_{1:04}".format(surveyId, int(seqNr))

    @staticmethod
    def write_idbr(fObj, **kwargs):
        output = CSFormatter.idbr_receipt(**kwargs)
        fObj.write(output)
        fObj.write("\n")

    @staticmethod
    def write_pck(fObj, data, **kwargs):
        output = CSFormatter.pck_lines(data, **kwargs)
        fObj.write("\n".join(output))
        fObj.write("\n")

    @staticmethod
    def create_zip(locn, manifest):
        zipBytes = io.BytesIO()

        with zipfile.ZipFile(zipBytes, "w", zipfile.ZIP_DEFLATED) as zipObj:
            for dst, fN in manifest:
                zipObj.write(os.path.join(locn, fN), arcname=os.path.join(dst, fN))

        zipBytes.seek(0)
        return zipBytes

    def __init__(self, response, log=None):
        self.response = response
        self.ids = Survey.identifiers(response)

        if self.ids is None:
            raise UserWarning("Missing identifiers")

        if log is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = self.bind_logger(log, self.ids)

    def pack(self):
        survey = self.load_survey(self.ids)
        manifest = []
        with tempfile.TemporaryDirectory(prefix="mwss_", dir="tmp") as locn:
            # Do transform and write PCK
            data = self.transform(self.response["data"], survey)
            fN = self.pck_name(**self.ids._asdict())
            with open(os.path.join(locn, fN), "w") as pck:
                self.write_pck(pck, data, **self.ids._asdict())
            manifest.append(("EDC_QData", fN))

            # Create IDBR file
            fN = self.idbr_name(**self.ids._asdict())
            with open(os.path.join(locn, fN), "w") as idbr:
                self.write_idbr(idbr, **self.ids._asdict())
            manifest.append(("EDC_QReceipts", fN))

            # Build PDF
            fP = os.path.join(locn, "pages.pdf")
            doc = SimpleDocTemplate(fP, pagesize=A4)
            doc.build(PDFTransformer.get_elements(survey, self.response))

            # Create page images from PDF
            imgTfr = ImageTransformer(self.log, survey, self.response)
            images = imgTfr.create_image_sequence(fP)
            for img in images:
                fN = os.path.basename(img)
                manifest.append(("EDC_QImages/Images", fN))

            # Write image index
            index = imgTfr.create_image_index(images)
            if index is not None:
                fN = os.path.basename(self.index)
                manifest.append(("EDC_QImages/Index", fN))

            return self.create_zip(locn, manifest)


def run():
    reply = json.load(sys.stdin)
    tfr = MWSSTransformer(reply)
    zipfile = tfr.pack()
    sys.stdout.write(zipfile)
    return 0

if __name__ == "__main__":
    run()
