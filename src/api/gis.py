import json
import logging

from datetime import datetime
from sqlalchemy import text
from flask import Blueprint, Response, request, jsonify

from extensions import db
from utils.openid_integration import authorization_helper
from utils.config import GIS_DB_SCHEMA, GIS_DB_RAAGEREDER_TABLE

logger = logging.getLogger(__name__)
gis_bp = Blueprint("gis", __name__, url_prefix="/gis")


@gis_bp.post("/raagereder")
@authorization_helper.authorization
def raagereder():
    data = request.get_json()
    if not data or 'geojson' not in data:
        return Response('Missing required key geojson', status=400)
    try:
        geojson = data['geojson']
        if isinstance(geojson, str):
            geojson = json.loads(geojson)

        gis_engine = db.engines['gis']

        with gis_engine.begin() as conn:
            id_sql = f"SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM {GIS_DB_SCHEMA}.aktive_raagereder_rk_all"
            result = conn.execute(text(id_sql))
            next_id = result.scalar() if result else 1

            sql = text(
                f"INSERT INTO {GIS_DB_SCHEMA}.{GIS_DB_RAAGEREDER_TABLE} (wkb_geometry, oprettet_dato, geojson, id) "
                f"VALUES (ST_SetSRID(ST_GeomFromGeoJSON(:geom_json), 25832), :oprettet_dato, :geojson, :id);"
            )

            for feature in geojson['features']:
                geom_json = json.dumps(feature['geometry'])
                oprettet_dato = datetime.now()

                conn.execute(sql, {
                    'geom_json': geom_json,
                    'oprettet_dato': oprettet_dato,
                    'geojson': geom_json,
                    'id': next_id
                })
            logger.info("GIS raagereder data added to database.")
    except Exception as e:
        logger.error(f"ERROR adding GIS raagereder data to database: {e}")
        return Response('Failed to add GIS raagereder data to database', status=500)
    return jsonify({"message": "GIS raagereder data modtaget"}), 200
