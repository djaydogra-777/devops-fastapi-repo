import logging
import sys
import json
from datetime import datetime

SERVICE_NAME = "simple-fastapi-app"
NAMESPACE = "simple-fastapi-app"
ENV = "development"


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": SERVICE_NAME,
            "namespace": NAMESPACE,
            "env": ENV,
            "logger": record.name,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []  # remove default handlers
    root_logger.addHandler(handler)


def get_logger(name: str):
    return logging.getLogger(name)