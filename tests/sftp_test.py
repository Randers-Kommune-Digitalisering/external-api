from utils.sftp import SFTPClient
from unittest.mock import patch, MagicMock


@patch('pysftp.Connection')
def test_get_connection_success(mock_connection):
    client = SFTPClient('host', 'user', 'pass')
    mock_connection.return_value = MagicMock()

    result = client.get_connection()

    assert result is not None
    mock_connection.assert_called_once_with(host='host', username='user', password='pass', private_key=None, cnopts=client.cnopts)


@patch('pysftp.Connection')
def test_get_connection_exception(mock_connection):

    client = SFTPClient('host', 'user', 'pass')
    mock_connection.side_effect = Exception("Connection failed")

    result = client.get_connection()

    assert result is None


@patch('base64.b64decode')
@patch('paramiko.RSAKey.from_private_key')
def test_make_key(mock_from_private_key, mock_b64decode):
    mock_b64decode.return_value = b'decoded_key'
    mock_from_private_key.return_value = 'RSAKey'

    client = SFTPClient('host', 'user', key_base64='base64key', key_pass='keypass')

    assert client.key == 'RSAKey'
    mock_b64decode.assert_called_once_with('base64key')
    mock_from_private_key.assert_called_once()
