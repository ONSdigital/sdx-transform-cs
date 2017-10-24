class CSFormatter:
    """Formatter for common software systems.

    Serialises standard data types to PCK format.
    Creates a receipt in IDBR format.

    """

    form_ids = {
        "134": "0004",
    }

    @staticmethod
    def pck_name(survey_id, seq_nr, **kwargs):
        """Generate the name of a PCK file."""
        return "{0}_{1:04}".format(survey_id, int(seq_nr))

    @staticmethod
    def pck_batch_header(batch_nr, ts):
        """Generate a batch header for a PCK file."""
        return "{0}{1:06}{2}".format("FBFV", batch_nr, ts.strftime("%d/%m/%y"))

    @staticmethod
    def pck_form_header(form_id, ru_ref, ru_check, period):
        """Generate a form header for PCK data."""
        form_id = "{0:04}".format(form_id) if isinstance(form_id, int) else form_id
        return "{0}:{1}{2}:{3}".format(form_id, ru_ref, ru_check, period)

    @staticmethod
    def pck_value(qid, val, survey_id=None):
        """Format a value as PCK data."""
        if isinstance(val, list):
            val = bool(val)

        if isinstance(val, bool):
            return 1 if val else 2
        elif isinstance(val, str):
            return 1 if val else 0
        else:
            return val

    @staticmethod
    def pck_item(q, a):
        """Return a PCK line item."""
        try:
            return "{0:04} {1:011}".format(int(q), CSFormatter.pck_value(q, a))
        except TypeError:
            return "{0} ???????????".format(q)

    @staticmethod
    def pck_lines(data, batch_nr, ts, survey_id, inst_id, ru_ref, ru_check, period, **kwargs):
        """Return a list of lines in a PCK file."""
        return [
            "FV" + " " * 10,
            CSFormatter.pck_form_header(inst_id, ru_ref, ru_check, period),
        ] + [
            CSFormatter.pck_item(q, a) for q, a in data.items()
        ]

    @staticmethod
    def write_pck(f_obj, data, **kwargs):
        """Write a PCK file."""
        output = CSFormatter.pck_lines(data, **kwargs)
        f_obj.write("\n".join(output))
        f_obj.write("\n")

    @staticmethod
    def idbr_name(user_ts, seq_nr, **kwargs):
        """Generate the name of an IDBR file."""
        return "REC{0}_{1:04}.DAT".format(user_ts.strftime("%d%m"), int(seq_nr))

    @staticmethod
    def idbr_receipt(survey_id, ru_ref, ru_check, period, **kwargs):
        """Format a receipt in IDBR format."""
        return "{ru_ref}:{ru_check}:{survey_id:03}:{period}".format(
            survey_id=int(survey_id), ru_ref=ru_ref, ru_check=ru_check, period=period
        )

    @staticmethod
    def write_idbr(f_obj, **kwargs):
        """Write an IDBR file."""
        output = CSFormatter.idbr_receipt(**kwargs)
        f_obj.write(output)
        f_obj.write("\n")
