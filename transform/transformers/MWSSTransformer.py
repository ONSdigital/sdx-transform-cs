from collections import namedtuple
import datetime
import json
import logging
import os
import sys
import tempfile

import pkg_resources
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import A4

#from transform.transformers.ImageTransformer import ImageTransformer
#from transform.transformers.PDFTransformer import PDFTransformer

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
            " ".join((q, a)) for q, a in data.items()
        ]

    @staticmethod
    def idbr_receipt(surveyId, ruRef, ruChk, period, **kwargs):
        return "{ruRef}:{ruChk}:{surveyId:03}:{period}".format(
            surveyId=int(surveyId), ruRef=ruRef, ruChk=ruChk, period=period
        )

class MWSSTransformer:

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

    def __init__(self, response, log=None):
        self.response = response
        self.ids = Survey.identifiers(response)

        if log is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = self.bind_logger(log, self.ids)
        self.home = None

    @staticmethod
    def bind_logger(log, ids):
        return log.bind(
            ru_ref=ids.ruRef,
            tx_id=ids.txId,
            user_id=ids.userId,
        )

    def pack(self):
        survey = self.load_survey(self.ids)
        with tempfile.TemporaryDirectory(prefix="mwss_", dir="tmp") as self.home:
            fP = os.path.join(self.home, "pages.pdf")
            doc = SimpleDocTemplate(fP, pagesize=A4)
            doc.build(PDFTransformer.get_elements(survey, self.response))
            imgTfr = ImageTransformer(self.log, survey, self.response)
            images = list(imgTfr.create_image_sequence(fP))
            index = imgTfr.create_image_index(images)
            return imgTfr.create_zip(images, index)

def run():
    reply = json.load(sys.stdin)
    tfr = MWSSTransformer(reply)
    zipfile = tfr.pack()
    sys.stdout.write(zipfile)
    return 0

if __name__ == "__main__":
    run()
