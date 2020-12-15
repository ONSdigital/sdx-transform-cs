class Formatter:
    """Common formatter functions for the various downstream systems."""

    @staticmethod
    def response_json_name(survey_id, tx_id):
        return "{0}_{1}.json".format(survey_id, Formatter._get_tx_code(tx_id))

    @staticmethod
    def idbr_name(user_ts, tx_id):
        """Generate the name of an IDBR file."""
        return "REC{0}_{1}.DAT".format(user_ts.strftime("%d%m"), Formatter._get_tx_code(tx_id))

    @staticmethod
    def pck_name(survey_id, tx_id):
        """Generate the name of a PCK file."""
        return f"{survey_id}_{Formatter._get_tx_code(tx_id)}"

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
    def get_index_name(survey_id: str, submission_date: str, tx_id: str):
        tx_code = Formatter._get_tx_code(tx_id)
        return "EDC_{0}_{1}_{2}.csv".format(survey_id, submission_date, tx_code)

    @staticmethod
    def _get_tx_code(tx_id: str):
        """Format the tx_id."""
        # tx_code is the first 16 digits of the tx_id without hyphens
        return "".join(tx_id.split("-"))[0:16]
