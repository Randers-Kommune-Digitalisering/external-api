import pytest

from unittest.mock import patch
from flask import json

from main import create_app
from api_endpoints import api_endpoints


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    app.register_blueprint(api_endpoints)
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@patch('api_endpoints.example')
def test_example_endpoint(mock_example, client):
    # Test POST with JSON data
    mock_example.return_value = 'You posted: {"test": "data"}'
    response = client.post('/example', data=json.dumps({"test": "data"}), content_type='application/json')
    assert response.status_code == 200
    assert response.data == b"You posted: {'test': 'data'}"

    # Test POST with non-JSON data
    mock_example.return_value = 'Content-Type must be application/json'
    response = client.post('/example', data='test data', content_type='text/plain')
    assert response.status_code == 400
    assert response.data == b'Content-Type must be application/json'

    # Test GET
    response = client.get('/example')
    assert response.status_code == 200
    assert response.data == b'Example response'
