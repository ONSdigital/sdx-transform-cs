### Unreleased
  -

### 2.9.0 2017-10-16
  - Support decimal values in MWSS Surveys ( survey_id 005 )
  - Refactored variable names for MWSS transformer

### 2.8.0 2017-10-02
  - Round decimal values in RSI surveys ( survey_id 023 )
  - Update deleting tmp files

### 2.7.0 2017-09-25
  - Removed SDX common clone in docker
  - Restore defaults for qids 130, 131, 132.
  - Remove pip `--require-hashes` requirement
  - Make use of sequence list endpoint
  - Populate default dates on certain surveys from metadata
  - Add fix for cryptography install in docker

### 2.6.0 2017-08-23
  - Update sdx-common version
  - Ensure integrity and version of library dependencies

### 2.5.0 2017-07-25
  - EQ MCI Survey Refresh
  - Change all instances of ADD to COPY in Dockerfile

### 2.4.0 2017-07-10
  - Update and pin version of sdx-common to 0.7.0
  - Remove use of SDX_HOME in makefile

### 2.3.0 2017-06-19
  - Timestamp all logs as UTC
  - Add common library logging
  - Updated to support the refreshed MCI
  - Correct license attribution
  - Remove generation of defaults for unanswered questions
  - Reformat image to make answers more prominent
  - Add codacy badge
  - MCI refresh
  - Add support for codecov to see unit test coverage

### 2.2.1 2017-06-14
  - Incident 0049895 MWSS fix for aggregate question code

### 2.2.0 2017-06-12
  - Correct license attribution
  - Remove generation of defaults for unanswered questions

### 2.1.0 2017-04-03
  - Support non-unique survey ids
  - Add environment variables to README
  - Fix sequence number bug in MWSS survey

### 2.0.1 2017-03-17
  - Change env var read from `FTP_HOST` to `FTP_PATH`
  - Change `Calling service` and `Returned from service` to add context

### 2.0.0 2017-03-16
  - Add MWSS transform
  - Log image file paths

### 1.4.1 2017-03-15
  - Log version number on startup
  - Change `status_code` to `status` for SDX logging

### 1.4.0 2017-02-16
  - Add change log
  - Add license
  - Update python library '_requests_': `2.10.0` -> `2.12.4`
  - Update build process to simplify testing
  - Add image mapping and form type for QBS

### 1.3.0 2016-11-23
  - Fix [#32](https://github.com/ONSdigital/sdx-transform-cs/issues/32) change layout of image to use paragraphs not tables

### 1.2.0 2016-11-10
  - Add `/healthcheck` endpoint
  - Update python library '_pillow_': `3.2.0` -> `3.4.0`
  - Fix [#26](https://github.com/ONSdigital/sdx-transform-cs/issues/26) wrapping unbroken text in image

### 1.1.1 2016-09-29
  - Fix image file for large comments

### 1.1.0 2016-09-19
  - Add configurable logging level
  - Add comment to image but not pck file

### 1.0.1 2016-08-22
  - Add configurable FTP image path

### 1.0.0 2016-08-17
  - Initial release
