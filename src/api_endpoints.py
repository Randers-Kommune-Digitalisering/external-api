import logging
import time

from datetime import timedelta
from flask import Blueprint, Response, request

from utils.config import POD_NAME
from utils.logging import is_ready_gauge, last_updated_gauge, job_start_counter, job_complete_counter, job_duration_summary

logger = logging.getLogger(__name__)
api_endpoints = Blueprint('api', __name__, url_prefix='/api')

# NB: uncomment code in main.py to enable these endpoints
# Any endpoints added here will be available at /api/<endpoint> - e.g. http://127.0.0.1:8080/api/example
# Change the the example below to suit your needs + add more as needed


@api_endpoints.route('/example', methods=['GET', 'POST'])
def example():
    if request.method == 'POST':
        if request.headers.get('Content-Type') == 'application/json':
            payload = request.get_json()

            # -- Example job with example use of metrics -- #
            is_ready_gauge.labels(error_type='working', job_name=POD_NAME).set(0)
            last_updated_gauge.set_to_current_time()

            job_start_counter.labels(job_name='example job').inc()

            start_time = time.time()
            logger.info('Doing important job - that somehow prevents the app from being ready')
            duration = timedelta(seconds=(time.time() - start_time))

            job_duration_summary.labels(job_name='example job', status='success').observe(duration.total_seconds())
            job_complete_counter.labels(job_name='example job', status='success').inc()

            is_ready_gauge.labels(error_type=None, job_name=POD_NAME).set(1)
            last_updated_gauge.set_to_current_time()
            # --------------------------------------------- #

            return Response(f'You posted: {payload}', status=200)
        else:
            return Response('Content-Type must be application/json', status=400)
    else:
        # -- Example job with example use of metrics -- #
        job_start_counter.labels(job_name='another example job').inc()

        start_time = time.time()
        logger.info('Doing important job - that does NOT prevent the app from being ready')
        duration = timedelta(seconds=(time.time() - start_time))

        job_duration_summary.labels(job_name='another example job', status='success').observe(duration.total_seconds())
        job_complete_counter.labels(job_name='another example job', status='success').inc()
        # --------------------------------------------- #

        return Response('Example response', status=200)
