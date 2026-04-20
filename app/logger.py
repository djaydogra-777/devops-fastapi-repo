import logging
import os

ENV = os.getenv("ENV", "dev")

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

class ServiceLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"]["service"] = self.extra["service"]
        return msg, kwargs


def create_logger(service_name: str):
    base_logger = logging.getLogger(service_name)
    base_logger.setLevel(logging.INFO)

    if base_logger.handlers:
        return base_logger

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    base_logger.addHandler(console_handler)

    logger = ServiceLogger(base_logger, {"service": service_name})

    if ENV == "prod":
        try:
            from logging_loki import LokiHandler

            loki_handler = LokiHandler(
                url="http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push",
                tags={
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