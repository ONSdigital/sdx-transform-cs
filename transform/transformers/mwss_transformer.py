from collections import OrderedDict
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from functools import partial

import itertools
import re

from transform.transformers.processor import Processor
from transform.transformers.transformer import Transformer

__doc__ = """Transform MWSS survey data into formats required downstream.

The class API is used by the SDX transform service.
"""


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
                "190w4", "191w4", "192w4", "193w4", "194w4", "195w4", "196w4", "197w4",
                "190m", "191m", "192m", "193m", "194m", "195m", "196m", "197m",
                "190w5", "191w5", "192w5", "193w5", "194w5", "195w5", "196w5", "197w5",
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
        return OrderedDict(
            (question_id, funct(question_id, data, default, survey))
            for question_id, (default, funct) in MWSSTransformer.ops().items()
            if Decimal(question_id) in supplied.union(mandatory)
        )