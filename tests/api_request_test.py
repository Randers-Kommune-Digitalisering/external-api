import pytest
import base64

from unittest.mock import MagicMock, patch

from utils.api_requests import APIClient


def test_init():
    api_client = APIClient('http://testurl.com')

    assert api_client.base_url == 'http://testurl.com'

# _authenticate tests


def test_authenticate_api_key():
    api_client = APIClient('http://testurl.com', api_key='test_key')

    assert api_client._authenticate() == {'Authorization': 'Bearer test_key'}


@patch('time.time')
@patch('requests.post')
def test_authenticate_client_credentials(mock_post, mock_time):
    api_client = APIClient('http://testurl.com', client_id='test_id', client_secret='test_secret', realm='test_realm')

    mock_time.return_value = 0

    res = MagicMock()
    res.raise_for_status.return_value = None
    res.json.return_value = {'access_token': 'test_token', 'expires_in': 10, 'refresh_token': 'test_refresh_token', 'refresh_expires_in': 20}
    mock_post.return_value = res

    assert api_client._authenticate() == {'Authorization': 'Bearer test_token'}
    mock_post.assert_called_once_with('http://testurl.com/auth/realms/test_realm/protocol/openid-connect/token', headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={'client_id': 'test_id', 'client_secret': 'test_secret', 'grant_type': 'client_credentials'})
    assert api_client.token_expiry == 10
    assert api_client.refresh_token_expiry == 20
    assert api_client.refresh_token == 'test_refresh_token'

    assert api_client._authenticate() == {'Authorization': 'Bearer test_token'}


@patch('time.time')
@patch('requests.post')
def test_authenticate_user_password(mock_post, mock_time):
    api_client = APIClient('http://testurl.com', client_id='test_id', client_secret='test_secret', realm='test_realm', username='test_user', password='test_pass')

    mock_time.return_value = 0

    res = MagicMock()
    res.raise_for_status.return_value = None
    res.json.return_value = {'access_token': 'test_token', 'expires_in': 10, 'refresh_token': 'test_refresh_token', 'refresh_expires_in': 20}
    mock_post.return_value = res

    assert api_client._authenticate() == {'Authorization': 'Bearer test_token'}
    mock_post.assert_called_once_with('http://testurl.com/auth/realms/test_realm/protocol/openid-connect/token', headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={'client_id': 'test_id', 'client_secret': 'test_secret', 'grant_type': 'password', 'username': 'test_user', 'password': 'test_pass'})
    assert api_client.token_expiry == 10
    assert api_client.refresh_token_expiry == 20
    assert api_client.refresh_token == 'test_refresh_token'


def test_authenticate_cert():
    test_base64 = base64.b64encode(b'test_cert')
    api_client = APIClient('http://testurl.com', cert_base64=test_base64, password='test_pass')

    assert api_client._authenticate() == {}


@patch('time.time')
@patch('requests.post')
def test_authenticate_refresh_token(mock_post, mock_time):
    api_client = APIClient('http://testurl.com', client_id='test_id', client_secret='test_secret', realm='test_realm')
    api_client.access_token = 'test_token'
    api_client.token_expiry = 10
    api_client.refresh_token = 'test_refresh_token'
    api_client.refresh_token_expiry = 20

    mock_time.return_value = 15

    res = MagicMock()
    res.raise_for_status.return_value = None
    res.json.return_value = {'access_token': 'test_token', 'expires_in': 10, 'refresh_token': 'test_refresh_token', 'refresh_expires_in': 20}
    mock_post.return_value = res

    assert api_client._authenticate() == {'Authorization': 'Bearer test_token'}
    mock_post.assert_called_once_with('http://testurl.com/auth/realms/test_realm/protocol/openid-connect/token', headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={'client_id': 'test_id', 'client_secret': 'test_secret', 'grant_type': 'refresh_token', 'refresh_token': 'test_refresh_token'})
    assert api_client.token_expiry == 25  # time now is 15
    assert api_client.refresh_token_expiry == 35  # time now is 15
    assert api_client.refresh_token == 'test_refresh_token'


def test_authenticate_no_realm():
    with pytest.raises(ValueError) as excinfo:
        api_client = APIClient('http://testurl.com', client_id='test_id', client_secret='test_secret', realm='test_realm')
        api_client.realm = None
        api_client._authenticate()
    assert 'Realm is required for client_id and client_secret authentication' in str(excinfo.value)

# make_request tests


@patch('requests.get')
def test_make_request_get(mock_get):
    api_client = APIClient('http://testurl.com', api_key='test_key')

    res = MagicMock()
    res.raise_for_status.return_value = None
    res.headers.get.return_value = 'application/json'
    res.json.return_value = {'test': 'test'}
    mock_get.return_value = res

    assert api_client.make_request(path='/test') == {'test': 'test'}
    mock_get.assert_called_once_with('http://testurl.com/test', headers={'Authorization': 'Bearer test_key'})


@patch('requests.post')
def test_make_request_post(mock_get):
    api_client = APIClient('http://testurl.com', api_key='test_key')

    res = MagicMock()
    res.raise_for_status.return_value = None
    res.content = b''
    mock_get.return_value = res

    assert api_client.make_request(path='/test', json={'test': 'test'}) == b' '
    mock_get.assert_called_once_with('http://testurl.com/test', headers={'Authorization': 'Bearer test_key', 'Content-Type': 'application/json'}, json={'test': 'test'})


@patch('requests.put')
def test_make_request_put(mock_get):
    api_client = APIClient('http://testurl.com', api_key='test_key')

    res = MagicMock()
    res.raise_for_status.return_value = None
    res.content = b'ok'
    mock_get.return_value = res

    assert api_client.make_request(method='put', headers={'custom': 'header'}, data='test') == b'ok'
    mock_get.assert_called_once_with('http://testurl.com', headers={'Authorization': 'Bearer test_key', 'custom': 'header'}, data='test')


@patch('requests.delete')
def test_make_request_delete(mock_get):
    api_client = APIClient('http://testurl.com', api_key='test_key')

    res = MagicMock()
    res.raise_for_status.return_value = None
    res.content = b'ok'
    mock_get.return_value = res

    assert api_client.make_request(method='DELETE', path='/test', data='test') == b'ok'
    mock_get.assert_called_once_with('http://testurl.com/test', headers={'Authorization': 'Bearer test_key'}, data='test')


@patch('requests_pkcs12.post')
def test_make_request_get_cert(mock_get):
    test_base64 = base64.b64encode(b'test_cert')
    api_client = APIClient('http://testurl.com', cert_base64=test_base64, password='test_pass')

    res = MagicMock()
    res.raise_for_status.return_value = None
    res.content = b'ok'
    mock_get.return_value = res

    assert api_client.make_request(path='/test', json={'test': 'test'}) == b'ok'
    mock_get.assert_called_once_with('http://testurl.com/test', json={'test': 'test'}, pkcs12_data=b'test_cert', pkcs12_password='test_pass', headers={'Content-Type': 'application/json'})


def test_make_request_wrong_path():
    api_client = APIClient('http://testurl.com', api_key='test_key')
    api_client.logger = MagicMock()
    assert api_client.make_request(path=1) is None
    api_client.logger.error.assert_called_once_with("Request failed with error: <class 'ValueError'> Path must be a string")


def test_make_request_wrong_headers():
    api_client = APIClient('http://testurl.com', api_key='test_key')
    api_client.logger = MagicMock()
    assert api_client.make_request(headers='not a dict') is None
    api_client.logger.error.assert_called_once_with("Request failed with error: <class 'ValueError'> Headers must be a dictionary")
