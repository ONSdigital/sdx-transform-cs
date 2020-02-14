import copy
from datetime import datetime
import decimal
from decimal import Decimal, ROUND_HALF_UP
import logging

import dateutil.parser
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


class PCKTransformer:
    comments_questions = ['147', '146a', '146b', '146c', '146d', '146e', '146f', '146g', '146h', '146i', '146j', '146k']
    rsi_turnover_questions = ["20", "21", "22", "23", "24", "25", "26"]
    rsi_currency_questions = rsi_turnover_questions + ["27"]
    employee_questions = ["50", "51", "52", "53", "54"]  # Used by qbs and rsi surveys

    qcas_machinery_acquisitions_questions = ['688', '695', '703', '707', '709', '711']
    qcas_other_acquisitions_questions = ['681', '697']
    qcas_disposals_questions = ['689', '696', '704', '708', '710', '712']
    qcas_calculated_total = ['692', '693', '714', '715']  # Calculated summary values
    qcas_currency_questions = qcas_other_acquisitions_questions + qcas_disposals_questions + qcas_machinery_acquisitions_questions + qcas_calculated_total

    qpses_decimal_questions = ["60", "561", "562", "661", "662"]

    # QSS (Stocks - survey_id 017) has 20 different formtypes where the majority of questions both numeric and in need of rounding.
    # The list of answers that DON'T need rounding is much shorter.
    qss_non_currency_questions = ["11", "12", "15", "146", '146a', '146b', '146c', '146d', '146e', '146f', '146g', '146h']

    # Mapping used to calculate totals and which qcode should hold the total value.
    qss_questions = {
        "0001": {
            "start": ['139', '144', '149'],
            "end": ['140', '145', '150']
        },
        "0002": {
            "start": ['139', '144', '149'],
            "end": ['140', '145', '150']
        },
        "0003": {
            "start": ['319', '329'],
            "end": ['320', '330']
        },
        "0004": {
            "start": ['319', '329'],
            "end": ['320', '330']
        },
        "0005": {
            "start": ['174', '179', '184', '189', '191'],
            "end": ['175', '180', '185', '190', '192']
        },
        "0006": {
            "start": ['174', '179', '184', '189', '191'],
            "end": ['175', '180', '185', '190', '192']
        },
        "0007": {
            "start": ['204', '209', '214'],
            "end": ['205', '210', '215']
        },
        "0008": {
            "start": ['204', '209', '214'],
            "end": ['205', '210', '215']
        },
        "0009": {
            "start": ['119', '144', '174', '179', '209'],
            "end": ['120', '145', '175', '180', '210']
        },
        "0010": {
            "start": ['119', '144', '174', '179', '209'],
            "end": ['120', '145', '175', '180', '210']
        },
        "0011": {
            "start": ['119', '144'],
            "end": ['120', '145']
        },
        "0012": {
            "start": ['119', '144'],
            "end": ['120', '145']
        },
        "0013": {
            "start": ['139', '144', '149'],
            "end": ['140', '145', '150']
        },
        "0014": {
            "start": ['139', '144', '149'],
            "end": ['140', '145', '150']
        },
        "0033": {
            "non_dwelling_questions_start": ['219', '229'],
            "non_dwelling_questions_end": ['220', '230'],
            "dwelling_questions_start": ['249', '259'],
            "dwelling_questions_end": ['250', '260'],
        },
        "0034": {
            "non_dwelling_questions_start": ['219', '229'],
            "non_dwelling_questions_end": ['220', '230'],
            "dwelling_questions_start": ['249', '259'],
            "dwelling_questions_end": ['250', '260'],
        },
        "0051": {
            "start": ['498'],
            "end": ['499'],
            "start_total_qcode": "498",
            "end_total_qcode": "499"
        },
        "0052": {
            "start": ['498'],
            "end": ['499'],
            "start_total_qcode": "498",
            "end_total_qcode": "499"
        },
        "0057": {
            "start": ['9', '193', '195'],
            "end": ['10', '194', '196']
        },
        "0058": {
            "start": ['9', '193', '195'],
            "end": ['10', '194', '196']
        },
        "0061": {
            "start": ['498'],
            "end": ['499'],
            "start_total_qcode": "498",
            "end_total_qcode": "499"
        },
        "0070": {
            "start": ['598'],
            "end": ['599'],
            "start_total_qcode": "598",
            "end_total_qcode": "599"
        }
    }

    form_types = {
        "019": {
            "0018": "0018",
            "0019": "0019",
            "0020": "0020"
        },
        "017": {
            "0001": "STP01",
            "0002": "STP01",
            "0003": "STQ03",
            "0004": "STQ03",
            "0005": "STE05",
            "0006": "STE05",
            "0007": "STE15",
            "0008": "STE15",
            "0009": "STE09",
            "0010": "STE09",
            "0011": "STE17",
            "0012": "STE17",
            "0013": "STE13",
            "0014": "STE13",
            "0033": "STC02",
            "0034": "STC02",
            "0051": "STW02",
            "0052": "STW02",
            "0057": "STM01",
            "0058": "STM01",
            "0061": "STW01",
            "0070": "STS01"
        },
        "023": {
            "0102": "RSI5B",
            "0112": "RSI6B",
            "0203": "RSI7B",
            "0205": "RSI9B",
            "0213": "RSI8B",
            "0215": "RSI10B"
        },
        "139": {
            "0001": "Q01B",
        },
        "160": {
            "0002": "T26A",
        },
        "165": {
            "0002": "T17A",
        },
        "169": {
            "0003": "T18A",
        },
        "182": {
            "0006": "VT6A",
        },
        "183": {
            "0006": "VT6A",
        },
        "184": {
            "0006": "VT6A",
        },
        "185": {
            "0005": "VT5A",
        },
    }

    qcas_survey_id = "019"
    qss_survey_id = "017"
    rsi_survey_id = "023"
    qbs_survey_id = "139"
    qpses_survey_ids = ["160", "165", "169"]

    def __init__(self, survey, response_data):
        self.survey = survey
        self.response = response_data

        self.data = copy.deepcopy(response_data['data']) if 'data' in response_data else {}
        self.form_questions = None
        self.form_question_types = None

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
                logger.debug("No type in answer.")

        return questions, question_types

    def get_cs_form_id(self):
        """
        Returns the formtype that common software uses from self.response data.  Also checks the form_type and intstrument_id are valid too.
        :returns: Common software version of formtype, or None if either form_type or instrument_id are invalid.
        """
        instrument_id = self.response['collection']['instrument_id']

        try:
            form_type = self.form_types[self.survey['survey_id']]
        except KeyError:
            logger.error("Invalid survey id", survey_id=self.survey['survey_id'])
            return None

        try:
            form_id = form_type[instrument_id]
        except KeyError:
            logger.error("Invalid instrument id", instrument_id=instrument_id)
            return None

        return form_id

    def get_subdate_str(self):
        """
        Gets the submission date from the 'submitted_at' field in the response and returns it formatted
        :returns: Date formatted in the 'dd/mm/yy' format.
        """
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
        if self.survey['survey_id'] in [self.rsi_survey_id, self.qcas_survey_id, self.qss_survey_id]:
            if '11' not in self.data:
                start_date = datetime.strptime(self.response['metadata']['ref_period_start_date'], "%Y-%m-%d")
                self.data['11'] = start_date.strftime("%d/%m/%Y")
            if '12' not in self.data:
                end_date = datetime.strptime(self.response['metadata']['ref_period_end_date'], "%Y-%m-%d")
                self.data['12'] = end_date.strftime("%d/%m/%Y")

    def round_numeric_values(self):
        """For RSI, QPSES Surveys, round the values of the currency fields.
        Rounds up if the value is .5

        For QSS (Stocks), round to the nearest thousand for every field EXCEPT a select list of
        non-numeric fields.

        For QCAS Surveys, round the values of the currency fields and divide
        by 1000 (i.e., 56100 would return 56)

        """
        if self.survey.get('survey_id') in [self.rsi_survey_id]:
            self.data.update({k: str(self.round_to_nearest_whole_number(v))
                              for k, v in self.data.items() if k in self.rsi_currency_questions})

        if self.survey.get('survey_id') in self.qpses_survey_ids:
            self.data.update({k: str(self.round_to_nearest_whole_number(v))
                              for k, v in self.data.items() if k in self.qpses_decimal_questions})

        if self.survey.get('survey_id') in [self.qss_survey_id]:
            self.data.update({k: str(self.round_to_nearest_thousand(v))
                              for k, v in self.data.items() if k not in self.qss_non_currency_questions})

        if self.survey.get('survey_id') in [self.qcas_survey_id]:
            self.data.update({k: str(self.round_to_nearest_thousand(v))
                              for k, v in self.data.items() if k in self.qcas_currency_questions})

    def parse_negative_values(self):
        """If any number field contains a negative value then replace it with a number containing
        the maxiumum number of 9's that downstream will allow
        """
        for k, v in self.data.items():  # noqa
            try:
                # If v isn't a number then an exception is thrown and we skip it
                int_v = int(v)
                # If the original number is between -1 and -499, it gets rounded to -0.  In this case, we want it to
                # also be all 9's as the original number was negative.
                if v == '-0' or int_v < 0:
                    self.data[k] = '9' * 11
            except ValueError:
                continue

    def evaluate_confirmation_questions(self):
        """
        For RSI and QBS Surveys, impute breakdown values as zero if the total
        provided was zero.
        For QCAS, the confirmation questions are not needed for transformation.
        """
        if self.survey.get('survey_id') == self.rsi_survey_id:
            if 'd20' in self.data:
                self.data.update({k: '0' for k in self.rsi_turnover_questions})
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
        For QCAS:
        Calculates the total value for both acquisitions and proceeds from disposals for machinery and equipment section
        as well as all sections.
        q_code - 692 - Total value of all acquisitions questions.
        q_code - 693 - Total value of all disposals questions.
        q_code - 714 - Total value of all acquisitions questions for only machinery and equipments sections.
        q_code - 715 - Total value of all disposals questions for only machinery and equipments sections.

        For QSS (Stocks):
        Calculates the total value of past and present stock values.  There are 20 different formtypes with different questions
        so there is a map of what formtype uses for its past and present stock value questions. Formtypes 0033 and 0034 have multiple totals
        which is why they're handled differently.
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
        if self.survey.get('survey_id') == self.qss_survey_id:
            instrument_id = self.response['collection']['instrument_id']
            if instrument_id in ['0033', '0034']:
                self._compute_multiple_total_qss_totals()
            else:
                self._compute_single_total_qss_totals()

    def _compute_single_total_qss_totals(self):
        """
        Calculates the start and end stock values for QSS (Stocks).  Saves these to qcode 65 and 66 respectively except for a few types
        that have the qcode for the totals defined in the mapping.
        """
        instrument_id = self.response['collection']['instrument_id']
        try:
            start_questions = self.qss_questions[instrument_id]['start']
            end_questions = self.qss_questions[instrument_id]['end']
            start_total_qcode = self.qss_questions[instrument_id].get('start_total_qcode', '65')
            end_total_qcode = self.qss_questions[instrument_id].get('end_total_qcode', '66')
        except KeyError:
            logger.exception("Missing key from mapping.  Is the mapping for the formtype correct?", formtype=instrument_id)
            raise

        start_total = sum(Decimal(value) for q_code, value in self.data.items() if q_code in start_questions)
        end_total = sum(Decimal(value) for q_code, value in self.data.items() if q_code in end_questions)
        self.data[start_total_qcode] = str(start_total)
        self.data[end_total_qcode] = str(end_total)

    def _compute_multiple_total_qss_totals(self):
        """
        Calculates the start and end stock values for QSS (Stocks).  This is used for the two formtypes that have two
        totals to calculate. Saves the total values to 298 and 299 for the non-dwelling questions and 398 and 399 for the
        dwelling questions.
        """
        instrument_id = self.response['collection']['instrument_id']
        try:
            non_dwelling_start_questions = self.qss_questions[instrument_id]['non_dwelling_questions_start']
            non_dwelling_end_questions = self.qss_questions[instrument_id]['non_dwelling_questions_end']
            dwelling_start_questions = self.qss_questions[instrument_id]['dwelling_questions_start']
            dwelling_end_questions = self.qss_questions[instrument_id]['dwelling_questions_end']
        except KeyError:
            logger.exception("Missing key from mapping.  Is the mapping for the formtype correct?", formtype=instrument_id)
            raise

        non_dwelling_start_total = sum(Decimal(value) for q_code, value in self.data.items() if q_code in non_dwelling_start_questions)
        non_dwelling_end_total = sum(Decimal(value) for q_code, value in self.data.items() if q_code in non_dwelling_end_questions)
        dwelling_start_total = sum(Decimal(value) for q_code, value in self.data.items() if q_code in dwelling_start_questions)
        dwelling_end_total = sum(Decimal(value) for q_code, value in self.data.items() if q_code in dwelling_end_questions)
        self.data['298'] = str(non_dwelling_start_total)
        self.data['299'] = str(non_dwelling_end_total)
        self.data['398'] = str(dwelling_start_total)
        self.data['399'] = str(dwelling_end_total)

    def parse_estimation_question(self):
        """
        For QSS (Stocks), the estimation question needs to be converted from Yes/No to 1/0.
        """
        if self.survey.get('survey_id') == self.qss_survey_id:
            self.data['15'] = "1" if self.response["data"].get("15") == "Yes" else "0"

    def derive_answers(self):
        """Takes a loaded dict structure of survey data and answers sent
        in a request and derives values to use in response
        """
        derived = []
        try:
            self.populate_period_data()
        except KeyError:
            logger.info("Missing metadata")

        # Important: Round first, then calculate totals, otherwise the totals won't add up correctly
        self.round_numeric_values()
        self.calculate_total_playback()

        self.parse_negative_values()
        self.evaluate_confirmation_questions()
        self.parse_estimation_question()

        answers = self.preprocess_comments()

        self.form_questions, self.form_question_types = self.get_form_questions()

        required_answers = [k for k, v in self.form_question_types.items() if v == 'contains']
        required = self.get_required_answers(required_answers)

        answers.update(required)

        for k, v in answers.items():
            if int(k) in self.form_questions:
                derived.append((int(k), self.get_derived_value(k, v)))

        return sorted(derived)

    @staticmethod
    def round_to_nearest_thousand(value):
        """QCAS rounding is done on a ROUND_HALF_UP basis and values are divided by 1000 for the pck"""
        decimal.getcontext().rounding = ROUND_HALF_UP
        return Decimal(round(Decimal(float(value))) / 1000).quantize(1)

    @staticmethod
    def round_to_nearest_whole_number(value):
        """Rounds number to nearest whole number (101.4 -> 101, 250.5 -> 251)"""
        return Decimal(value).quantize(Decimal('1.'), ROUND_HALF_UP)
