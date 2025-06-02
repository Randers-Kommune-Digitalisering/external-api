import sys
import logging
import re

from werkzeug import serving
from prometheus_client import Gauge, Counter, Summary

from utils.config import DEBUG

# Prometheus metricts

# Availavility metrics
is_ready_gauge = Gauge('is_ready', '1 - app is running, 0 - app is down', labelnames=['error_type', 'job_name'])
last_updated_gauge = Gauge('last_updated_ms', "Timestamp in milliseconds of the last time the app's availability was updated")

# Dependency metrics
is_available_gauge = Gauge('is_available', '1 - dependency is available, 0 - dependency is not available', labelnames=['dependency_name'])

# Job metrics
job_start_counter = Counter('job_start', 'Number of times a job has started', labelnames=['job_name'])
job_complete_counter = Counter('job_complete', 'Number of times a job has completed', labelnames=['job_name', 'status'])
job_duration_summary = Summary('job_duration_s', 'Duration of a job in seconds', labelnames=['job_name', 'status'])


# Logging configuration
def set_logging_configuration():
    log_level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(stream=sys.stdout, level=log_level, format='[%(asctime)s] %(levelname)s - %(name)s - %(module)s:%(funcName)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
    disable_endpoint_logs(('/metrics', '/healthz'))


def disable_endpoint_logs(disabled_endpoints):
    parent_log_request = serving.WSGIRequestHandler.log_request

    def log_request(self, *args, **kwargs):
        if not any(re.match(f"{de}$", self.path) for de in disabled_endpoints):
            parent_log_request(self, *args, **kwargs)

    serving.WSGIRequestHandler.log_request = log_request
