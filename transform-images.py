from jinja2 import Environment, PackageLoader
import json

env = Environment(loader=PackageLoader('transform', 'templates'))

response = {
   "type": "uk.gov.ons.edc.eq:surveyresponse",
   "version": "0.0.1",
   "origin": "uk.gov.ons.edc.eq",
   "survey_id": "023",
   "collection": {
     "exercise_sid": "hfjdskf",
     "instrument_id": "0203",
     "period": "1604"
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

template = env.get_template('html.tmpl')

with open("./surveys/023.0203.json") as json_file:
    survey = json.load(json_file)
    print(template.render(response=response, survey=survey))
