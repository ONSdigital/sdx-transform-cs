from transform import __version__
from transform import app, settings
import logging
import os


def _get_value(key):
    value = os.getenv(key)
    if not value:
        raise ValueError("No value set for " + key)


def check_default_env_vars():

    env_vars = ["SDX_SEQUENCE_URL", "FTP_PATH", "SDX_FTP_IMAGES_PATH", "SDX_FTP_DATA_PATH", "SDX_FTP_RECEIPT_PATH"]

    missing_env_var = False
    
    for i in env_vars:
        try:
            _get_value(i)
        except ValueError as e:
            logger.error("Unable to start service", error=e)
            missing_env_var = True

    if missing_env_var is True:
        sys.exit(1)


if __name__ == '__main__':
    # Startup
    check_default_env_vars()
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    logging.info("Starting server: version='{}'".format(__version__))
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
