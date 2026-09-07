import os
import pandas as pd

from datetime import datetime
from flask import Blueprint, Response, request

from extensions import db
from utils.openid_integration import authorization_helper
from utils.config import SKOLE_AD_DB_SCHEMA, SKOLE_AD_DB_TABLE

skole_ad_bp = Blueprint("skole-ad", __name__, url_prefix="/skole-ad")


@skole_ad_bp.post('/upload-person-file')
@authorization_helper.authorization
def upload_person_file():
    if 'file' not in request.files:
        return Response('No file part in the request', status=400)

    file = request.files['file']
    if file.filename == '':
        return Response('No selected file', status=400)

    try:
        with db.engine.begin() as conn:
            file_ext = os.path.splitext(file.filename)[1].lower()

            if file_ext == '.csv':
                file.seek(0)
                df = pd.read_csv(file.stream, sep=';', encoding='cp1252')
            elif file_ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file)
            else:
                return Response(f"Unsupported file type: {file_ext}", status=400)

            df['updated'] = datetime.now()

            df.to_sql(SKOLE_AD_DB_TABLE, con=conn, schema=SKOLE_AD_DB_SCHEMA, if_exists='replace', index=False)

            return Response(f"File {file.filename} processed and added to the database", status=200)
    except Exception as e:
        return Response(f"Failed to add file {file.filename} to database: {str(e)}", status=500)
