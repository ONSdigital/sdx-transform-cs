from transform.settings import SDX_FTP_IMAGE_PATH
from transform.transformers import ImageTransformer
from transform.transformers.survey import Survey


class Transformer:

    def __init__(self, survey_response, sequence_no, logger) -> None:

        self._logger = logger
        self.ids = Survey.identifiers(survey_response, seq_nr=sequence_no)

        pattern = "./transform/surveys/{survey_id}.{inst_id}.json"
        self.survey = Survey.load_survey(self.ids, pattern)

        self._image_transformer = ImageTransformer(self._logger, self._survey, survey_response,
                                                   sequence_no=sequence_no, base_image_path=SDX_FTP_IMAGE_PATH)

        
