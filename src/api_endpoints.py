import os
import logging
import json
import glob
import requests
import pandas as pd

from datetime import datetime
from urllib.parse import urlparse
from sqlalchemy import text
from flask import Blueprint, Response, request, jsonify

from nexus.client import NexusClient
from utils.openid_integration import AuthorizationHelper
from utils.database import DatabaseClient
from utils.token_provider import BearerAuth
from utils.files import danish_to_ascii, decode_base64_file
from utils.config import SKOLE_AD_DB_HOST, SKOLE_AD_DB_USER, SKOLE_AD_DB_PASS, SKOLE_AD_DB_NAME, SKOLE_AD_DB_SCHEMA, \
    KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_AUDIENCE, KEYCLOAK_USER_ADMIN_CLIENT_ID, KEYCLOAK_USER_ADMIN_CLIENT_SECRET, \
    GIS_DB_USER, GIS_DB_PASS, GIS_DB_HOST, GIS_DB_PORT, GIS_DB_NAME, GIS_DB_SCHEMA, NEXUS_FORMS, XFLOW_API_KEY, \
    NEXUS_URL, NEXUS_TOKEN_URL, NEXUS_CLIENT_ID, NEXUS_CLIENT_SECRET


logger = logging.getLogger(__name__)
api_endpoints = Blueprint('api', __name__)
ah = AuthorizationHelper(KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_AUDIENCE)
db_client_meta = DatabaseClient(db_type="postgresql", database=SKOLE_AD_DB_NAME, username=SKOLE_AD_DB_USER, password=SKOLE_AD_DB_PASS, host=SKOLE_AD_DB_HOST)
db_client_gis = DatabaseClient(db_type="postgresql", database=GIS_DB_NAME, username=GIS_DB_USER, password=GIS_DB_PASS, host=GIS_DB_HOST, port=GIS_DB_PORT)


@api_endpoints.route('/skole-ad-file', methods=['GET', 'POST'])
@ah.authorization
def skole_ad_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return Response('No file part in the request', status=400)

        file = request.files['file']
        if file.filename == '':
            return Response('No selected file', status=400)

        added_to_db = False
        saved_to_disk = False

        try:
            file.save(file.filename)
            saved_to_disk = True
        except Exception as e:
            logger.error(f"Failed to save file {file.filename}: {e}")

        filename = file.filename

        try:
            with db_client_meta.get_connection() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SKOLE_AD_DB_SCHEMA}"))
                conn.commit()
                file_ext = os.path.splitext(filename)[1].lower()

                if file_ext == '.csv':
                    file.seek(0)
                    df = pd.read_csv(file.stream, sep=';', encoding='cp1252')
                elif file_ext in ['.xls', '.xlsx']:
                    df = pd.read_excel(file)
                else:
                    raise ValueError(f"Unsupported file type: {file_ext}")

                df['updated'] = datetime.now()

                df.to_sql('person', con=conn, schema=SKOLE_AD_DB_SCHEMA, if_exists='replace', index=False)
                added_to_db = True
                conn.commit()
                logger.info(f"File {filename} processed and added to the database.")
        except Exception as e:
            logger.error(f"Failed to add file {filename} to database: {e}")

        if added_to_db and saved_to_disk:
            return Response('File saved successfully', status=200)
        elif added_to_db:
            return Response('File only added to the database', status=200)
        elif saved_to_disk:
            return Response('File only saved to disk', status=200)
        else:
            logger.error("Failed to save file or add to database.")
            return Response('Failed to save file', status=500)
    else:
        filename = request.args.get('filename')
        if not filename:
            files = [os.path.basename(f) for f in glob.glob("*.csv") + glob.glob("*.xls") + glob.glob("*.xlsx")]
            return jsonify({'files': files}), 200
        try:
            return Response(open(filename, 'rb').read(), mimetype='application/octet-stream')
        except FileNotFoundError:
            return Response('File not found', status=404)
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            return Response('Internal server error', status=500)


@api_endpoints.route('/add-user-to-keycloak-group', methods=['POST'])
@ah.authorization
def add_user_to_group():
    data = request.get_json()
    if not data or 'email' not in data or 'group' not in data:
        return Response('Missing required keys: email and group', status=400)

    keycloak_url = KEYCLOAK_URL
    parsed = urlparse(keycloak_url)
    if not parsed.scheme:
        keycloak_url = "https://" + keycloak_url.lstrip("/")
    if not keycloak_url.endswith("/"):
        keycloak_url += "/"

    session = requests.Session()
    session.auth = BearerAuth(
        token_url=f"{keycloak_url}auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
        client_id=KEYCLOAK_USER_ADMIN_CLIENT_ID,
        client_secret=KEYCLOAK_USER_ADMIN_CLIENT_SECRET
    )

    user_id = session.get(
        url=f"{keycloak_url}auth/admin/realms/{KEYCLOAK_REALM}/users",
        params={'email': data['email']}
    ).json()

    group_id = session.get(
        url=f"{keycloak_url}auth/admin/realms/{KEYCLOAK_REALM}/groups",
        params={'search': data['group']}
    ).json()

    user_added = False
    message = "Der er desværre sket en fejl i forbindelse med tildeling af rettigheder. For at få rettet op på dette bedes I venligst videresende denne mail til digitalisering@randers.dk."
    error = None
    if len(user_id) != 1 or len(group_id) != 1:
        logger.error('User or group not found or multiple matches found')
        error = 'User or group not found or multiple matches found'
    else:
        try:
            res = session.put(
                url=f"{keycloak_url}auth/admin/realms/{KEYCLOAK_REALM}/users/{user_id[0]['id']}/groups/{group_id[0]['id']}"
            )
            res.raise_for_status()
            user_added = True
            message = "Du har nu fået tildelt de ønskede rettigheder."
        except Exception as e:
            logger.error(f"Failed to add user to group: {e}")
            error = str(e)
    return jsonify({"user_added": user_added, "message": message, "error": error}), 200


@api_endpoints.route('/add-gis-raagereder-data-to-db', methods=['POST'])
@ah.authorization
def add_gis_raagereder_data_to_db():
    data = request.get_json()
    if not data or 'geojson' not in data:
        return Response('Missing required key geojson', status=400)
    try:
        geojson = json.loads(data['geojson'])
        with db_client_gis.get_connection() as conn:
            id_sql = f"SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM {GIS_DB_SCHEMA}.aktive_raagereder_rk_all"
            result = conn.execute(text(id_sql))
            next_id = result.scalar() if result else 1
            for feature in geojson['features']:
                geom_json = json.dumps(feature['geometry'])
                sql = (
                    f"INSERT INTO {GIS_DB_SCHEMA}.aktive_raagereder_rk_all (wkb_geometry, oprettet_dato, geojson, id) "
                    f"VALUES (ST_SetSRID(ST_GeomFromGeoJSON('{geom_json}'), 25832), :oprettet_dato, :geojson, :id);"
                )
                oprettet_dato = datetime.now()
                conn.execute(text(sql), {'oprettet_dato': oprettet_dato, 'geojson': geom_json, 'id': next_id})
            conn.commit()
            logger.info("GIS raagereder data added to database.")
    except Exception as e:
        logger.error(f"ERROR adding GIS raagereder data to database: {e}")
        return Response('Failed to add GIS raagereder data to database', status=500)
    return jsonify({"message": "GIS raagereder data modtaget"}), 200


@api_endpoints.route('/nexus', methods=['POST'])
@ah.authorization
def post_form_data_to_nexus():
    if not request.is_json:
        return Response('Request body must be JSON', status=400)

    data = request.get_json()
    required_keys = {"cpr", "formName", "formData", "attachments", "date"}
    missing_keys = sorted(required_keys - set(data or {}))
    if missing_keys:
        return Response(f"Missing required keys: {', '.join(missing_keys)}", status=400)

    # When xFlow attaches a 'blanket' to an email it replaces spaces with underscores and removes hyphens, as well as transforms Danish characters. So the pattern is matched here.
    form_name = danish_to_ascii(data['formName'].replace(" ", "_").replace("-", ""))
    if form_name not in NEXUS_FORMS:
        return Response(f"Form name '{form_name}' is not allowed", status=400)

    cpr = data["cpr"]
    try:
        form_date = datetime.fromisoformat(data["date"].replace("Z", "+00:00")).date()
    except (AttributeError, TypeError, ValueError):
        return Response('Invalid date format; expected ISO 8601 date or datetime', status=400)

    # TODO: Remove when going to PROD - for new ignore all requests except for the test CPR number
    if cpr != "111131-1112":
        return jsonify({"msg": "not adding to Nexus"}), 200

    client = NexusClient(base_url=NEXUS_URL, token_url=NEXUS_TOKEN_URL, client_id=NEXUS_CLIENT_ID, client_secret=NEXUS_CLIENT_SECRET)
    patient_data = client.get_patient_data(cpr=cpr)

    docs: list[dict] = []

    if form_name == NEXUS_FORMS[0]:  # Personligt_hjaelpemiddel__Kopi__TEST
        device_name = data["text0"]

        form_doc_name = f"Ansøgning {device_name}" if device_name.replace(" ", "").strip() else "Ansøgning Personlig hjælpemiddel"
        attachment_doc_name = f"Ansøgning Bilag {device_name}" if device_name.replace(" ", "").strip() else "Ansøgning Bilag Personlig hjælpemiddel"

        request_file_bytes, request_mime_type = decode_base64_file(data["formData"])
        request_file_name = f"{form_name}.pdf"
        docs.append({
            "name": form_doc_name,
            "file_name": request_file_name,
            "file_bytes": request_file_bytes,
            "mime_type": request_mime_type
        })

        with requests.Session() as attachment_session:
            attachment_session.headers.update({"publicApiToken": XFLOW_API_KEY})

            for attachment in data["attachments"]:
                attachment_file_name = attachment.get("title")
                attachment_mime_type = attachment.get("mimeType")
                attachment_response = attachment_session.get(attachment.get("url"))
                attachment_response.raise_for_status()
                attachment_file_bytes = attachment_response.content
                docs.append({
                    "name": attachment_doc_name,
                    "file_name": attachment_file_name,
                    "file_bytes": attachment_file_bytes,
                    "mime_type": attachment_mime_type
                })

        can_collect_data: bool = data.get("canCollectData", False) is True

        for_another = data.get("forAnother", False)

        if for_another:
            on_behalf_of_relation = "Pårørende" if any(value in (data.get("relation") or "").lower() for value in ("forælder", "barn")) else "Andre" if "anden relation" in (data.get("relation") or "").lower() else None
            on_behalf_of_name = data["text1"] if data["text1"] else None
            on_behalf_of_phone = data["text2"] if data["text2"] else None
        else:
            on_behalf_of_relation = None
            on_behalf_of_name = None
            on_behalf_of_phone = None

        for doc in docs:
            client.add_assistive_device_document(
                patient_data=patient_data,
                name=doc["name"],
                file_name=doc["file_name"],
                file_bytes=doc["file_bytes"],
                mime_type=doc["mime_type"]
            )

        formatted_form_date = form_date.strftime("%d-%m-%Y")
        reason_text = f"{formatted_form_date} - Ansøgning om {device_name}" if device_name.replace(" ", "").strip() else f"{formatted_form_date} - Ansøgning om Personlig hjælpemiddel"
        if len(docs) > 1:
            reason_text += " med bilag"

        client.create_assistive_device_communication_form(
            patient_data=patient_data,
            application_date=form_date,
            application_reason=reason_text,
            communication_source="Borger" if not for_another else on_behalf_of_relation,
            device=device_name,
            optional_contact_info=f"{on_behalf_of_relation}\n{on_behalf_of_name}\n{on_behalf_of_phone}" if for_another and on_behalf_of_relation else None,
            patient_understands=True,
            can_information_be_obtained=can_collect_data
        )

    return jsonify({"msg": "added to Nexus"}), 200
