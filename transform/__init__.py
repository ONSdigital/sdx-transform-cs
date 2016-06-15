from flask import Flask
import settings

app = Flask(__name__)

app.config['WRITE_BATCH_HEADER'] = settings.WRITE_BATCH_HEADER

import transform.views.test_views