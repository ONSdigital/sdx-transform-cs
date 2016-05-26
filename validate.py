from voluptuous import Schema, Required, Length, All
from dateutil import parser

response = {
   "type": "uk.gov.ons.edc.eq:surveyresponse",
   "origin": "uk.gov.ons.edc.eq",
   "survey_id": "023",
   "version": "0.0.1",
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


def Timestamp(value):
    return parser.parse(value)

collection_s = Schema({
    Required('period'): str
}, extra=True)

metadata_s = Schema({
    Required('user_id'): str,
    Required('ru_ref'): All(str, Length(12))
})

s = Schema({
    Required('type'): "uk.gov.ons.edc.eq:surveyresponse",
    Required('version'): "0.0.1",
    Required('origin'): "uk.gov.ons.edc.eq",
    Required('survey_id'): str,
    Required('submitted_at'): Timestamp,
    Required('collection'): collection_s,
    Required('metadata'): metadata_s,
}, extra=True)

s(response)
