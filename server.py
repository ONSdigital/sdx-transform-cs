import settings
import json
import logging
import logging.handlers
from jinja2 import Environment, PackageLoader
from flask import Flask, request
from pcktransformer import derive_answers, form_ids

import dateutil.parser

env = Environment(loader=PackageLoader('transform', 'templates'))

app = Flask(__name__)


@app.route('/<survey_id>/<form_id>.pck', methods=['POST'])
def pck(survey_id, form_id):
    response = request.get_json(silent=True)
    template = env.get_template('pck.tmpl')

    instrument_id = response['collection']['instrument_id']

    submission_date = dateutil.parser.parse(response['submitted_at'])
    submission_date_str = submission_date.strftime("%d/%m/%y")

    cs_form_id = form_ids[instrument_id]

    with open("./surveys/%s.%s.json" % (survey_id, form_id)) as json_file:
        survey = json.load(json_file)

        answers = derive_answers(survey, response['data'].items())

        return template.render(response=response, submission_date=submission_date_str, batch_number=30000, form_id=cs_form_id, answers=answers)


@app.route('/<survey_id>/<form_id>.idbr', methods=['POST'])
def idbr(survey_id, form_id):
    response = request.get_json(silent=True)
    template = env.get_template('idbr.tmpl')

    return template.render(response=response)


@app.route('/<survey_id>/<form_id>.html', methods=['POST'])
def html(survey_id, form_id):
    response = request.get_json(silent=True)
    template = env.get_template('html.tmpl')

    with open("./surveys/%s.%s.json" % (survey_id, form_id)) as json_file:
        survey = json.load(json_file)
        return template.render(response=response, survey=survey)


if __name__ == '__main__':
    # Startup
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    app.run(debug=True, host='0.0.0.0')
