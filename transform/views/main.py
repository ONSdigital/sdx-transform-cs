import threading

import structlog
from flask import request, send_file, jsonify
from jinja2 import Environment, PackageLoader
from structlog.contextvars import bind_contextvars

from transform import app
from transform.transformers.survey import MissingSurveyException, MissingIdsException
from transform.transformers.transform_selector import get_transformer

env = Environment(loader=PackageLoader('transform', 'templates'))

logger = structlog.get_logger()


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


@app.route('/common-software', methods=['POST'])
@app.route('/common-software/<sequence_no>', methods=['POST'])
@app.route('/cora', methods=['POST'])
@app.route('/cora/<sequence_no>', methods=['POST'])
@app.route('/cord', methods=['POST'])
@app.route('/cord/<sequence_no>', methods=['POST'])
@app.route('/transform', methods=['POST'])
@app.route('/transform/<sequence_no>', methods=['POST'])
def transform(sequence_no=1000):
    survey_response = request.get_json(force=True)
    tx_id = survey_response.get("tx_id")
    bind_contextvars(app="sdx-transform")
    bind_contextvars(tx_id=tx_id)
    bind_contextvars(thread=threading.currentThread().getName())

    if sequence_no:
        sequence_no = int(sequence_no)

    try:
        transformer = get_transformer(survey_response, sequence_no)
        zip_file = transformer.get_zip()
        logger.info("Transformation was a success, returning zip file")
        return send_file(zip_file, mimetype='application/zip', add_etags=False)

    except MissingIdsException as e:
        return client_error(str(e))

    except MissingSurveyException:
        return client_error("Unsupported survey/instrument id")

    except Exception as e:
        tx_id = survey_response.get("tx_id")
        survey_id = survey_response.get("survey_id")
        logger.exception("TRANSFORM:could not create files for survey", survey_id=survey_id, tx_id=tx_id)
        return server_error(e)


@app.route('/info', methods=['GET'])
@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """A simple endpoint that reports the health of the application"""
    return jsonify({'status': 'OK'})
