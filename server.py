import settings
from transform import app
import logging
import logging.handlers
import os


if __name__ == '__main__':
    # Startup
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
