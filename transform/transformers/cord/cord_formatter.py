import logging
from structlog import wrap_logger
from transform.utilities.formatter import Formatter

logger = wrap_logger(logging.getLogger(__name__))


class CORDFormatter(Formatter):
    """Formatter for CORD systems.

    Serialises standard data types to PCK format.
    Creates a receipt in IDBR format.

    """

    @staticmethod
    def get_pck(data, survey_id, ru_ref, period):
        """Write a PCK file."""
        pck_lines = CORDFormatter._pck_lines(data, survey_id, ru_ref, period)
        output = "\n".join(pck_lines)
        return output

    @staticmethod
    def _pck_lines(data, survey_id, ru_ref, period):
        """Return a list of lines in a PCK file."""
        return [f"{ru_ref}:{survey_id}:{period}:{qcode}:{value}" for qcode, value in sorted(data.items())]

    @staticmethod
    def get_idbr(survey_id, ru_ref, ru_check, period):
        """Write an IDBR file.
        CORD currently only has one survey; E-commerce, an annual survey with a 4 digit period representing YYYY.
        IDBR requires 6 digits and so a '12' is appended to the period to represent the month.
        If CORD receives a period in 6 digit format then it can be passed to IDBR unaltered.
        If in the future CORD requires a monthly survey with a 4 digit period (YYMM)
        then this method will have to change."""

        period = period + "12" if len(period) == 4 else period
        return "{0}:{1}:{2:03}:{3}".format(ru_ref, ru_check, int(survey_id), period)
