# sdx-transform-cs

The sde-transform-cs app is used within the Office National of Statistics (ONS) for transforming Survey Data Exchange (SDX) Surveys.

## Installation

Using virtualenv and pip, create a new environment and install within using:

    $ pip install -r requirements.txt

It's also possible to install within a container using docker. From the sdx-validate directory:

    $ docker build -t sdx-transform-cs .

## Usage

Start sdx-transform-cs service using the following command:

    python server.py

sdx-transform-cs exposes a three endpoints for transforming to idbr, pck and html formats and by default binds to port 5000 on localhost. It returns a response formatted in the typerequested. Post requests are made aginst the uri scheme /<survey_id>/<form_id>.<format>

### Example

The example below uses the Python library [requests](https://github.com/kennethreitz/requests) to confirm some data is valid using sdx-validate.

```python
import requests

data_to_transform = '''{
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
}'''

r = requests.post('http://127.0.0.1:5000/023/0203.pck', data=data_to_transform)

r.data = 

'''FBFV03000012/03/16
FV          
RSI7B:12345678901A:0216'''

```