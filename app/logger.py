import logging
import os
import json

logger = logging.getLogger("fastapi-app")
logger.setLevel(logging.INFO)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "simple-fastapi-app"
        })

formatter = JsonFormatter()

# Avoid duplicate handlers
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

ENV = os.getenv("ENV", "dev")

if ENV == "prod":
    try:
        from logging_loki import LokiHandler

        loki_handler = LokiHandler(
            url="http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push",
            tags={
                "service": "simple-fastapi-app",
                "env": "prod"
            },
            version="1",
            headers={"X-Scope-OrgID": "tenant1"},
        )

        loki_handler.setFormatter(formatter)
        logger.addHandler(loki_handler)

    except Exception as e:
        logger.error(f"Failed to initialize Loki handler: {e}")