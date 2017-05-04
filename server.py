from transform import __version__
from transform import app, settings
import logging
import os


def check_default_env_vars():

    env_vars = ["SDX_SEQUENCE_URL", "FTP_PATH", "SDX_FTP_IMAGES_PATH", "SDX_FTP_DATA_PATH", "SDX_FTP_RECEIPT_PATH"]

    for i in env_vars:
        if os.getenv(i) is None:
            logger.error("No ", i, "env var supplied")
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
