import time
import base64
import logging


class APIClient:
    def __init__(self, base_url, api_key=None, realm=None, client_id=None, client_secret=None, username=None, password=None, cert_base64=None):
        self.base_url = base_url
        self.api_key = api_key
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password

        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.refresh_token_expiry = None
        self.cert_data = None

        if cert_base64:
            self.cert_data = base64.b64decode(cert_base64)

        self.logger = logging.getLogger(__name__)

    def _authenticate(self):
        if self.api_key:
            return {'Authorization': f'Bearer {self.api_key}'}
        elif self.client_id and self.client_secret:
            if not self.realm:
                raise ValueError('Realm is required for client_id and client_secret authentication')

            refresh_token = False

            if self.access_token:
                if self.token_expiry:
                    if time.time() < self.token_expiry:
                        return {'Authorization': f'Bearer {self.access_token}'}
                    else:
                        if self.refresh_token:
                            if self.refresh_token_expiry:
                                if time.time() < self.refresh_token_expiry:
                                    refresh_token = True

            tmp_url = f'{self.base_url}/auth/realms/{self.realm}/protocol/openid-connect/token'

            tmp_headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            tmp_json_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            if refresh_token:
                tmp_json_data['grant_type'] = 'refresh_token'
                tmp_json_data['refresh_token'] = self.refresh_token
            elif self.username and self.password:
                tmp_json_data['grant_type'] = 'password'
                tmp_json_data['username'] = self.username
                tmp_json_data['password'] = self.password
            else:
                tmp_json_data['grant_type'] = 'client_credentials'

            now = time.time()

            import requests

            response = requests.post(tmp_url, headers=tmp_headers, data=tmp_json_data)
            response.raise_for_status()
            data = response.json()

            self.access_token = data['access_token']
            self.token_expiry = now + data['expires_in']

            if 'refresh_token' in data:
                self.refresh_token = data['refresh_token']
                self.refresh_token_expiry = now + data['refresh_expires_in']

            return {'Authorization': f'Bearer {self.access_token}'}
        else:
            return {}

    def make_request(self, **kwargs):
        try:
            if self.cert_data:
                import requests_pkcs12 as requests
                kwargs['pkcs12_data'] = self.cert_data
                kwargs['pkcs12_password'] = self.password
            else:
                import requests

            if 'path' in kwargs:
                if not isinstance(kwargs['path'], str):
                    raise ValueError('Path must be a string')
                url = self.base_url.rstrip('/') + '/' + kwargs.pop('path').lstrip('/')
            else:
                url = self.base_url

            if 'headers' in kwargs:
                if not isinstance(kwargs['headers'], dict):
                    raise ValueError('Headers must be a dictionary')
                kwargs['headers'] = kwargs['headers'] | self._authenticate()
            else:
                kwargs['headers'] = self._authenticate()

            if not any(ele in kwargs for ele in ['method', 'json', 'data', 'files']):
                method_string = 'GET'
                method = requests.get
            elif 'method' in kwargs:
                method_string = kwargs.pop('method').strip().upper()
                method = getattr(requests, method_string.lower())
            else:
                method_string = 'POST'
                method = requests.post

            if 'json' in kwargs:
                kwargs['headers']['Content-Type'] = 'application/json'

            response = method(url, **kwargs)
            response.raise_for_status()

            self.logger.info(f'{method_string} request to {url} successful')

            if 'application/json' in response.headers.get('Content-Type', ''):
                return response.json()
            else:
                if not response.content:
                    return b' '
                return response.content

        except Exception as e:
            self.logger.error(f'Request failed with error: {e.__class__} {e}')
