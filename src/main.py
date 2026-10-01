from flask import Flask
from flask_migrate import Migrate
from healthcheck import HealthCheck
from prometheus_client import generate_latest

from api.skole_ad import skole_ad_bp
from api.keycloak import keycloak_bp
from api.gis import gis_bp
from api.nexus import nexus_bp
from extensions import db
from utils.config import DEBUG, PORT, \
    META_DB_HOST, META_DB_PORT, META_DB_NAME, META_DB_USER, META_DB_PASS, \
    GIS_DB_HOST, GIS_DB_PORT, GIS_DB_NAME, GIS_DB_USER, GIS_DB_PASS, XFLOW_NEXUS_DB_SCHEMA


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{META_DB_USER}:{META_DB_PASS}@{META_DB_HOST}:{META_DB_PORT}/{META_DB_NAME}"
    app.config["SQLALCHEMY_BINDS"] = {
        "gis": f"postgresql://{GIS_DB_USER}:{GIS_DB_PASS}@{GIS_DB_HOST}:{GIS_DB_PORT}/{GIS_DB_NAME}"
    }
    db.init_app(app)
    Migrate(app, db, include_schemas=True, version_table_schema=XFLOW_NEXUS_DB_SCHEMA)

    health = HealthCheck()
    app.add_url_rule('/healthz', 'healthcheck', view_func=lambda: health.run())
    app.add_url_rule('/metrics', 'metrics', view_func=generate_latest)
    app.register_blueprint(skole_ad_bp)
    # Route for backward compatibility with previous endpoint name
    app.add_url_rule(
        '/skole-ad-file',
        endpoint='skole_ad_file_root',
        view_func=app.view_functions['skole-ad.upload_person_file'],
        methods=['POST']
    )
    app.register_blueprint(keycloak_bp)
    app.register_blueprint(gis_bp)
    app.register_blueprint(nexus_bp)
    return app


app = create_app()


if __name__ == '__main__':  # pragma: no cover
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
