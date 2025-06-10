import os
from dotenv import load_dotenv


# loads .env file, will not overide already set enviroment variables (will do nothing when testing, building and deploying)
load_dotenv()


DEBUG = os.getenv('DEBUG', 'False') in ['True', 'true']
PORT = os.getenv('PORT', '8080')
POD_NAME = os.getenv('POD_NAME', 'pod_name_not_set')

KEYCLOAK_URL = os.environ["KEYCLOAK_URL"].strip()
KEYCLOAK_REALM = os.environ["KEYCLOAK_REALM"].strip()
KEYCLOAK_AUDIENCE = os.environ["KEYCLOAK_AUDIENCE"].strip()

SKOLE_AD_DB_USER = os.environ["SKOLE_AD_DB_USER"].strip()
SKOLE_AD_DB_PASS = os.environ["SKOLE_AD_DB_PASS"].strip()
SKOLE_AD_DB_HOST = os.environ["SKOLE_AD_DB_HOST"].strip()
SKOLE_AD_DB_PORT = os.environ["SKOLE_AD_DB_PORT"].strip()
SKOLE_AD_DB_NAME = os.environ["SKOLE_AD_DB_NAME"].strip()
SKOLE_AD_DB_SCHEMA = "skolead"
