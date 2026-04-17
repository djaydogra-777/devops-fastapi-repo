import logging
import os


def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)


def setup_logging() -> None:
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    ENV = os.getenv("ENV", "dev")

    if ENV == "prod":
        try:
            from logging_loki import LokiHandler

            loki_handler = LokiHandler(
                url="http://loki-gateway.loki.svc.cluster.local",
                tags={
                    "service": "simple-fastapi-app",
                    "env": "prod",
                },
                version="1",
            )
            loki_handler.setFormatter(formatter)
            app_logger.addHandler(loki_handler)

        except Exception as e:
            app_logger.error(f"Failed to initialize Loki handler: {e}")