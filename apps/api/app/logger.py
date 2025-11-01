import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

from app.config import settings

# Context variable for request ID correlation
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """Add request ID to log records."""
    
    def filter(self, record):
        record.request_id = request_id_var.get() or "no-request"
        return True


def setup_logging():
    """Configure structured logging with request ID correlation."""
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (req:%(request_id)s) - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.addHandler(handler)
    
    # Reduce noise from external libraries
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("stripe").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name)


def set_request_id(request_id: Optional[str] = None):
    """Set request ID for current context."""
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get current request ID."""
    return request_id_var.get()