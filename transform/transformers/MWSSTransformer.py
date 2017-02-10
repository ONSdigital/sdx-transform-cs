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
        "userId", "ruRef", "ruChk", "period"
    ])

    @staticmethod
    def identifiers(data, batchNr=0, seqNr=0, log=None):
        log = log or logging.getLogger(__name__)
        ruRef = data.get("metadata", {}).get("ru_ref", "")
        rv = Survey.Identifiers(
            batchNr, seqNr, datetime.date.today(),
            data.get("tx_id"),
            data.get("survey_id"),
            data.get("collection", {}).get("instrument_id"),
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


class CSFormatter:

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
    def pck_lines(data, batchNr, ts, surveyId, ruRef, ruChk, period, **kwargs):
        formId = CSFormatter.formIds[surveyId]
        return [
            CSFormatter.pck_batch_header(batchNr, ts),
            "FV",
            CSFormatter.pck_form_header(formId, ruRef, ruChk, period),
        ] + [
            "{0} {1:011}".format(q, a) for q, a in data.items()
        ]

    @staticmethod
    def idbr_receipt(surveyId, ruRef, ruChk, period, **kwargs):
        return "{ruRef}:{ruChk}:{surveyId:03}:{period}".format(
            surveyId=int(surveyId), ruRef=ruRef, ruChk=ruChk, period=period
        )


class MWSSTransformer:

    class Processor:
        """
        Processors return data of the same type as the supplied default.

        """

        @staticmethod
        def match_type(qId, data, default):
            return type(default)(data.get(qId, default))

        @staticmethod
        def unsigned_integer(qId, data, default):
            rv = int(data.get(qId, default))
            return rv if rv >= 0 else default

    defn = [
        (range(40, 90, 10), 0, Processor.unsigned_integer),
        (3, 0, Processor.match_type)
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

    @staticmethod
    def transform(data):
        ops = MWSSTransformer.ops

    @staticmethod
    def idbr_name(submittedAt, seqNr, **kwargs):
        subDT = datetime.datetime.strptime(submittedAt, "%Y-%m-%dT%H:%M:%SZ")
        return "REC{0}_{1:04}.DAT".format(subDT.strftime("%d%m"), int(seqNr))

    @staticmethod
    def pck_name(surveyId, seqNr, **kwargs):
        return "{0}_{1:04}".format(surveyId, int(seqNr))

    @staticmethod
    def write_idbr(fObj, **kwargs):
        output = CSFormatter.idbr_receipt(fObj, **kwargs)
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

    @property
    def ops(self):
        return OrderedDict([
            (qId, (dflt, fn))
            for rng, dflt, fn in self.defn
            for qId in (rng if isinstance(rng, range) else [rng])
        ])

    def pack(self):
        survey = self.load_survey(self.ids)
        manifest = []
        with tempfile.TemporaryDirectory(prefix="mwss_", dir="tmp") as locn:
            # Do transform and write PCK
            data = self.transform(self.response["data"])
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
