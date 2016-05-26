from datetime import datetime

form_ids = {
  "0203": "RSI7B",
  "0205": "RSI9B",
  "0213": "RSI8B",
  "0215": "RSI10B"
}


def get_form_questions(survey):
    questions = []
    question_types = {}

    for answer_group in survey['answer_groups']:
        for answer in answer_group['answers']:
            question_id = answer['question_id']
            questions.append(int(question_id))
            if 'type' in answer:
                question_types[question_id] = answer['type']

    return questions, question_types


def get_derived_value(form_question_types, question_id, value):
    if question_id in form_question_types:
        form_question_type = form_question_types[question_id]
        if form_question_type == 'contains':
            value = "1" if value else "2"
        elif form_question_type == 'date':
            derived_date = datetime.strptime(value, "%d/%m/%Y")

            value = derived_date.strftime("%d%m%y")

    return value.zfill(11)


def derive_answers(survey, answers):
    derived = []

    form_questions, form_question_types = get_form_questions(survey)

    for k, v in answers:
        if int(k) in form_questions:
            derived.append((int(k), get_derived_value(form_question_types, k, v)))

    return sorted(derived)
