"""Gunicorn configuration file for production deployment."""

import multiprocessing
import os

bind = os.getenv('BIND_ADDRESS', '0.0.0.0:8000')

workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))

worker_class = 'uvicorn.workers.UvicornWorker'

worker_connections = 1000

max_requests = 1000
max_requests_jitter = 50

timeout = 30
keepalive = 2

accesslog = '-'
errorlog = '-'
loglevel = 'info'

capture_output = True
enable_stdio_inheritance = True

reload = False

preload_app = True

def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    pass

def when_ready(server):
    """Called just after the server is started."""
    pass

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    pass

def pre_exec(server):
    """Called just before a new master process is forked."""
    pass

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    pass

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass

def child_exit(server, worker):
    """Called just after a worker has been exited."""
    pass

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    pass

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    pass

def on_exit(server):
    """Called just before exiting Gunicorn."""
    pass