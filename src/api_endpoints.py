import os
import logging
import pandas as pd

from sqlalchemy import text
from flask import Blueprint, Response, request, jsonify

from utils.openid_integration import AuthorizationHelper
from utils.database import DatabaseClient
from utils.config import SKOLE_AD_DB_HOST, SKOLE_AD_DB_USER, SKOLE_AD_DB_PASS, SKOLE_AD_DB_NAME, SKOLE_AD_DB_SCHEMA, KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_AUDIENCE
from datetime import datetime
import glob

logger = logging.getLogger(__name__)
api_endpoints = Blueprint('api', __name__)
ah = AuthorizationHelper(KEYCLOAK_URL, KEYCLOAK_REALM, KEYCLOAK_AUDIENCE)
db_client = DatabaseClient(db_type="postgresql", database=SKOLE_AD_DB_NAME, username=SKOLE_AD_DB_USER, password=SKOLE_AD_DB_PASS, host=SKOLE_AD_DB_HOST)


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

        try:
            with db_client.get_connection() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SKOLE_AD_DB_SCHEMA}"))
                conn.commit()
                filename = file.filename
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
