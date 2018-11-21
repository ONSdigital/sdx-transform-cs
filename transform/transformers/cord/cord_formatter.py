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
        return ["{0}:{1}:{2}:{3}:{4}".format(ru_ref, survey_id, period, qcode, value) for qcode, value in sorted(data.items())]
