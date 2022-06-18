import multiprocessing

# see https://docs.gunicorn.org/en/latest/settings.html

accesslog = "./logs/gunicorn_access_log.txt"
bind = "0.0.0.0:5433"
# capture_output = True
errorlog = "./logs/gunicorn_error_log.txt"
loglevel = "info"
threads = multiprocessing.cpu_count() * 2 + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
