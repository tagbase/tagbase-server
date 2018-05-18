#!/usr/bin/env python3

import connexion
import logging
from logging.handlers import RotatingFileHandler
from logging import Formatter
from swagger_server import encoder

def main():
    handler = RotatingFileHandler('tagbase.log', maxBytes=10000, backupCount=10)
    handler.setLevel(logging.INFO)
    handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))

    logger = logging.getLogger('werkzeug')
    logger.addHandler(handler)
    app = connexion.FlaskApp(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Tagbase API'})
    app.run(port=5433, host='localhost', threaded=True)

if __name__ == '__main__':
    main()
