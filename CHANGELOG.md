### Unreleased

### 4.0.0 2020-09-07
 - Major refactor
 - Add EPE transformer
 - Moved logging setup

### 3.21.0 2020-08-05
 - Fix E-commerce index file period 

### 3.20.0 2020-07-28
 - Ensure IDBR receipts have a 6 digit period

### 3.19.0 2020-07-07
 - Remove Vacancies formtype mapping to 181 for indices  
 - Add openapi.yml
 - Add uml diagrams

### 3.18.0 2020-06-09
 - Add construction formtype 0002
 - Remove Cloudfoundry deployment files

### 3.17.1 2020-05-21
 - Updated packages

### 3.17.0 2020-04-27
 - Fix construction transformation when total value is zero and missing qcodes 902-904 

### 3.16.0 2020-04-17
 - Add construction survey

### 3.15.0 2020-03-20
 - Handle new comment field in QBS (139)

### 3.14.1 2020-03-03
 - Added implicit percentages for a number of sets of questions in Ecommerce (0001, 0002)
 - Changed filename generation in vacancies to match the downstream requirements (IDBR unchanged, everything else changed to survey id 181)
 - Fixed the titles for Vacancies images.

### 3.14.0 2020-01-30
 - Add Vacancies survey

### 3.13.1 2019-12-17
 - Fix transformation errors in e-commerce 0001 and 0002 formtypes

### 3.13.0 2019-11-25
 - Add E-commerce 2019 survey
 - Update packages and fix security issue in Pillow

### 3.12.3 2019-11-08
 - Add python 3.8 to travis builds

### 3.12.2 2019-09-26
 - Update werkzeug to 0.15.6 to fix security issue
 - Update various packages to keep them current

### 3.12.1 2019-09-04
 - Update documentation
 - Remove unused `comments` value in JSON files used for image generation

### 3.12.0 2019-08-13
 - Remove unused `/html` and `/pdf` endpoints

### 3.11.2 2019-06-28
 - Fix incorrect value in stocks formtypes 0001 and 0002

### 3.11.1 2019-06-19
 - Update structlog package version
 - Fix incorrect value in stocks formtype 0061

### 3.11.0 2019-05-31
 - Renamed QSI (Quarterly Stocks Inquiry) to QSS (Quarterly Stocks Survey)
 - Add calculated totals for QSS as the totals aren't passed to SDX
 - Fix missing date qcodes (11 and 12) for QSS (Stocks)
 - Add formtype 0070 for QSS (Stocks)
 - Change rounding to stocks to divide by 1000 after rounding (like QCAS)

### 3.10.0 2019-04-02
 - Update Jinja to 2.10.1 to fix a security issue.
 - Update Pillow and PyYAML versions
 - Updated the dockerfile
 - Used Python 3.5 inbuilt dictionary merging instead of merge_dicts
 - Added support for QSI (Stocks) survey

### 3.9.0 2019-02-19
 - Added support for QPSES survey

### 3.8.0 2019-02-08
 - Added support for UKIS and CORA surveys

### 3.7.1 2018-12-20
 - Change option value for E-Commerce q-code 416 (r3)
 - Ensure r3 is on image file

### 3.7.0 2018-12-12
  - Added support for E-commerce form and CORD surveys.
  - Improve tests for mbs_transformer

### 3.6.0 2018-09-11
  - Added support for QCAS form types.
  - Calculate total values for QCAS to be sent downstream.
  - Replace all negative numbers with a string of 11 characters containing only 9's in pck file.
    
### 3.5.2 2018-08-09
  - Fix error in turnover rounding

### 3.5.1 2018-07-12
  - Add turnover question to 009.0167 (MBS)

### 3.5.0 2018-06-28
  - Change mbs transformer q_code from d40 to d49

### 3.4.0 2018-05-21
  - Add MBS Transformer

### 3.3.0 2018-03-26
  - Impute zero values for MWSS gross pay breakdown questions when the respondent has confirmed they are zero

### 3.2.0 2018-03-22
  - Impute zero values for RSI and QBS total questions when the respondent has confirmed they are zero

### 3.1.0 2018-02-20
  - Changes to the MWSS survey.  Question text and format changes in the schema. Also, questions beginning 90 and 190 aggregate to 90 in the downstream file.  Questions 91-97 and 191-197 no longer need to be included in the aggregation.

### 3.0.0 2018-01-04
  - Added the original Json data in the zip file sent to the ftp server
  - refactored cs_fromatter to use named parameters instead of **kwargs for clarity
  - Add /info healthcheck endpoint
  - Remove reference to ftp server

### 2.13.0 2017-11-27
  - Bug fix - nothing displayed after the decimal point in decimal responses in image files
  - Move transformers to be memory based instead of file based
  - Initial files for move to cloudfoundry

### 2.12.0 2017-11-09
  - Fix incorrect index date time

### 2.11.0 2017-11-01
  - Removed unchanging configurable variables.
  - Add all service configurations to config file
  - Correct the spelling error in RSI image
  - Rename FTP_HOST to FTP_PATH
  - Improve test output and implemented Pytest

### 2.10.0 2017-10-18
  - Refactored variable names for MWSS transformer

### 2.9.0 2017-10-16
  - Support decimal values in MWSS Surveys ( survey_id 005 )

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
