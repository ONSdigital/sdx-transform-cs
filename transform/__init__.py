from flask import Flask

app = Flask(__name__)

import transform.views.test_views  # noqa
import transform.views.main  # noqa
