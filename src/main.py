from flask import Flask
from healthcheck import HealthCheck
from prometheus_client import generate_latest

from utils.logging import set_logging_configuration
from utils.config import DEBUG, PORT
from api_endpoints import api_endpoints


set_logging_configuration()


def create_app():
    app = Flask(__name__)
    health = HealthCheck()
    app.add_url_rule('/healthz', 'healthcheck', view_func=lambda: health.run())
    app.add_url_rule('/metrics', 'metrics', view_func=generate_latest)
    app.register_blueprint(api_endpoints)
    return app


app = create_app()


if __name__ == '__main__':  # pragma: no cover
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
