#!/usr/bin/env python3

import connexion
import logging

#from flask_swagger_ui import get_swaggerui_blueprint
from logging.handlers import RotatingFileHandler
from logging import Formatter
from openapi_server import encoder

def main():
    handler = RotatingFileHandler('tagbase.log', maxBytes=10000, backupCount=10)
    handler.setLevel(logging.INFO)
    handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))

    logger = logging.getLogger('werkzeug')
    logger.addHandler(handler)
    app = connexion.FlaskApp(__name__, specification_dir='./openapi/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('openapi.yaml', arguments={'title': 'Tagbase API'})

    ## Uncomment the following code if you wish the swagger ui to be available at
    ## http://localhost:5433/api/docs/

    # # flask-swagger-ui configuration
    # SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
    # API_URL = 'http://localhost:5433/v1/tagbase/swagger.json'  # Our API url (can of course be a local resource)

    # # Call factory function to create our blueprint
    # swaggerui_blueprint = get_swaggerui_blueprint(
    #     SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    #     API_URL,
    #     config={  # Swagger UI config overrides
    #         'app_name': "Tagbase API"
    #     },
    #     # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #     #    'clientId': "your-client-id",
    #     #    'clientSecret': "your-client-secret-if-required",
    #     #    'realm': "your-realms",
    #     #    'appName': "your-app-name",
    #     #    'scopeSeparator': " ",
    #     #    'additionalQueryStringParams': {'test': "hello"}
    #     # }
    # )

    # # Register blueprint at URL
    # # (URL must match the one given to factory function above)
    # app.app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    app.run(port=5433, host='0.0.0.0', threaded=True)

if __name__ == '__main__':
    main()
