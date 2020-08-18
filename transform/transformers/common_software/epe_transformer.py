from transform.transformers.survey_transformer import SurveyTransformer


class EPETransformer(SurveyTransformer):
    """Performs the transforms and formatting for the EPE survey.

    EPE is unusual in that it does not create a pck file
    """

    def create_pck(self):
        pck_name = ""
        pck = None
        return pck_name, pck
