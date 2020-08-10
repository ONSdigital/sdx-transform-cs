import datetime
import decimal
import logging
from decimal import ROUND_HALF_UP, Decimal

from structlog import wrap_logger

from transform.transformers.common_software.cs_formatter import CSFormatter
from transform.transformers.survey import Survey
from transform.transformers.transformer import Transformer

logger = wrap_logger(logging.getLogger(__name__))


class MBSTransformer(Transformer):
    """Perform the transforms and formatting for the MBS survey."""

    @staticmethod
    def round_mbs(value):
        """MBS rounding is done on a ROUND_HALF_UP basis and values are divided by 1000 for the pck"""
        try:
            # Set the rounding context for Decimal objects to ROUND_HALF_UP
            decimal.getcontext().rounding = ROUND_HALF_UP
            return Decimal(round(Decimal(float(value))) / 1000).quantize(1)

        except TypeError:
            logger.info("Tried to quantize a NoneType object. Returning None")
            return None

    @staticmethod
    def convert_str_to_int(value):
        """Convert submitted data to int in the transform"""
        try:
            return int(value)
        except TypeError:
            logger.info("Tried to transform None to int. Returning None.")
            return None

    @staticmethod
    def parse_timestamp(text):
        """Parse a text field for a date or timestamp.

        Date and time formats vary across surveys.
        This method reads those formats.

        :param str text: The date or timestamp value.
        :rtype: Python date or datetime.

        """

        cls = datetime.datetime

        if text:
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
                pass

            if len(text) != 6:
                return None

            try:
                return cls.strptime(text + "01", "%Y%m%d").date()

            except ValueError:
                return None

    def __init__(self, response, seq_nr=0):

        super().__init__(response, seq_nr)

        self.employment_questions = ("51", "52", "53", "54")
        self.turnover_questions = ("49",)

        self.idbr_ref = {
            "0106": "T106G",
            "0111": "T111G",
            "0161": "T161G",
            "0117": "T117G",
            "0123": "T123G",
            "0158": "T158G",
            "0167": "T167G",
            "0173": "T173G",
            "0201": "MB01B",
            "0202": "MB01B",
            "0203": "MB03B",
            "0204": "MB03B",
            "0205": "MB15B",
            "0216": "MB15B",
            "0251": "MB51B",
            "0253": "MB53B",
            "0255": "MB65B",
            "0817": "T817G",
            "0823": "T823G",
            "0867": "T867G",
            "0873": "T873G",
        }

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

        for key, value in ids.items():
            if value is None:
                logger.error(f"Missing value for: {key}")
                return None

        return ids

    def check_employee_totals(self):
        """Populate qcode 51:54 based on d50"""
        if self.response["data"].get("d50") == "Yes":
            logger.info("Setting default values to 0 for question codes 51:54")
            return {q_id: 0 for q_id in self.employment_questions}

        else:
            logger.info("d50 not yes. No default values set for question codes 51:54.")
            employee_totals = {}

            for q_id in self.employment_questions:
                # QIDSs 51 - 54 aren't compulsory. If a value isn't present,
                # then it doesn't need to go in the PCK file.
                try:
                    employee_totals[q_id] = self.convert_str_to_int(
                        self.response["data"].get(q_id)
                    )
                except TypeError:
                    logger.info(f"No answer supplied for {q_id}. Skipping.")

            return employee_totals

    def check_turnover_totals(self):
        """Populate qcode 49 based on d49"""
        if self.response["data"].get("d49") == "Yes":
            logger.info("Setting default value to 0 for question code 49")
            return {q_id: 0 for q_id in self.turnover_questions}

        else:
            logger.info("d49 not yes. No default values set for question code 49.")
            turnover_totals = {}

            for q_id in self.turnover_questions:
                try:
                    turnover_totals[q_id] = self.round_mbs(
                        self.response["data"].get(q_id)
                    )
                except TypeError:
                    logger.info(f"No answer supplied for {q_id}. Skipping.")

            return turnover_totals

    def survey_dates(self):
        """If questions 11 or 12 don't appear in the survey data, then populate
        them with the period start and end date found in the metadata
        """
        try:
            start_date = MBSTransformer.parse_timestamp(self.response["data"]["11"])
        except KeyError:
            logger.info("Populating start date using metadata")
            start_date = MBSTransformer.parse_timestamp(
                self.response.get("metadata", {})["ref_period_start_date"]
            )

        try:
            end_date = MBSTransformer.parse_timestamp(self.response["data"]["12"])
        except KeyError:
            logger.info("Populating end date using metadata")
            end_date = MBSTransformer.parse_timestamp(
                self.response.get("metadata", {})["ref_period_end_date"]
            )

        return {"11": start_date, "12": end_date}

    def _transform(self):
        """Perform a transform on survey data."""
        employee_totals = self.check_employee_totals()
        turnover_totals = self.check_turnover_totals()
        dates = self.survey_dates()

        logger.info(
            "Transforming data for {}".format(self.ids.ru_ref),
            tx_id=self.ids.tx_id
        )

        transformed_data = {
            "146": True if self.response["data"].get("146") == "Yes" else False,
            "40": self.round_mbs(self.response["data"].get("40")),
            "42": self.round_mbs(self.response["data"].get("42")),
            "43": self.round_mbs(self.response["data"].get("43")),
            "46": self.round_mbs(self.response["data"].get("46")),
            "47": self.round_mbs(self.response["data"].get("47")),
            "90": self.round_mbs(self.response["data"].get("90")),
            "50": MBSTransformer.convert_str_to_int(self.response["data"].get("50")),
            "110": MBSTransformer.convert_str_to_int(self.response["data"].get("110")),
        }

        return {
            k: v
            for k, v in {**transformed_data, **employee_totals, **turnover_totals, **dates}.items()
            if v is not None
        }

    def create_pck(self, img_seq=None):
        logger.info("Creating PCK", ru_ref=self.ids["ru_ref"])
        pck_name = CSFormatter.pck_name(self.ids["survey_id"], self.ids["seq_nr"])
        transformed_data = self._transform()
        pck = CSFormatter.get_pck(
            transformed_data,
            self.idbr_ref[self.ids["instrument_id"]],
            self.ids["ru_ref"],
            self.ids["ru_check"],
            self.ids["period"],
        )

        return pck_name, pck

    def create_receipt(self):
        logger.info("Creating IDBR receipt", ru_ref=self.ids["ru_ref"])
        idbr_name = CSFormatter.idbr_name(self.ids["submitted_at"], self.ids["seq_nr"])
        idbr = CSFormatter.get_idbr(
            self.ids["survey_id"],
            self.ids["ru_ref"],
            self.ids["ru_check"],
            self.ids["period"],
        )

        return idbr_name, idbr
