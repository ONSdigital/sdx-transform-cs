import logging
import os

from sdx.common.logger_config import logger_initial_config

from transform import __version__
from transform import app, settings

logger_initial_config(service_name='sdx-transform-cs',
                      log_level=settings.LOGGING_LEVEL)


if __name__ == '__main__':
    # Startup
    logging.info("Starting server: version='{}'".format(__version__))
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
