import pytest
from unittest.mock import patch, MagicMock
from utils.database import DatabaseClient


def test_invalid_db_type():
    with pytest.raises(ValueError) as excinfo:
        DatabaseClient('invalid_db', 'database', 'username', 'password', 'host')
    assert 'Invalid database type' in str(excinfo.value)


@patch('sqlalchemy.create_engine')
def test_valid_db_type_mssql(mock_create_engine):
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    client = DatabaseClient('mssql', 'database', 'username', 'password', 'host')
    mock_create_engine.assert_called_with('mssql+pymssql://username:password@host/database')

    client = DatabaseClient('mariadb', 'database', 'username', 'password', 'host', 3306)
    mock_create_engine.assert_called_with('mariadb+mariadbconnector://username:password@host:3306/database')

    client = DatabaseClient('postgresql', 'database', 'username', 'password', 'host', '5432')
    mock_create_engine.assert_called_with('postgresql+psycopg2://username:password@host:5432/database')
    assert client.engine == mock_engine


@patch('sqlalchemy.create_engine')
def test_get_connection_success(mock_create_engine):
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_engine.connect.return_value = mock_connection
    mock_create_engine.return_value = mock_engine

    client = DatabaseClient('mssql', 'database', 'username', 'password', 'host')
    conn = client.get_connection()
    assert conn == mock_connection
    mock_engine.connect.assert_called_once()


@patch('sqlalchemy.create_engine')
def test_get_connection_failure(mock_create_engine):
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = Exception('Connection error')
    mock_create_engine.return_value = mock_engine

    client = DatabaseClient('mssql', 'database', 'username', 'password', 'host')
    with patch.object(client.logger, 'error') as mock_logger_error:
        conn = client.get_connection()
        assert conn is None
        mock_logger_error.assert_called_with('Error connecting to database: Connection error')


@patch('sqlalchemy.create_engine')
def test_get_connection_no_engine_failure(mock_create_engine):
    client = DatabaseClient('mssql', 'database', 'username', 'password', 'host')
    client.engine = None
    with patch.object(client.logger, 'error') as mock_logger_error:
        conn = client.get_connection()
        assert conn is None
        mock_logger_error.assert_called_with('DatabaseClient not initialized properly. Engine is None. Check error from init.')


@patch('sqlalchemy.create_engine')
def test_execute_sql_success(mock_create_engine):
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_connection.__enter__().execute.return_value = mock_result
    mock_engine.connect.return_value = mock_connection
    mock_create_engine.return_value = mock_engine

    client = DatabaseClient('mssql', 'database', 'username', 'password', 'host')
    sql = 'SELECT * FROM table'
    result = client.execute_sql(sql)
    assert result == mock_result


@patch('sqlalchemy.create_engine')
def test_execute_sql_failure(mock_create_engine):
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_connection.__enter__().execute.side_effect = Exception('SQL error')
    mock_engine.connect.return_value = mock_connection
    mock_create_engine.return_value = mock_engine

    client = DatabaseClient('mssql', 'database', 'username', 'password', 'host')
    sql = 'SELECT * FROM table'
    with patch.object(client.logger, 'error') as mock_logger_error:
        result = client.execute_sql(sql)
        assert result is None
        mock_logger_error.assert_any_call('Error executing SQL: SQL error')
