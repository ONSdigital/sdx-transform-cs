import structlog
from transform import app
from gunicorn.app.base import BaseApplication

logger = structlog.get_logger()


class Server(BaseApplication):

    def __init__(self, application, options_dict=None):
        self.options = options_dict or {}
        self.application = application
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == '__main__':
    logger.info('Starting SDX Deliver')
    options = {
        'bind': '%s:%s' % ('0.0.0.0', '5000'),
        'workers': 2,
    }
    Server(app, options).run()
