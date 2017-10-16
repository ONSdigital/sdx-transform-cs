#!/usr/bin/env python
#  coding: UTF-8

import argparse
import logging
import os.path
import sys

DFLT_LOCN = os.path.expanduser("~")

__doc__ = """
Defines a common CLI for SDX tooling.

Operation via CLI requires a set of common options.


"""


def logging_format(service="sdx-common"):
    return "%(asctime)s|%(levelname)s: {0}: %(message)s".format(service)


def add_common_options(parser):
    parser.add_argument(
        "--version", action="store_true", default=False,
        help="Print the current version number")
    parser.add_argument(
        "-v", "--verbose", required=False,
        action="store_const", dest="log_level",
        const=logging.DEBUG, default=logging.INFO,
        help="Increase the verbosity of output")
    return parser


def add_transformer_options(parser):
    parser.add_argument(
        "--work", default=DFLT_LOCN,
        help="Set a path to the working directory.")
    parser.add_argument(
        "--img_nr", type=int, default=0,
        help="Set a starting number for the image sequence.")
    parser.add_argument(
        "--seq_nr", type=int, default=0,
        help="Set a sequence number for the data output.")
    parser.add_argument(
        "input",
        nargs="?", type=argparse.FileType("r"), default=sys.stdin,
        help="Specify survey data."
    )
    parser.add_argument(
        "output",
        nargs="?", type=argparse.FileType("wb"), default=sys.stdout.buffer,
        help="Specify output file."
    )
    return parser


def parser(description):
    return argparse.ArgumentParser(
        description,
    )


def transformer_cli(description=__doc__):
    return add_transformer_options(
        add_common_options(
            parser(description)
        )
    )
