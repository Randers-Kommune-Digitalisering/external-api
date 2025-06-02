# Python app template projekt
Template til nye Python app projekter.
Projekt indeholder en bare bone Flask app
* Health endpoint
* Prometheus metrics endpoint
* Test job endpoint
* Unit test af de 3 endpoints

# Brug af python-app-template
1. Klik på "use this template" og vælg "create a new repository"
2. Udfyld skærmbillede med information om den nye service
3. Åbn dit nye git projekt

# Nyt Python app projekt
Nedenstående relaterer sig til et nyt Python app projekt der er baseret på denne template.

## Udvikling i et Codespace:
1. Gå til det nyoprettede repository i github.
2. Klik på den grønne <>Code knap og vælg "create codespace on \<branch>"
3. Kør ```. ./setup-dev-linux.sh ```, scriptet sætter et virtual environment op og installerer pakkerne i app/requirements.txt og requirements-dev.txt

## Udvikling lokalt:
1. Gå til det nyoprettede repository i github.
2. Klik på den grønne <>Code knap og kopier url'et, clone det med git: ```git clone <url>```
3. Kør ```. ./setup-dev-linux.sh ``` (Linux) eller ```setup-dev-windows.bat``` (Windows), scriptet sætter et virtual environment op og installerer pakkerne i app/requirements.txt og requirements-dev.txt

## Quick start

### Almindelige commands
* Start app'en:  ```python src/main.py```
* Start app'en i docker container: ```docker-compose up```
* Unit tests: ```pytest```
* Lint: ```flake8 --ignore=E501 src tests --show-source```

### Logning
* Logning gøres med logger og **ikke** print() functionen
```
import logging
logger = logging.getLogger(__name__)
logger.info('My log line')
```
* Logning til stdout med filtrering  (kald til /healthz og /metrics fjernes) er sat op i [logging.py](/src/utils/logging.py#L12), og skal køres inden app'en starter, dette er allerede sat op i [main](/src/main.py)
* Prometheus: eksempel på gauge [opsætning her](/src/utils/logging.py#L9), [brug her](/src/main.py#L16)

### Database
* DatabaseClient kan håndtere 3 typer af dattabaser: 'mariadb', 'postgresql' and 'mssql'
* It can return the database connection or execute sql which returns a [SQLAlchemy Result object](https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Result)
* Eksempel på brug:
```
from utils.config import DB_DATABASE, DB_USER, DB_PASS, DB_HOST, DB_PORT
from utils.database import DatabaseClient

# Init DatabaseClient - available types are 
my_db = DatabaseClient('mariadb', DB_DATABASE, DB_USER, DB_PASS, DB_HOST, DB_PORT)

# Execute sql
res = my_db.execute_sql('SELCT * FROM my_table')
for row in res:
    print(row)

# Get connection - e.g. can be used with pandas 
with my_db.get_connection() as conn:
    my_pandas_dataframe.to_sql(name='my_table', con=conn, if_exists='replace', index=False)
```

### HTTP(S) requests - brug af eksterne API'er
APIClient kan håntere flere typer authentication, eksempel på brug herunder:
* API key, fx. uddannelsesstatistik
```
from utils.config import MY_API_KEY
from utils.api_requests import APIClient

us_client = ApiClient('https://api.uddannelsesstatistik.dk/Api/v1/statistik', api_key=MY_API_KEY)
```
* Access token, fx. sbsys eller nexus
```
from utils.config import MY_CLIENT_SECRET, MY_CLIENT_ID, MY_USERNAME, MY_PASSWORD
from utils.api_requests import APIClient

nexus_client = ApiClient('https://randers.nexus-review.kmd.dk:443/api/core/mobile/randers/v2/', client_id=MY_CLIENT_ID, client_secret=MY_CLIENT_SECRET)
sbsys_client = ApiClient('https://sbsip-web-test01.randers.dk:8543/', client_id=MY_CLIENT_ID, client_secret=MY_CLIENT_SECRET, username=MY_USERNAME, password=MY_PASSWORD)
```
* Certifikat, fx. delta
```
from utils.config import MY_BASE64_CERT, MY_PASSWORD
from utils.api_requests import APIClient

delta_client = ApiClient('https://randers.nexus-review.kmd.dk:443/api/core/mobile/randers/v2/', cert_base64=MY_BASE64_CERT, password=MY_PASSWORD)
```
* Requests
```
# GET requests
my_api_client.make_request(path='some/path')
my_api_client.make_request(method='get', path='some/path')

# POST requests
my_dict = {'key': 'value'}
my_api_client.make_request(path='some/path', json=my_dict)

my_json = json.dumps(my_dict)
my_api_client.make_request(method='POST', path='some/path', data=my_json)

# PUT or DELETE
my_api_client.make_request(method='PUT', path='some/path', json=my_dict)
my_api_client.make_request(method='delete', path='some/path', json=my_dict)
```

### SFTP - forbind til ftp server
SFTPClient kan håntere flere typer authentication, eksempel på brug herunder:
* Username og password
```
from utils.config import HOST, USERNAME, PASSWORD
from utils.sftp import SFTPClient

client = SFTPClient(HOST, USERNAME, PASSWORD)
```
* SSH nøgle
```
from utils.config import HOST, USERNAME, BASE64_SSH_KEY
from utils.sftp import SFTPClient

client = SFTPClient(HOST, USERNAME, key_base64=BASE64_SSH_KEY)
```
* kodeordsbeskyttet SSH nøgle
```
from utils.config import HOST, USERNAME, BASE64_SSH_KEY, SSH_KEY_PASS
from utils.sftp import SFTPClient

client = SFTPClient(HOST, USERNAME, key_base64=BASE64_SSH_KEY,  key_pass=SSH_KEY_PASS)
```
* Forbind og brug som [pysftp](https://pysftp.readthedocs.io/)
```
with client.get_connection() as conn:
    print(conn.listdir())
    my_file = conn.open('somepath/some_remote_file.txt')

```

### Endpoints
* Eksempel findes i [api_endpoints.py](src/api_endpoints.py), husk at aktivere i main.py

### Skriv til filer
* Hvis der skal skrives til filer skal det være på et eksternt mount
* Eksempel til at test lokalt [docker-compose.yml](/docker-compose.yml#L18)

### Scheduler - kør kode på bestemt tidspunkt eller med interval
* Lav endpoint der starter jobbet og Kald endpoint med cronjob i kubenetes
