import datetime
import decimal
import json
import logging
import os
from decimal import ROUND_HALF_UP, Decimal

from structlog import wrap_logger

from transform.settings import (
    SDX_FTP_DATA_PATH,
    SDX_FTP_IMAGE_PATH,
    SDX_FTP_RECEIPT_PATH,
    SDX_RESPONSE_JSON_PATH,
)
from transform.transformers.cs_formatter import CSFormatter
from transform.transformers.survey import Survey
from transform.transformers.transformer import ImageTransformer

logger = wrap_logger(logging.getLogger(__name__))

# Set the rounding contect for Decimal objects to ROUND_HALF_UP
decimal.getcontext().rounding = ROUND_HALF_UP


class MBSTransformer():
    """Perform the transforms and formatting for the MBS survey."""

    @staticmethod
    def _merge_dicts(x, y):
        """Makes it possible to merge two dicts on Python 3.4."""
        z = x.copy()
        z.update(y)
        return z

    @staticmethod
    def round_mbs(value):
        """MBS rounding is done on a ROUND_HALF_UP basis and values are divided by 1000 for the pck"""
        try:
            return Decimal(round(Decimal(float(value))) / 1000).quantize(1)
        except TypeError:
            logger.info("Tried to quantize a NoneType object. Returning None")
            return None

    def __init__(self, response, seq_nr=0):

        self.idbr_ref = {"0106": "T106G", "0255": "MB65B", "0203": "MB03B"}

        self.response = response
        self.ids = self.get_identifiers(seq_nr=seq_nr)

        survey_file = "./transform/surveys/{}.{}.json".format(
            self.ids["survey_id"], self.ids["instrument_id"]
        )

        with open(survey_file) as fp:
            logger.info("Loading {}".format(survey_file))
            self.survey = json.load(fp)

        self.image_transformer = ImageTransformer(
            logger,
            self.survey,
            self.response,
            sequence_no=self.ids["seq_nr"],
            base_image_path=SDX_FTP_IMAGE_PATH,
        )

    def get_identifiers(self, batch_nr=0, seq_nr=0):
        """Parse common metadata from the survey.

        Return a named tuple which code can use to access the various ids and discriminators.

        :param dict data: A survey reply.
        :param int batch_nr: A batch number for the reply.
        :param int seq_nr: An image sequence number for the reply.

        """

        logger.info("Parsing data from submission")

        ru_ref = self.response.get("metadata", {}).get("ru_ref", "")
        ts = datetime.datetime.now(datetime.timezone.utc)
        ids = {
            "batch_nr": batch_nr,
            "seq_nr": seq_nr,
            "ts": ts,
            "tx_id": self.response.get("tx_id"),
            "survey_id": self.response.get("survey_id"),
            "instrument_id": self.response.get("collection", {}).get("instrument_id"),
            "submitted_at": Survey.parse_timestamp(
                self.response.get("submitted_at", ts.isoformat())
            ),
            "user_id": self.response.get("metadata", {}).get("user_id"),
            "ru_ref": "".join(i for i in ru_ref if i.isdigit()),
            "ru_check": ru_ref[-1] if ru_ref and ru_ref[-1].isalpha() else "",
            "period": self.response.get("collection", {}).get("period"),
        }

        if any(i is None for i in ids):
            logger.error("Missing an id from {0}".format(ids))
            return None

        else:
            return ids

    def transform(self):
        """Perform a transform on survey data."""
        employment_questions = ("51", "52", "53", "54")

        if self.response["data"].get("d50") == "Yes":
            logger.info("Setting default values to 0 for question codes 51:54")
            employee_totals = {q_id: 0 for q_id in employment_questions}
        else:
            logger.info("d50 not yes. No default values set for question codes 51:54.")
            employee_totals = {}
            for q_id in employment_questions:

                # QIDSs 51 - 54 aren't compulsory. If a value isn't present,
                # then it doesn't need to go in the PCK file.

                try:
                    employee_totals[q_id] = int(self.response["data"].get(q_id))
                except TypeError:
                    logger.exception(
                        "No answer supplied for {}. Skipping.".format(q_id)
                    )

        logger.info(
            "Transforming data for {}".format(self.ids["ru_ref"]),
            tx_id=self.ids["tx_id"],
        )

        transformed_data = {
            "146": True if self.response["data"].get("146") == "Yes" else False,
            "11": Survey.parse_timestamp(self.response["data"].get("11")),
            "12": Survey.parse_timestamp(self.response["data"].get("12")),
            "40": self.round_mbs(self.response["data"].get("40")),
            "49": self.round_mbs(self.response["data"].get("49")),
            "90": self.round_mbs(self.response["data"].get("90")),
            "50": self.response["data"].get("50"),
            "110": self.response["data"].get("110"),
        }

        return {
            k: v
            for k, v in self._merge_dicts(transformed_data, employee_totals).items()
            if v is not None
        }

    def create_zip(self, img_seq=None):
        """Perform transformation on the survey data
        and pack the output into a zip file exposed by the image transformer
        """

        logger.info("Creating PCK", ru_ref=self.ids["ru_ref"])

        pck_name = CSFormatter.pck_name(self.ids["survey_id"], self.ids["seq_nr"])
        transformed_data = self.transform()
        pck = CSFormatter.get_pck(
            transformed_data,
            self.idbr_ref[self.ids["instrument_id"]],
            self.ids["ru_ref"],
            self.ids["ru_check"],
            self.ids["period"],
        )

        logger.info("Creating IDBR receipt", ru_ref=self.ids["ru_ref"])

        idbr_name = CSFormatter.idbr_name(self.ids["submitted_at"], self.ids["seq_nr"])
        idbr = CSFormatter.get_idbr(
            self.ids["survey_id"],
            self.ids["ru_ref"],
            self.ids["ru_check"],
            self.ids["period"],
        )

        response_json_name = CSFormatter.response_json_name(
            self.ids["survey_id"], self.ids["seq_nr"]
        )

        self.image_transformer.zip.append(
            os.path.join(SDX_FTP_DATA_PATH, pck_name), pck
        )
        self.image_transformer.zip.append(
            os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr
        )

        self.image_transformer.get_zipped_images(img_seq)

        self.image_transformer.zip.append(
            os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name),
            json.dumps(self.response),
        )

    def get_zip(self):
        self.image_transformer.zip.rewind()
        return self.image_transformer.zip.in_memory_zip
