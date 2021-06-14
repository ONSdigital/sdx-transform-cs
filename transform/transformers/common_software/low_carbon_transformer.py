from transform.transformers.survey_transformer import SurveyTransformer


class LCTransformer(SurveyTransformer):
    """Performs the transforms and formatting for the low carbon survey.

    low carbon is unusual in that it does not create a pck file
    """

    def create_pck(self):
        pck_name = ""
        pck = None
        return pck_name, pck
