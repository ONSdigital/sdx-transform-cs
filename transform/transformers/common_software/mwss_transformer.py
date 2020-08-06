from collections import OrderedDict
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from functools import partial
import logging

import itertools
import re
from structlog import wrap_logger

from transform.transformers.common_software.cs_formatter import CSFormatter
from transform.transformers.image_transformer import ImageTransformer
from transform.transformers.processor import Processor
from transform.transformers.survey import Survey
from transform.settings import SDX_FTP_IMAGE_PATH

__doc__ = """Transform MWSS survey data into formats required downstream.

The class API is used by the SDX transform service.
"""

from transform.transformers.transformer import Transformer


class MWSSTransformer(Transformer):
    """Perform the transforms and formatting for the MWSS survey.

    Weights = A sequence of 2-tuples giving the weight value for each question in the group.
    The weight of a question is dependant on the type so 40f is a fortnightly question
    so it will have a different weighting when it's transformed.

    Group = A sequence of question ids.

    """

    defn = [
        (40, 0, partial(Processor.aggregate, weights=[("40f", 1)])),
        (50, 0, partial(Processor.aggregate, weights=[("50f", 0.5)],
                        precision='1.',
                        rounding_direction=ROUND_HALF_UP)),
        (60, 0, partial(Processor.aggregate, weights=[("60f", 0.5)],
                        precision='1.',
                        rounding_direction=ROUND_HALF_UP)),
        (70, 0, partial(Processor.aggregate, weights=[("70f", 0.5)],
                        precision='1.',
                        rounding_direction=ROUND_HALF_UP)),
        (80, 0, partial(Processor.aggregate, weights=[("80f", 0.5)],
                        precision='1.',
                        rounding_direction=ROUND_HALF_UP)),
        (90, False, partial(
            Processor.evaluate,
            group=[
                "90w", "90f",
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
        (range(151, 154, 1), 0, partial(Processor.unsigned_integer,
                                        precision='1.',
                                        rounding_direction=ROUND_HALF_UP)),
        (range(171, 174, 1), 0, partial(Processor.unsigned_integer,
                                        precision='1.',
                                        rounding_direction=ROUND_HALF_UP)),
        (range(181, 184, 1), 0, partial(Processor.unsigned_integer,
                                        precision='1.',
                                        rounding_direction=ROUND_HALF_UP)),
        (190, False, partial(
            Processor.evaluate,
            group=[
                "190w4", "190m", "190w5",
            ],
            convert=re.compile("^((?!No).)+$").search, op=lambda x, y: x or y)),
        (200, False, partial(Processor.boolean, group=["200w4", "200w5"])),
        (210, [], partial(Processor.events, group=["210w4", "210w5"])),
        (220, False, partial(Processor.mean, group=["220w4", "220w5"])),
        (300, False, partial(
            Processor.evaluate,
            group=[
                "300w", "300f", "300m", "300w4", "300w5",
            ],
            convert=str, op=lambda x, y: x + "\n" + y)),
    ]

    pattern = "./transform/surveys/{survey_id}.{inst_id}.json"

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
                raise UserWarning(f"Missing class attribute: {attr}")

        self.survey = Survey.load_survey(self.ids, self.pattern)
        self.image_transformer = ImageTransformer(self.log, self.survey, self.response,
                                                  sequence_no=self.ids.seq_nr, base_image_path=SDX_FTP_IMAGE_PATH)

    @staticmethod
    def transform(data, survey=None):
        """Perform a transform on survey data.

        We generate defaults only for certain mandatory values.
        We will not receive any value for an aggregate total.

        """
        pattern = re.compile("[0-9]+")

        # Taking the question_id for each supplied answer, and then also
        # rounding down the first numeric component of each answered question_id
        # gives us the set of downstream questions we have data for.
        supplied = set(itertools.chain.from_iterable((
            Decimal(i.group(0)),
            (Decimal(i.group(0)) / 10).quantize(Decimal(1), rounding=ROUND_DOWN) * 10)
            for i in (pattern.match(key) for key in data)
            if i is not None
        ))
        mandatory = set([Decimal("130"), Decimal("131"), Decimal("132")])

        if 'd50' in data or 'd50f' in data:
            mandatory.update([Decimal("50"), Decimal("60"), Decimal("70"), Decimal("80")])

        if 'd151' in data:
            mandatory.update([Decimal("151"), Decimal("171"), Decimal("181")])

        if 'd152' in data:
            mandatory.update([Decimal("152"), Decimal("172"), Decimal("182")])

        if 'd153' in data:
            mandatory.update([Decimal("153"), Decimal("173"), Decimal("183")])

        return OrderedDict(
            (question_id, funct(question_id, data, default, survey))
            for question_id, (default, funct) in MWSSTransformer.ops().items()
            if Decimal(question_id) in supplied.union(mandatory)
        )

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

    def create_pck(self):
        data = self.transform(self.response["data"], self.survey)
        id_dict = self.ids._asdict()
        pck_name = CSFormatter.pck_name(id_dict["survey_id"], id_dict["seq_nr"])
        pck = CSFormatter.get_pck(data, id_dict["inst_id"], id_dict["ru_ref"], id_dict["ru_check"], id_dict["period"])
        return pck_name, pck

    def create_receipt(self):
        id_dict = self.ids._asdict()
        idbr_name = CSFormatter.idbr_name(id_dict["user_ts"], id_dict["seq_nr"])
        idbr = CSFormatter.get_idbr(id_dict["survey_id"], id_dict["ru_ref"], id_dict["ru_check"], id_dict["period"])
        return idbr_name, idbr