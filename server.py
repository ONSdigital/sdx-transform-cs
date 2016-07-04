import settings
from settings import MakeFileHandler
from transform import app
import logging
from logging import Formatter


if __name__ == '__main__':
    # Startup
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    handler = MakeFileHandler(settings.LOGGING_LOCATION, maxBytes=20000, backupCount=5)
    handler.setFormatter(Formatter(settings.LOGGING_FORMAT))
    app.logger.addHandler(handler)
    app.run(debug=True, host='0.0.0.0')
