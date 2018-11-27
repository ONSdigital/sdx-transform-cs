import datetime

from transform.utilities.formatter import Formatter


class CSFormatter(Formatter):
    """Formatter for common software systems.

    Serialises standard data types to PCK format.
    Creates a receipt in IDBR format.

    """

    @staticmethod
    def get_pck(data, inst_id, ru_ref, ru_check, period):
        """Write a PCK file."""
        pck_lines = CSFormatter._pck_lines(data, inst_id, ru_ref, ru_check, period)
        output = "\n".join(pck_lines)
        return output + "\n"

    @staticmethod
    def _pck_lines(data, inst_id, ru_ref, ru_check, period):
        """Return a list of lines in a PCK file."""
        return [
            "FV" + " " * 10,
            CSFormatter._pck_form_header(inst_id, ru_ref, ru_check, period),
        ] + [
            CSFormatter._pck_item(q, a) for q, a in data.items()
        ]

    @staticmethod
    def _pck_value(val):
        """Format a value as PCK data."""
        if isinstance(val, list):
            val = bool(val)

        if isinstance(val, bool):
            return 1 if val else 2
        elif isinstance(val, str):
            return 1 if val else 0
        elif isinstance(val, datetime.date):
            return int(val.strftime('%d%m%y'))
        else:
            return val

    @staticmethod
    def _pck_form_header(form_id, ru_ref, ru_check, period):
        """Generate a form header for PCK data."""
        form_id = "{0:04}".format(form_id) if isinstance(form_id, int) else form_id
        return "{0}:{1}{2}:{3}".format(form_id, ru_ref, ru_check, period)

    @staticmethod
    def _pck_item(q, a):
        """Return a PCK line item."""
        try:
            return "{0:04} {1:011}".format(int(q), CSFormatter._pck_value(a))
        except TypeError:
            return "{0} ???????????".format(q)
