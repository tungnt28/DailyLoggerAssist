"""
Gunicorn configuration for Daily Logger Assist production deployment.
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Restart workers after this many seconds
max_worker_age = 3600

# Kill workers if they don't respond within this time
timeout = 120
graceful_timeout = 30

# Logging
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "daily_logger_assist"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/private.key"
# certfile = "/path/to/certificate.crt"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Environment
raw_env = [
    f"ENVIRONMENT={os.getenv('ENVIRONMENT', 'production')}",
    f"DATABASE_URL={os.getenv('DATABASE_URL', '')}",
    f"REDIS_URL={os.getenv('REDIS_URL', '')}",
    f"SECRET_KEY={os.getenv('SECRET_KEY', '')}",
]

# Worker class specific settings
worker_tmp_dir = "/dev/shm"  # Use memory filesystem for better performance

# Preload app for better memory usage
preload_app = True

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Daily Logger Assist server is ready. Accepting connections.")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker %s received INT or QUIT signal", worker.pid)

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker aborted (pid: %s)", worker.pid) 