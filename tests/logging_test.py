import logging
import sys

from unittest.mock import patch, Mock
from werkzeug import serving

from utils.logging import disable_endpoint_logs, set_logging_configuration


def test_disable_endpoint_logs():
    original_log_request = Mock()
    with patch.object(serving.WSGIRequestHandler, 'log_request', new=original_log_request):

        disable_endpoint_logs(['/disabled-endpoint'])

        mock_request = Mock()
        mock_request.path = '/disabled-endpoint'

        serving.WSGIRequestHandler.log_request(mock_request)

        original_log_request.assert_not_called()

        mock_request.path = '/other'

        serving.WSGIRequestHandler.log_request(mock_request)

        original_log_request.assert_called_once_with(mock_request)


@patch('logging.basicConfig')
@patch('utils.logging.disable_endpoint_logs')
def test_set_logging_configuration(mock_disable_endpoint_logs, mock_basicConfig):

    set_logging_configuration()

    mock_basicConfig.assert_called_once_with(
        stream=sys.stdout,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s - %(name)s - %(module)s:%(funcName)s - %(message)s',
        datefmt='%d-%m-%Y %H:%M:%S'
    )

    mock_disable_endpoint_logs.assert_called_once_with(('/metrics', '/healthz'))
