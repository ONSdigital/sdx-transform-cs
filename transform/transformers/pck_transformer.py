import copy
import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

import dateutil.parser

logger = logging.getLogger(__name__)


class PCKTransformer:
    comments_questions = ['147', '146a', '146b', '146c', '146d', '146e', '146f', '146g', '146h', '146i', '146j', '146k']
    rsi_turnover_questions = ["20", "21", "22", "23", "24", "25", "26"]
    rsi_currency_questions = rsi_turnover_questions + ["27"]
    employee_questions = ["50", "51", "52", "53", "54"]

    qcas_machinery_acquisitions_questions = ['688', '695', '703', '707', '709', '711']
    qcas_other_acquisitions_questions = ['681', '697']
    qcas_disposals_questions = ['689', '696', '704', '708', '710', '712']
    qcas_calculated_total = ['692', '693', '714', '715']  # Calculated summary values
    qcas_currency_questions = qcas_other_acquisitions_questions + qcas_disposals_questions + qcas_machinery_acquisitions_questions + qcas_calculated_total

    form_types = {
        "019": {
            "0018": "0018",
            "0019": "0019",
            "0020": "0020"
        },
        "023": {
            "0102": "RSI5B",
            "0112": "RSI6B",
            "0203": "RSI7B",
            "0205": "RSI9B",
            "0213": "RSI8B",
            "0215": "RSI10B",
        },
        "139": {
            "0001": "Q01B",
        }
    }

    qcas_survey_id = "019"
    rsi_survey_id = "023"
    qbs_survey_id = "139"

    def __init__(self, survey, response_data):
        self.survey = survey
        self.response = response_data

        self.data = copy.deepcopy(response_data['data']) if 'data' in response_data else {}

    def get_form_questions(self):
        """Return the questions (list) and question types (dict
        lookup to question type)
        """
        questions = []
        question_types = {}

        answers = [
            answer for question_group in self.survey['question_groups']
            for answer in question_group['questions']
            if answer['question_id'] not in self.comments_questions
        ]

        for answer in answers:
            questions.append(int(answer['question_id']))
            try:
                question_types[answer['question_id']] = answer['type']
            except KeyError:
                logger.info("No type in answer.")

        return questions, question_types

    def get_cs_form_id(self):
        instrument_id = self.response['collection']['instrument_id']

        try:
            form_type = self.form_types[self.survey['survey_id']]
        except KeyError:
            logger.error("Invalid survey id '{}'".format(self.survey['survey_id']))
            return None

        try:
            form_id = form_type[instrument_id]
        except KeyError:
            logger.error("Invalid instrument id '{}'".format(instrument_id))
            return None

        return form_id

    def get_subdate_str(self):
        submission_date = dateutil.parser.parse(self.response['submitted_at'])

        return submission_date.strftime("%d/%m/%y")

    def get_derived_value(self, question_id, value=None):
        """Returns a derived value to be used in pck response based on the
        question id. Takes a lookup of question types parsed in
        get_form_questions
        """
        if question_id in self.form_question_types:
            form_question_type = self.form_question_types[question_id]
            if form_question_type == 'contains':
                value = "1" if value else "2"
            elif form_question_type == 'date':
                derived_date = datetime.strptime(value, "%d/%m/%Y")

                value = derived_date.strftime("%d%m%y")

        return value.zfill(11)

    def get_required_answers(self, required_answers):
        """Determines if default answers need to be added where
        missing data is in the json payload
        """
        required = []

        for answer in required_answers:
            if answer not in self.data:
                required.append((answer, ''))

        return required

    def populate_period_data(self):
        """If questions 11 or 12 don't appear in the survey data, then populate
        them with the period start and end date found in the metadata
        """
        if self.survey['survey_id'] == self.rsi_survey_id:
            if '11' not in self.data:
                start_date = datetime.strptime(self.response['metadata']['ref_period_start_date'], "%Y-%m-%d")
                self.data['11'] = start_date.strftime("%d/%m/%Y")
            if '12' not in self.data:
                end_date = datetime.strptime(self.response['metadata']['ref_period_end_date'], "%Y-%m-%d")
                self.data['12'] = end_date.strftime("%d/%m/%Y")

    def round_currency_values(self):
        """For RSI/QCAS Surveys, round the values of the currency fields.
        Rounds up if the value is .5
        """
        if self.survey.get('survey_id') in [self.rsi_survey_id, self.qcas_survey_id]:
            self.data.update({k: str(Decimal(v).quantize(Decimal('1.'), ROUND_HALF_UP))
                for k, v in self.data.items()  # noqa
                    if k in self.rsi_currency_questions or k in self.qcas_currency_questions})  # noqa

    def evaluate_confirmation_questions(self):
        """
        For RSI and QBS Surveys, impute breakdown values as zero if the total
        provided was zero.
        For QCAS, the confirmation questions are not needed for transformation.
        """
        if self.survey.get('survey_id') == self.rsi_survey_id:
            if 'd20' in self.data:
                self.data.update({k: '0' for k in self.rsi_turnover_questions})  # noqa
                del self.data['d20']

        if self.survey.get('survey_id') in [self.rsi_survey_id, self.qbs_survey_id]:
            if 'd50' in self.data:
                self.data.update({k: '0' for k in self.employee_questions})  # noqa
                del self.data['d50']

        if self.survey.get('survey_id') == self.qcas_survey_id:
            if 'd12' in self.data:
                del self.data['d12']

            if 'd681' in self.data:
                del self.data['d681']

    def preprocess_comments(self):
        """147 or any 146x indicates a special comment type that should not be shown
        in pck, but in image. Additionally should set 146 if unset.
        """
        if set(self.comments_questions) <= set(self.data.keys()) and '146' not in self.data.keys():
                self.data['146'] = 1

        data = {k: v for k, v in self.data.items() if k not in self.comments_questions}
        self.data = data
        return self.data

    def calculate_total_playback(self):
        """
        Calculates the total value for both acquisitions and proceeds from disposals for machinery and equipment section
        as well as all sections.
        q_code - 692 - Total value of all acquisitions questions.
        q_code - 693 - Total value of all disposals questions.
        q_code - 714 - Total value of all acquisitions questions for only machinery and equipments sections.
        q_code - 715 - Total value of all disposals questions for only machinery and equipments sections.
        """
        if self.survey.get('survey_id') == self.qcas_survey_id:
            all_acquisitions_questions = self.qcas_machinery_acquisitions_questions + self.qcas_other_acquisitions_questions

            total_machinery_acquisitions = sum(Decimal(value) for q_code, value in self.data.items() if q_code in self.qcas_machinery_acquisitions_questions)
            total_disposals = sum(Decimal(value) for q_code, value in self.data.items() if q_code in self.qcas_disposals_questions)
            all_acquisitions_total = sum(Decimal(value) for q_code, value in self.data.items() if q_code in all_acquisitions_questions)

            self.data['714'] = str(total_machinery_acquisitions)
            self.data['715'] = str(total_disposals)
            self.data['692'] = str(all_acquisitions_total)
            self.data['693'] = str(total_disposals)   # Construction and minerals do not have disposals answers.

    def derive_answers(self):
        """Takes a loaded dict structure of survey data and answers sent
        in a request and derives values to use in response
        """
        derived = []
        try:
            self.populate_period_data()
        except KeyError:
            logger.info("Missing metadata")

        self.calculate_total_playback()
        self.round_currency_values()
        self.evaluate_confirmation_questions()

        answers = self.preprocess_comments()

        self.form_questions, self.form_question_types = self.get_form_questions()

        required_answers = [k for k, v in self.form_question_types.items() if v == 'contains']
        required = self.get_required_answers(required_answers)

        answers.update(required)

        for k, v in answers.items():
            if int(k) in self.form_questions:
                derived.append((int(k), self.get_derived_value(k, v)))

        return sorted(derived)
