class Formatter:
    """Common formatter functions for the various downstream systems."""

    @staticmethod
    def response_json_name(survey_id, seq_nr):
        return "%s_%04d.json" % (survey_id, seq_nr)

    @staticmethod
    def idbr_name(user_ts, seq_nr):
        """Generate the name of an IDBR file."""
        return "REC{0}_{1:04}.DAT".format(user_ts.strftime("%d%m"), int(seq_nr))

    @staticmethod
    def pck_name(survey_id, seq_nr):
        """Generate the name of a PCK file."""
        return "{0}_{1:04}".format(survey_id, int(seq_nr))

    @staticmethod
    def get_idbr(survey_id, ru_ref, ru_check, period):
        """Write an IDBR file."""
        return Formatter._idbr_receipt(survey_id, ru_ref, ru_check, period)

    @staticmethod
    def _idbr_receipt(survey_id, ru_ref, ru_check, period):
        """Format a receipt in IDBR format."""
        # ensure the period is 6 digits
        period = "20" + period if len(period) == 4 else period
        return "{0}:{1}:{2:03}:{3}".format(ru_ref, ru_check, int(survey_id), period)

    @staticmethod
    def get_image_name(tx_id: str, i: int):
        return f"S{Formatter._get_tx_code(tx_id)}_{i}.JPG"

    @staticmethod
    def _get_tx_code(tx_id: str):
        return "".join(tx_id.split("-"))[0:16]
