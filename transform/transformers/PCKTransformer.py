from datetime import datetime
import dateutil.parser


class PCKTransformer(object):
    form_ids = {
        "0102": "RSI5B",
        "0112": "RSI6B",
        "0203": "RSI7B",
        "0205": "RSI9B",
        "0213": "RSI8B",
        "0215": "RSI10B"
    }

    def __init__(self, survey, response_data):
        self.survey = survey
        self.response = response_data

        self.data = response_data['data'] if 'data' in response_data else {}

    def get_form_questions(self):
        '''
        Return the questions (list) and question types (dict
        lookup to question type)
        '''
        questions = []
        question_types = {}

        for question_group in self.survey['question_groups']:
            for answer in question_group['questions']:
                question_id = answer['question_id']
                if int(question_id) is not 147:
                    questions.append(int(answer['question_id']))
                    if 'type' in answer:
                        question_types[question_id] = answer['type']

        return questions, question_types

    def get_cs_form_id(self):
        instrument_id = self.response['collection']['instrument_id']

        return self.form_ids[instrument_id]

    def get_subdate_str(self):
        submission_date = dateutil.parser.parse(self.response['submitted_at'])

        return submission_date.strftime("%d/%m/%y")

    def get_derived_value(self, question_id, value=None):
        '''
        Returns a derived value to be used in pck response based on the
        question id. Takes a lookup of question types parsed in
        get_form_questions
        '''
        if question_id in self.form_question_types:
            form_question_type = self.form_question_types[question_id]
            if form_question_type == 'contains':
                value = "1" if value else "2"
            elif form_question_type == 'date':
                derived_date = datetime.strptime(value, "%d/%m/%Y")

                value = derived_date.strftime("%d%m%y")

        return value.zfill(11)

    def get_required_answers(self, required_answers):
        '''
        Determines if default answers need to be added where
        missing data is in the json payload
        '''
        required = []

        for answer in required_answers:
            if answer not in self.data:
                required.append((answer, ''))

        return required

    def preprocess_comments(self):
        '''
        147 indicates a special comment type that should not be shown
        in pck, but in image. Additionally should set 146 if unset.
        '''
        if '147' in self.data:
            del self.data['147']
            if '146' not in self.data:
                self.data['146'] = 1

        return self.data

    def derive_answers(self):
        '''
        Takes a loaded dict structure of survey data and answers sent
        in a request and derives values to use in response
        '''
        derived = []
        answers = self.preprocess_comments()

        self.form_questions, self.form_question_types = self.get_form_questions()

        required_answers = [k for k, v in self.form_question_types.items() if v == 'contains']
        required = self.get_required_answers(required_answers)

        answers.update(required)

        for k, v in answers.items():
            if int(k) in self.form_questions:
                derived.append((int(k), self.get_derived_value(k, v)))

        return sorted(derived)
