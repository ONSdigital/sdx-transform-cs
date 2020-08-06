from transform.transformers.survey import Survey


class Transformer:

    def __init__(self, survey_response, logger, sequence_no) -> None:
        self.survey_response = survey_response
        self._logger = logger
        self.ids = Survey.identifiers(survey_response, seq_nr=sequence_no)

    def create_pck(self):
        pass

    def create_receipt(self):
        pass
