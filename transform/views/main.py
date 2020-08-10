import json
import logging
import os.path
from json import JSONDecodeError

from flask import request, send_file, jsonify
from jinja2 import Environment, PackageLoader
from structlog import wrap_logger

from transform import app, settings
from transform.transformers import ImageTransformer
from transform.transformers.survey import MissingSurveyException, Survey
from transform.transformers.transform_selector import get_transformer
from transform.views.logger_config import logger_initial_config

env = Environment(loader=PackageLoader('transform', 'templates'))

logger_initial_config(service_name='sdx-transform-cs',
                      log_level=settings.LOGGING_LEVEL)
logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(400)
def errorhandler_400(e):
    return client_error(repr(e))


def client_error(error=None):
    logger.error("Client error", error=error)
    message = {
        'status': 400,
        'message': error,
        'uri': request.url,
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.errorhandler(500)
def server_error(error=None):
    logger.error("Server error", error=repr(error))
    message = {
        'status': 500,
        'message': "Internal server error: " + repr(error),
    }
    resp = jsonify(message)
    resp.status_code = 500

    return resp


def get_survey(survey_response):
    """
    Takes the survey and returns the file that represents the image of that survey from the
    /transform/surveys directory.

    :param survey_response: The JSON response passed to us from EQ
    :raises KeyError: Raised if survey_id or instrument_id is missing
    :raises IOError: Raised if file cannot be opened
    :raises JSONDecodeError:  Raised if returned file isn't valid JSON
    :raises UnicodeDecodeError:
    """
    try:
        tx_id = survey_response.get("tx_id", "N/A")
        form_id = survey_response['collection']['instrument_id']
        survey_id = survey_response['survey_id']
    except KeyError:
        logger.exception("Missing instrument_id or survey_id", tx_id=tx_id)
        return None

    try:
        survey_file_name = f"{survey_id}.{form_id}.json"
        file_path = os.path.join(".", "transform", "surveys", survey_file_name)
        logger.info("Opening file", file=file_path, tx_id=tx_id)
        with open(file_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    except (OSError, UnicodeDecodeError):
        logger.exception("Error opening file", file=file_path, tx_id=tx_id)
        return None
    except JSONDecodeError:
        logger.exception("File is not valid JSON", file=file_path, tx_id=tx_id)
        return None


@app.route('/images', methods=['POST'])
def render_images():

    survey_response = request.get_json(force=True)

    ids = Survey.identifiers(survey_response)
    survey = Survey.load_survey(ids)

    if not survey:
        return client_error("IMAGES:Unsupported survey/instrument id")

    transformer = ImageTransformer(logger, survey, survey_response)

    try:
        zipfile = transformer.get_zipped_images()
    except IOError as e:
        return client_error("IMAGES:Could not create zip buffer: {0}".format(repr(e)))
    except Exception as e:
        logger.exception("IMAGES: Error {0}".format(repr(e)))
        return server_error(e)
    logger.info("IMAGES:SUCCESS")

    return send_file(zipfile.in_memory_zip, mimetype='application/zip', add_etags=False)


@app.route('/common-software', methods=['POST'])
@app.route('/common-software/<sequence_no>', methods=['POST'])
def common_software(sequence_no=1000):
    survey_response = request.get_json(force=True)

    if sequence_no:
        sequence_no = int(sequence_no)

    try:
        transformer = get_transformer(survey_response, sequence_no)
        zip_file = transformer.get_zip()
        logger.info("CS:SUCCESS")
        return send_file(zip_file, mimetype='application/zip', add_etags=False)

    except MissingSurveyException:
        return client_error("Unsupported survey/instrument id")

    except Exception as e:
        tx_id = survey_response.get("tx_id")
        survey_id = survey_response.get("survey_id")
        logger.exception("CS:could not create files for survey", survey_id=survey_id, tx_id=tx_id)
        return server_error(e)


@app.route('/cora', methods=['POST'])
@app.route('/cora/<sequence_no>', methods=['POST'])
def cora(sequence_no=1000):
    survey_response = request.get_json(force=True)

    if sequence_no:
        sequence_no = int(sequence_no)

    try:
        transformer = get_transformer(survey_response, sequence_no)
        zip_file = transformer.get_zip()
        logger.info("CORA:SUCCESS")
        return send_file(zip_file, mimetype='application/zip', add_etags=False)

    except MissingSurveyException:
        return client_error("Unsupported survey/instrument id")

    except Exception as e:
        tx_id = survey_response.get("tx_id")
        survey_id = survey_response.get("survey_id")
        logger.exception("CORA:could not create files for survey", survey_id=survey_id, tx_id=tx_id)
        return server_error(e)


@app.route('/cord', methods=['POST'])
@app.route('/cord/<sequence_no>', methods=['POST'])
def cord(sequence_no=1000):
    survey_response = request.get_json(force=True)

    if sequence_no:
        sequence_no = int(sequence_no)

    try:
        transformer = get_transformer(survey_response, sequence_no)
        zip_file = transformer.get_zip()
        logger.info("CORD:SUCCESS")
        return send_file(zip_file, mimetype='application/zip', add_etags=False)

    except MissingSurveyException:
        return client_error("Unsupported survey/instrument id")

    except Exception as e:
        tx_id = survey_response.get("tx_id")
        survey_id = survey_response.get("survey_id")
        logger.exception("CORD:could not create files for survey", survey_id=survey_id, tx_id=tx_id)
        return server_error(e)


@app.route('/info', methods=['GET'])
@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """A simple endpoint that reports the health of the application"""
    return jsonify({'status': 'OK'})


@app.route('/transform', methods=['POST'])
@app.route('/transform/<sequence_no>', methods=['POST'])
def transform(sequence_no=1000):
    survey_response = request.get_json(force=True)

    if sequence_no:
        sequence_no = int(sequence_no)

    try:
        transformer = get_transformer(survey_response, sequence_no)
        zip_file = transformer.get_zip()
        logger.info("TRANSFORM:SUCCESS")
        return send_file(zip_file, mimetype='application/zip', add_etags=False)

    except MissingSurveyException:
        return client_error("Unsupported survey/instrument id")

    except Exception as e:
        tx_id = survey_response.get("tx_id")
        survey_id = survey_response.get("survey_id")
        logger.exception("TRANSFORM:could not create files for survey", survey_id=survey_id, tx_id=tx_id)
        return server_error(e)
