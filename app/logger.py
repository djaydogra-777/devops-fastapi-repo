import logging
import os

logger = logging.getLogger("fastapi-app")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

# Console handler (always)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

ENV = os.getenv("ENV", "dev")

# Only enable Loki in prod
if ENV == "prod":
    try:
        from logging_loki import LokiHandler

        loki_handler = LokiHandler(
            url="http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push",
            tags={
                "service": "fast-api-services",
                "env": "prod"
            },
            version="1",
        )

        loki_handler.setFormatter(formatter)
        logger.addHandler(loki_handler)

    except Exception as e:
        logger.error(f"Failed to initialize Loki handler: {e}")