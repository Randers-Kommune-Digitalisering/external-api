"""
Gunicorn configuration.

This module configures Gunicorn logging for the generated Flask app. It
defines a custom access logger that can suppress noisy request paths such as
health checks, keeps log output container-friendly, and applies the same
Danish timestamp format to Gunicorn runtime logs as the application logs.
"""
import os

try:  # Gunicorn is optional for local dev server usage
    from gunicorn.glogging import Logger as _GunicornLogger
except Exception:  # pragma: no cover
    _GunicornLogger = object  # type: ignore[assignment]


class AccessLogger(_GunicornLogger):
    """
    Gunicorn logger that can suppress access logs for selected paths.
    """

    def access(
        self: "AccessLogger",
        resp: object,
        req: object,
        environ: dict[str, object],
        request_time: float,
    ) -> None:
        """
        Log a request unless it matches a disabled path or status code.

        Disabled paths can be set via `GUNICORN_DISABLE_ACCESS_LOG_PATHS` and
        disabled status codes via `GUNICORN_DISABLE_ACCESS_LOG_STATUS_CODES`.
        """
        disabled_paths_env = os.getenv("GUNICORN_DISABLE_ACCESS_LOG_PATHS", "/healthz")
        disabled_paths = {p.strip() for p in disabled_paths_env.split(",") if p.strip()}

        disabled_status_codes_env = os.getenv("GUNICORN_DISABLE_ACCESS_LOG_STATUS_CODES", "404")
        disabled_status_codes = {
            int(code.strip())
            for code in disabled_status_codes_env.split(",")
            if code.strip()
        }

        raw_uri = environ.get("RAW_URI") or ""
        path_info = environ.get("PATH_INFO") or ""
        path = raw_uri or path_info or getattr(req, "path", "")
        path_only = str(path).split("?", 1)[0]

        if path_only in disabled_paths:
            return

        status = getattr(resp, "status", "")
        status_code = None
        try:
            if isinstance(status, str):
                status_code = int(status.split()[0])
            else:
                status_code = int(status)
        except (TypeError, ValueError):
            status_code = None

        if status_code in disabled_status_codes:
            return

        if not hasattr(super(), "access"):
            raise RuntimeError("Gunicorn is required to use AccessLogger")

        return super().access(resp, req, environ, request_time)


# Keep these environment-driven so ops can tune without rebuilding.
loglevel = "debug" if os.getenv("DEBUG", "False").lower() in ("true", "1", "t") else "info"
errorlog = "-"  # stdout/stderr in containers

# Emit access logs to stdout. The format is customized below.
accesslog = "-"

# Keep access logs compact (no headers/payloads/user-agent) and Werkzeug-like.
# Note: Timestamp comes from the log formatter (Danish format), not from %(t)s.
access_log_format = '%(h)s - - "%(m)s %(U)s%(q)s %(H)s" %(s)s %(B)s'

# Custom logger allows suppressing noisy endpoints like /healthz.
pythonpath = os.getenv("GUNICORN_PYTHONPATH", "src")
logger_class = AccessLogger

# Format Gunicorn startup/runtime logs with Danish timestamp.
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "gunicorn": {
            "class": "logging.Formatter",
            "format": "[%(asctime)s] %(levelname)s - %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "gunicorn",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "gunicorn.error": {
            "level": loglevel.upper(),
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": loglevel.upper(),
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
