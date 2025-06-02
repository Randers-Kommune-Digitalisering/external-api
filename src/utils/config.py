import os
from dotenv import load_dotenv


# loads .env file, will not overide already set enviroment variables (will do nothing when testing, building and deploying)
load_dotenv()


DEBUG = os.getenv('DEBUG', 'False') in ['True', 'true']
PORT = os.getenv('PORT', '8080')
POD_NAME = os.getenv('POD_NAME', 'pod_name_not_set')

# DB_USER = os.environ["DB_USER"].strip()
# DB_PASS = os.environ["DB_PASS"].strip()
# DB_HOST = os.environ["DB_HOST"].strip()
# DB_PORT = os.environ["DB_PORT"].strip()
# DB_DATABASE = os.environ["DB_DATABASE"].strip()
