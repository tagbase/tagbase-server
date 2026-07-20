"""Gunicorn settings for tagbase-server.

OpenTelemetry must be initialized after fork so each Uvicorn worker
gets its own SDK providers and exporters.
"""

import multiprocessing

# see https://docs.gunicorn.org/en/latest/settings.html

accesslog = "./logs/gunicorn_access_log.txt"
bind = "0.0.0.0:5433"
errorlog = "./logs/gunicorn_error_log.txt"
loglevel = "info"
worker_class = "uvicorn.workers.UvicornWorker"
workers = max(2, multiprocessing.cpu_count())


def post_fork(server, worker):
    from tagbase_server.__main__ import app
    from tagbase_server.telemetry import setup_telemetry

    setup_telemetry(flask_app=app.app)
    server.log.info("OpenTelemetry setup complete in worker pid=%s", worker.pid)
