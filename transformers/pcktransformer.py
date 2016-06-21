from datetime import datetime

form_ids = {
    "0102": "RSI5B",
    "0112": "RSI6B",
    "0203": "RSI7B",
    "0205": "RSI9B",
    "0213": "RSI8B",
    "0215": "RSI10B"
}


def get_form_questions(survey):
    '''
    Return the questions (list) and question types (dict
    lookup to question type)
    '''
    questions = []
    question_types = {}

    for question_group in survey['question_groups']:
        for answer in question_group['questions']:
            question_id = answer['question_id']
            questions.append(int(answer['question_id']))
            if 'type' in answer:
                question_types[question_id] = answer['type']

    return questions, question_types


def get_derived_value(form_question_types, question_id, value=None):
    '''
    Returns a derived value to be used in pck response based on the
    question id. Takes a lookup of question types parsed in
    get_form_questions
    '''
    if question_id in form_question_types:
        form_question_type = form_question_types[question_id]
        if form_question_type == 'contains':
            value = "1" if value else "2"
        elif form_question_type == 'date':
            derived_date = datetime.strptime(value, "%d/%m/%Y")

            value = derived_date.strftime("%d%m%y")

    return value.zfill(11)


def get_required_answers(answers, required_answers):
    '''
    Determines if default answers need to be added where
    missing data is in the json payload
    '''
    required = []

    for answer in required_answers:
        if answer not in answers:
            required.append((answer, ''))

    return required


def derive_answers(survey, answers={}):
    '''
    Takes a loaded dict structure of survey data and answers sent
    in a request and derives values to use in response
    '''
    derived = []

    form_questions, form_question_types = get_form_questions(survey)

    required_answers = [k for k, v in form_question_types.items() if v == 'contains']
    required = get_required_answers(answers, required_answers)

    answers.update(required)

    for k, v in answers.items():
        if int(k) in form_questions:
            derived.append((int(k), get_derived_value(form_question_types, k, v)))

    return sorted(derived)
