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
from structlog import wrap_logger

from sdx.common.formats.cs_formatter import CSFormatter
from sdx.common.processor import Processor
from sdx.common.survey import Survey
from sdx.common.transformer import Transformer

__doc__ = """Transform MWSS survey data into formats required downstream.

The class API is used by the SDX transform service.
Additionally this module will run as a script from the command line:

python -m transform.transformers.MWSSTransformer \
< tests/replies/eq-mwss.json > test-output.zip

"""


class MWSSTransformer(Transformer):
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

    package = __name__
    pattern = "../surveys/{survey_id}.{inst_id}.json"


def run():
    reply = json.load(sys.stdin)
    tfr = MWSSTransformer(reply)
    zipfile = tfr.pack(img_seq=itertools.count())
    sys.stdout.buffer.write(zipfile.read())

if __name__ == "__main__":
    run()
