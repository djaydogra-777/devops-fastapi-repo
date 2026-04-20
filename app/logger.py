import logging
import os
from logging import LoggerAdapter

# Environment
ENV = os.getenv("ENV", "dev")

# Formatter (simple + works well with Loki)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)


def create_logger(service_name: str):
    base_logger = logging.getLogger(service_name)
    base_logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if base_logger.handlers:
        return base_logger

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    base_logger.addHandler(console_handler)

    # Attach service context
    logger = LoggerAdapter(base_logger, {"service": service_name})

    # Loki handler only in prod
    if ENV == "prod":
        try:
            from logging_loki import LokiHandler

            loki_handler = LokiHandler(
                url="http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push",
                tags={
                    "service": service_name,
                    "env": ENV,
                },
                version="1",
            )

            loki_handler.setFormatter(formatter)
            base_logger.addHandler(loki_handler)

        except Exception as e:
            base_logger.error(f"Loki init failed: {e}")

    return logger


# Default logger used across app
logger = create_logger("simple-fastapi-app")