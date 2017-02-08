from collections import namedtuple
import datetime
import logging
import tempfile


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
        "008": "MS31B",
        "017": "STW01",
        "050": "0008",
        "134": "0004",
        "141": "HE2015",
        "0102": "RSI5B",  # TODO: Check which mapping
    }

    @staticmethod
    def batch_header(batchNr, ts):
        return "{0}{1:06}{2}".format("FBFV", batchNr, ts.strftime("%d/%m/%y"))

    @staticmethod
    def form_header(formId, ruRef, ruChk, period):
        formId = "{0:04}".format(formId) if isinstance(formId, int) else formId
        return "{0}:{1}{2}:{3}".format(formId, ruRef, ruChk, period)

    @staticmethod
    def pck_lines(data, batchNr, ts, instId, ruRef, ruChk, period, **kwargs):
        formId = CSFormatter.formIds[instId]
        return [
            CSFormatter.batch_header(batchNr, ts),
            "FV",
            CSFormatter.form_header(formId, ruRef, ruChk, period),
        ] + [
            " ".join((q, a)) for q, a in data.items()
        ]


class MWSSTransformer:

    def __init__(self, survey, log=None):
        self.ids = Survey.identifiers(survey)
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
        with tempfile.TemporaryDirectory(prefix="mwss_", dir="tmp") as self.home:
            print(self.home)
