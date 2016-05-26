from jinja2 import Environment, PackageLoader
from datetime import datetime

import dateutil.parser
env = Environment(loader=PackageLoader('transform', 'templates'))

form_ids = {
  "0203": "RSI7B",
  "0205": "RSI9B",
  "0213": "RSI8B",
  "0215": "RSI10B"
}

form_questions = {
  "0203": [1, 11, 12, 20, 21, 22, 23, 24, 25, 26, 146],
  "0205": [1, 11, 12, 20, 21, 22, 23, 24, 25, 26, 27, 146],
  "0213": [1, 11, 12, 20, 21, 22, 23, 24, 25, 26, 50, 51, 52, 53, 54, 146],
  "0215": [1, 11, 12, 20, 21, 22, 23, 24, 25, 26, 27, 50, 51, 52, 53, 54, 146]
}

form_question_types = {
  "1": 'contains',
  "11": 'date',
  "12": 'date',
  "146": 'contains'
}

response = {
   "type": "uk.gov.ons.edc.eq:surveyresponse",
   "version": "0.0.1",
   "origin": "uk.gov.ons.edc.eq",
   "survey_id": "023",
   "collection": {
     "exercise_sid": "hfjdskf",
     "instrument_id": "0203",
     "period": "0216"
   },
   "submitted_at": "2016-03-12T10:39:40Z",
   "metadata": {
     "user_id": "789473423",
     "ru_ref": "12345678901A"
   },
   "data": {
     "11": "01/04/2016",
     "12": "31/10/2016",
     "20": "1800000",
     "51": "84",
     "52": "10",
     "53": "73",
     "54": "24",
     "50": "205",
     "22": "705000",
     "23": "900",
     "24": "74",
     "25": "50",
     "26": "100",
     "21": "60000",
     "27": "7400",
     "146": "some comment"
   }
}


def get_derived_value(question_id, value):
    if question_id in form_question_types:
        form_question_type = form_question_types[question_id]

        if form_question_type == 'contains':
            value = "1" if value else "2"
        elif form_question_type == 'date':
            derived_date = datetime.strptime(value, "%d/%m/%Y")

            value = derived_date.strftime("%d%m%y")

    return value.zfill(11)


def derive_answers(answers, instrument_id):
    answers = []

    for k, v in response['data'].items():
        if int(k) in form_questions[instrument_id]:
            answers.append((int(k), get_derived_value(k, v)))

    return sorted(answers)


template = env.get_template('pck.tmpl')

instrument_id = response['collection']['instrument_id']

submission_date = dateutil.parser.parse(response['submitted_at'])
submission_date_str = submission_date.strftime("%d/%m/%y")

form_id = form_ids[instrument_id]

answers = derive_answers(response['data'].items(), instrument_id)

print(template.render(response=response, submission_date=submission_date_str, batch_number=30000, form_id=form_id, answers=answers))
