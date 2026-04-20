import logging
import os
import json

ENV = os.getenv("ENV", "dev")

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "simple-fastapi-app"
        })

formatter = JsonFormatter()

def create_logger(service_name: str):
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if ENV == "prod":
        try:
            from logging_loki import LokiHandler

            loki_handler = LokiHandler(
                url="http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push",
                tags={"env": ENV},
                version="1",
            )

            loki_handler.setFormatter(formatter)
            logger.addHandler(loki_handler)

        except Exception as e:
            logger.error(f"Loki init failed: {e}")

    return logger


logger = create_logger("simple-fastapi-app")