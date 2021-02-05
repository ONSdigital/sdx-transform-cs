# sdx-transform-cs

[![Build Status](https://github.com/ONSdigital/sdx-transform-cs/workflows/Build/badge.svg)](https://github.com/ONSdigital/sdx-transform-cs) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/0d8f1899b0054322b9d0ec8f2bd62d86)](https://www.codacy.com/app/ons-sdc/sdx-transform-cs?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/sdx-transform-cs&amp;utm_campaign=Badge_Grade) [![codecov](https://codecov.io/gh/ONSdigital/sdx-transform-cs/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/sdx-transform-cs)

The sde-transform-cs app is used within the Office National of Statistics (ONS) for transforming Survey Data Exchange (SDX) Surveys to formats in use in Common Software.

## Prerequisites
The service has a dependency on the `pdf2ppm` commandline tool bundled in the poppler package. 
To check whether this is already installed, run:
```bash
$ make check-dependencies
```

To install `pdf2ppm` on a Mac, use:

```bash
$ brew install poppler
```

## Installation
This application presently installs required packages from requirements files:
- `requirements.txt`: packages for the application, with hashes for all packages: see https://pypi.org/project/hashin/
- `test-requirements.txt`: packages for testing and linting

It's also best to use `pyenv` and `pyenv-virtualenv`, to build in a virtual environment with the currently recommended version of Python.  To install these, see:
- https://github.com/pyenv/pyenv
- https://github.com/pyenv/pyenv-virtualenv
- (Note that the homebrew version of `pyenv` is easiest to install, but can lag behind the latest release of Python.)

### Getting started
Once your virtual environment is set, install the requirements:
```shell
$ make build
```

To test, first run `make build` as above, then run:
```shell
$ make test
```

NOTE: .pck and .nobatch test files are required to not have a newline character at the end of the file.
A simple way to remove it is to do the following command `perl -pi -e 'chomp if eof' filename`

It's also possible to build sdx-transform-cs within a container using docker. From the sdx-transform-cs directory:

```bash
$ docker build -t sdx-transform-cs .
```

## Usage

To start sdx-transform-cs service locally, use the following command:

```bash
$ python server.py
```

If you've built the image under docker, you can start using the following:

```bash
$ docker run -p 5000:5000 sdx-transform-cs
```

sdx-transform-cs by default binds to port 5000 on localhost. It exposes several endpoints for transforming to idbr and pck formats. It returns a response formatted in the type requested. Post requests are made aginst the uri endpoints /pck, /idbr, /images, /common-software or /cord. Responses are delivered in the format requested, except the /images, /common-software, /cord and /cora endpoints which return archived zips of requested data. There is also a health check endpoint (get /healtcheck), which returns a json response with a key/value pairs describing the service state.

### Example

The example below uses the Python library [requests](https://github.com/kennethreitz/requests) to confirm some data is valid using sdx-transform-cs.

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

r = requests.post('http://127.0.0.1:5000/pck', data=data_to_transform)

r.data =

'''FBFV03000012/03/16
FV          
RSI7B:12345678901A:0216'''
```

## Configuration

Some of important environment variables available for configuration are listed below:

| Environment Variable    | Default                               | Description
|-------------------------|---------------------------------------|----------------
| SDX_SEQUENCE_URL        | `http://sdx-sequence:5000`            | URL of the ``sdx-sequence`` service
| FTP_PATH                | `\\`                                  | FTP path
| SDX_FTP_IMAGE_PATH      | `EDC_QImages`                         | Location of EDC Images

## Image generation

When hitting certain endpoints, a zip file that contains a number of JPG images that represent the submission will be returned.
These images are produced with the help of JSON files that describe what the image should look like.  These can be found in
`transform/surveys/*.json`

The keys of these json files describe how the image should look and below is a guide on the what they do.

- `title`: Full survey name, appears at the top as a header
- `survey_id` : Id of the survey, appears below the title
- `form_type` : Form type of the survey,
- `question_groups`:  An array of sections.  Each section is comprised of a heading
and a number of questions relating to that section.

Each element of the question_groups is made up of the following:

- `title`:  Name of the section, appears at the top of the section
- `questions`: Array of questions.  Each question corresponds to a question the respondent would've filled out on EQ.

Each element of questions is made up of the following:

- `text`: This is the heading of the question.  This should be as close as possible to the question asked in EQ.
- `question_id`: This is the qcode of the question.  The code in the data from EQ will be used to populate the answer of this field
- `number`: Used to output the qcode of the question in the image.
- `type`: Can be one of `currency`, `date`, `checkbox`, `radio`, `contains`, `positiveinteger` or `percentage`. None of these affect the image.
The `contains` and `date` types affect the data added to the pck file.  The other types are there to aid in maintaining the survey.
- `options`:  Doesn't affect the image.  It's used to add context to radio and checkbox fields as each possible answer will have its own qcode
but needs to have the same question because of the way it needs to look in the image.

## License

Copyright © 2016, Office for National Statistics (https://www.ons.gov.uk)

Released under MIT license, see [LICENSE](LICENSE) for details.
