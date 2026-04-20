import logging
from logging import LoggerAdapter

def create_logger(service_name: str):
    base_logger = logging.getLogger(service_name)
    base_logger.setLevel(logging.INFO)

    if base_logger.handlers:
        return base_logger

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    base_logger.addHandler(console_handler)

    logger = LoggerAdapter(base_logger, {"service": service_name})

    if ENV == "prod":
        try:
            from logging_loki import LokiHandler

            loki_handler = LokiHandler(
                url="http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push",
                tags={
                    "service": service_name,
                    "env": ENV
                },
                version="1",
            )

            loki_handler.setFormatter(formatter)
            base_logger.addHandler(loki_handler)

        except Exception as e:
            base_logger.error(f"Loki init failed: {e}")

    return logger


logger = create_logger("simple-fastapi-app")