import logging
from structlog import wrap_logger
from transform.utilities.formatter import Formatter

logger = wrap_logger(logging.getLogger(__name__))


class CORAFormatter(Formatter):
    """Formatter for CORA systems.

    Serialises standard data types to PCK format.
    Creates a receipt in IDBR format.
    """

    @staticmethod
    def get_pck(data, survey_id, ru_ref, page_identifier, period, instance):
        """Write a PCK file."""
        pck_lines = CORAFormatter._pck_lines(data, survey_id, ru_ref, page_identifier, period, instance)
        output = "\n".join(pck_lines)
        return output

    @staticmethod
    def _pck_lines(data, survey_id, ru_ref, page_identifier, period, instance):
        """Return a list of lines in a PCK file."""
        return ["{0}:{1}:{2}:{3}:{4}:{5}:{6}".format(survey_id, ru_ref, page_identifier, period, instance, qcode, value)
                for qcode, value in sorted(data.items())]
