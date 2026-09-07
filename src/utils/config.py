import os
from dotenv import load_dotenv


# loads .env file, will not overide already set enviroment variables (will do nothing when testing, building and deploying)
load_dotenv()


DEBUG = os.getenv("DEBUG", "False").strip().lower() in ["true", "1", "t", "y", "yes"]
PORT = os.getenv("PORT", "8080")
POD_NAME = os.getenv("POD_NAME", "pod_name_not_set")

KEYCLOAK_URL = os.environ["KEYCLOAK_URL"].strip()
KEYCLOAK_REALM = os.environ["KEYCLOAK_REALM"].strip()
KEYCLOAK_AUDIENCE = os.environ["KEYCLOAK_AUDIENCE"].strip()

KEYCLOAK_USER_ADMIN_CLIENT_ID = os.environ["KEYCLOAK_USER_ADMIN_CLIENT_ID"].strip()
KEYCLOAK_USER_ADMIN_CLIENT_SECRET = os.environ["KEYCLOAK_USER_ADMIN_CLIENT_SECRET"].strip()

META_DB_USER = os.environ["META_DB_USER"].strip()
META_DB_PASS = os.environ["META_DB_PASS"].strip()
META_DB_HOST = os.environ["META_DB_HOST"].strip()
META_DB_PORT = os.environ["META_DB_PORT"].strip()
META_DB_NAME = os.environ["META_DB_NAME"].strip()

SKOLE_AD_DB_SCHEMA = "skolead"
SKOLE_AD_DB_TABLE = "person"

XFLOW_NEXUS_DB_SCHEMA = "xflow_nexus"
XFLOW_NEXUS_HJAELPEMIDDEL_DB_TABLE = XFLOW_NEXUS_DB_SCHEMA

XFLOW_API_KEY = os.environ["XFLOW_API_KEY"].strip()

GIS_DB_USER = os.environ["GIS_DB_USER"].strip()
GIS_DB_PASS = os.environ["GIS_DB_PASS"].strip()
GIS_DB_HOST = os.environ["GIS_DB_HOST"].strip()
GIS_DB_PORT = os.environ["GIS_DB_PORT"].strip()
GIS_DB_NAME = os.environ["GIS_DB_NAME"].strip()
GIS_DB_SCHEMA = "s34_xflow"
GIS_DB_RAAGEREDER_TABLE = "aktive_raagereder_rk_all"

NEXUS_URL = os.environ["NEXUS_URL"].strip()
NEXUS_TOKEN_URL = os.environ["NEXUS_TOKEN_URL"].strip()
NEXUS_CLIENT_ID = os.environ["NEXUS_CLIENT_ID"].strip()
NEXUS_CLIENT_SECRET = os.environ["NEXUS_CLIENT_SECRET"].strip()
