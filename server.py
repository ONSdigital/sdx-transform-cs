from transform import __version__
from transform import app, settings
import logging
import os
import sys


def bad_globals(module):
    g = {k: v for k, v in vars(module).items() if not k.startswith("_") and k.isupper()}
    return [k for k, v in g.items() if v is None]


if __name__ == '__main__':
    # Startup
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    logging.info("Starting server: version='{}'".format(__version__))
    bad = bad_globals(settings)
    for g in bad:
        logging.error("{0} missing from environment.".format(g))
    if bad:
        sys.exit(1)

    port = int(os.getenv("PORT"))
    app.run(debug=True, host='0.0.0.0', port=port)
