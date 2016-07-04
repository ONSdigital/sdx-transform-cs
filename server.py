import settings
from transform import app
import logging
import logging.handlers


if __name__ == '__main__':
    # Startup
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    handler = logging.handlers.RotatingFileHandler(settings.LOGGING_LOCATION, maxBytes=20000, backupCount=5)
    handler.setFormatter(logging.Formatter(settings.LOGGING_FORMAT))
    log = logging.getLogger('werkzeug')
    log.addHandler(handler)
    app.logger.addHandler(handler)
    app.run(debug=True, host='0.0.0.0')
