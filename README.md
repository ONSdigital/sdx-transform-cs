# sdx-transform-cs

[![Build Status](https://travis-ci.org/ONSdigital/sdx-transform-cs.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-transform-cs) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/0d8f1899b0054322b9d0ec8f2bd62d86)](https://www.codacy.com/app/ons-sdc/sdx-transform-cs?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/sdx-transform-cs&amp;utm_campaign=Badge_Grade) [![codecov](https://codecov.io/gh/ONSdigital/sdx-transform-cs/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/sdx-transform-cs)

The sde-transform-cs app is used within the Office National of Statistics (ONS) for transforming Survey Data Exchange (SDX) Surveys to formats in use in Common Software.

## Installation

The service has a dependency on the pdf2ppm commandline tool bundled in the poppler package. You can install this on a mac using:

    $ brew install poppler

*It is recommended that this service is installed inside a virtualenv.*

To install, use:

```bash
make build
```

To install using local sdx-common repo (requires SDX_HOME environment variable), use:

```bash
make dev
```

To run the test suite, use:

```bash
make test
```

NOTE: .pck and .nobatch test files are required to not have a newline character at the end of the file.
A simple way to remove it is to do the following command `perl -pi -e 'chomp if eof' filename`

It's also possible to build sdx-transform-cs within a container using docker. From the sdx-transform-cs directory:

    $ docker build -t sdx-transform-cs .

## Usage

To start sdx-transform-cs service locally, use the following command:

    python server.py

If you've built the image under docker, you can start using the following:

    docker run -p 5000:5000 sdx-transform-cs

sdx-transform-cs by default binds to port 5000 on localhost. It exposes several endpoints for transforming to idbr, pck and html formats. It returns a response formatted in the type requested. Post requests are made aginst the uri endpoints /pck, /idbr, /html, /pdf, /images or /common-software. Responses are delivered in the format requested, except the /images and /common-software endpoints which return archived zips of requested data. There is also a health check endpoint (get /healtcheck), which returns a json response with a key/value pairs describing the service state.

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
| FTP_PATH                | `\\\\NP3-------370\\SDX_preprod\\`    | FTP path
| SDX_FTP_IMAGE_PATH      | `EDC_QImages`                         | Location of EDC Images

### License

Copyright © 2016, Office for National Statistics (https://www.ons.gov.uk)

Released under MIT license, see [LICENSE](LICENSE) for details.
