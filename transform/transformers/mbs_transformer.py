import datetime
import json
import os
from collections import namedtuple
from decimal import ROUND_HALF_UP, Decimal
import logging

from transform.settings import (
    SDX_FTP_DATA_PATH, SDX_FTP_IMAGE_PATH, SDX_FTP_RECEIPT_PATH, SDX_RESPONSE_JSON_PATH
)

from transform.transformers.survey import Survey
from transform.transformers.transformer import ImageTransformer
from transform.transformers.cs_formatter import CSFormatter


__doc__ = """Transform MBS survey data into formats required downstream."""

logger = logging.getLogger(__name__)


class MBSTransformer():
    """Perform the transforms and formatting for the MBS survey."""

    def __init__(self, response, seq_nr=0):

        self.response = response

        self.Identifiers = namedtuple(
            "Identifiers",
            [
                "batch_nr",
                "seq_nr",
                "ts",
                "tx_id",
                "survey_id",
                "inst_id",
                "user_ts",
                "user_id",
                "ru_ref",
                "ru_check",
                "period",
            ],
        )

        self.ids = self.get_identifiers(seq_nr=seq_nr)

        self.survey = "../surveys/{survey_id}.{instrument_id}.json".format(
            survey_id=self.Identifiers.survey_id, instrument_id=self.Identifiers.inst_id
        )
        self.image_transformer = ImageTransformer(
            logger,
            self.survey,
            self.response,
            sequence_no=self.ids.seq_nr,
            base_image_path=SDX_FTP_IMAGE_PATH,
        )

    def get_identifiers(self, batch_nr=0, seq_nr=0):
        """Parse common metadata from the survey.

        Return a named tuple which code can use to access the various ids and discriminators.

        :param dict data:   A survey reply.
        :param int batch_nr: A batch number for the reply.
        :param int seq_nr: An image sequence number for the reply.

        """
        ru_ref = self.response.get("metadata", {}).get("ru_ref", "")
        ts = datetime.datetime.now(datetime.timezone.utc)
        ids = self.Identifiers(
            batch_nr,
            seq_nr,
            ts,
            self.response.get("tx_id"),
            self.response.get("survey_id"),
            self.response.get("collection", {}).get("instrument_id"),
            Survey.parse_timestamp(self.response.get("submitted_at", ts.isoformat())),
            self.response.get("metadata", {}).get("user_id"),
            "".join(i for i in ru_ref if i.isdigit()),
            ru_ref[-1] if ru_ref and ru_ref[-1].isalpha() else "",
            self.response.get("collection", {}).get("period"),
        )

        if any(i is None for i in ids):
            logger.warning("Missing an id from {0}".format(ids))
            return None

        else:
            return ids

    def transform(self):
        """Perform a transform on survey data."""

        return {
            "146": 1 if self.response["data"].get("146a") == "Yes" else 2,
            "11": Survey.parse_timestamp(self.response["data"].get("11")),
            "12": Survey.parse_timestamp(self.response["data"].get("12")),
            "40": Decimal(self.response["data"].get("40")).quantize(Decimal(-3), rounding=ROUND_HALF_UP),
            "49": Decimal(self.response["data"].get("40")).quantize(Decimal(-3), rounding=ROUND_HALF_UP),
            "90": Decimal(self.response["data"].get("40")).quantize(Decimal(-3), rounding=ROUND_HALF_UP),
            "50": self.response["data"].get("50"),
            "51": self.response["data"].get("51"),
            "52": self.response["data"].get("52"),
            "53": self.response["data"].get("53"),
            "54": self.response["data"].get("54"),
        }

    def create_zip(self, img_seq=None):
        """Perform transformation on the survey data
        and pack the output into a zip file exposed by the image transformer

        """

        data = self.transform()

        id_dict = dict(self.ids)

        pck_name = CSFormatter.pck_name(id_dict["survey_id"], id_dict["seq_nr"])

        pck = CSFormatter.get_pck(
            data,
            id_dict["inst_id"],
            id_dict["ru_ref"],
            id_dict["ru_check"],
            id_dict["period"],
        )

        idbr_name = CSFormatter.idbr_name(id_dict["user_ts"], id_dict["seq_nr"])

        idbr = CSFormatter.get_idbr(
            id_dict["survey_id"],
            id_dict["ru_ref"],
            id_dict["ru_check"],
            id_dict["period"],
        )

        response_json_name = CSFormatter.response_json_name(
            id_dict["survey_id"], id_dict["seq_nr"]
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
