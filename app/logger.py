"""
logger.py – Python equivalent of the pino + pino-loki setup.

JS → Python mapping
────────────────────────────────────────────────────────────────
pino.transport({ target: "pino-loki", options: { ... } })
  → LokiHandler  (custom logging.Handler)
      Ships log records to Loki's /loki/api/v1/push endpoint.

batching: true, interval: 5
  → background daemon thread that drains a queue.Queue every 5 s
    (or when BATCH_MAX_SIZE lines accumulate)

headers: { "X-Scope-OrgID": "tenant1" }
  → requests.Session header for Loki multi-tenancy

labels: { env, service }
  → Loki stream-level labels (searchable in Grafana)

propsToLabels: ["service"]
  → "service" is promoted from the log record to a Loki label

replaceTimestamp: true
  → log record's created-time is used as the Loki nanosecond ts

base: { service: "..." }
  → SERVICE_NAME constant, injected into every log record's labels

transport.on('error', ...)
  → transport errors are printed to stderr; they never crash the app
────────────────────────────────────────────────────────────────
"""

import json
import logging
import queue
import threading
import time
import traceback
from typing import Optional

import requests

# ── Configuration ─────────────────────────────────────────────────────────────
LOKI_HOST = "http://loki-gateway.loki.svc.cluster.local"
LOKI_PUSH_URL = f"{LOKI_HOST}/loki/api/v1/push"

LOKI_TENANT_ID = "tenant1"   # X-Scope-OrgID – required when auth.enabled = true

SERVICE_NAME = "fastapi-app"  # equivalent to pino's base.service
ENV = "development"

BATCH_INTERVAL = 5            # seconds between flushes  (pino: interval: 5)
BATCH_MAX_SIZE = 100          # max lines per HTTP push
# ─────────────────────────────────────────────────────────────────────────────

# Standard Python level names → Loki-friendly label values
_LEVEL_MAP = {
    "DEBUG":    "debug",
    "INFO":     "info",
    "WARNING":  "warn",
    "ERROR":    "error",
    "CRITICAL": "critical",
}


class LokiHandler(logging.Handler):
    """
    Async, batching log handler that ships structured log lines to Grafana Loki.

    Each emitted record becomes one "value" inside a Loki stream.
    Records with the same label-set are grouped into the same stream before
    the batch is POSTed, reducing the number of active streams in Loki.
    """

    def __init__(
        self,
        url: str,
        labels: dict,
        tenant_id: Optional[str] = None,
        batch_interval: int = BATCH_INTERVAL,
        batch_max_size: int = BATCH_MAX_SIZE,
    ) -> None:
        super().__init__()
        self.url = url
        self.base_labels = labels          # static labels applied to every stream
        self.tenant_id = tenant_id
        self.batch_interval = batch_interval
        self.batch_max_size = batch_max_size

        self._queue: queue.Queue = queue.Queue()
        self._session = self._make_session()

        self._stop = threading.Event()
        # daemon=True → thread dies automatically when the process exits
        self._worker = threading.Thread(
            target=self._run, daemon=True, name="loki-transport"
        )
        self._worker.start()

    # ── internal helpers ──────────────────────────────────────────────────────

    def _make_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        if self.tenant_id:
            # Multi-tenancy header expected by Loki (pino: headers: { "X-Scope-OrgID": ... })
            session.headers["X-Scope-OrgID"] = self.tenant_id
        return session

    def _record_to_entry(self, record: logging.LogRecord) -> tuple[str, str, dict]:
        """
        Convert a LogRecord into a (timestamp_ns, message, extra_labels) tuple.

        replaceTimestamp: true → use the record's own creation time, not wall-clock.
        """
        timestamp_ns = str(int(record.created * 1e9))
        level_label = _LEVEL_MAP.get(record.levelname, record.levelname.lower())

        # Build the log line as a compact JSON string so Grafana can parse fields
        line: dict = {"level": record.levelname, "message": record.getMessage()}

        # Attach any extra= fields the caller passed (e.g. stack, error, order_id)
        for key, val in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                line[key] = val

        # Include the traceback when an exception was captured
        if record.exc_info:
            line["stack"] = "".join(traceback.format_exception(*record.exc_info))

        # propsToLabels: ["service"] – promote service to a Loki label
        extra_labels = {"level": level_label}
        if "service" in line:
            extra_labels["service"] = str(line.pop("service"))

        return timestamp_ns, json.dumps(line, default=str), extra_labels

    # ── logging.Handler interface ─────────────────────────────────────────────

    def emit(self, record: logging.LogRecord) -> None:
        """Called synchronously by the logging framework; must not block."""
        try:
            self._queue.put_nowait(record)
            # Flush immediately if the queue has grown large
            if self._queue.qsize() >= self.batch_max_size:
                self._stop.set()   # wake the worker early
                self._stop.clear()
        except Exception:
            self.handleError(record)

    # ── background worker ─────────────────────────────────────────────────────

    def _drain(self) -> list[logging.LogRecord]:
        batch = []
        while len(batch) < self.batch_max_size:
            try:
                batch.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return batch

    def _push(self, batch: list[logging.LogRecord]) -> None:
        if not batch:
            return

        # Group by label-set → one Loki stream per unique combination
        streams: dict = {}
        for record in batch:
            ts, line, extra_labels = self._record_to_entry(record)
            stream_labels = {**self.base_labels, **extra_labels}
            key = frozenset(stream_labels.items())
            if key not in streams:
                streams[key] = {"stream": stream_labels, "values": []}
            streams[key]["values"].append([ts, line])

        payload = {"streams": list(streams.values())}

        try:
            resp = self._session.post(
                self.url, data=json.dumps(payload, default=str), timeout=5
            )
            resp.raise_for_status()
        except Exception as exc:
            # Mirror: transport.on('error', (err) => console.error('🚨 Pino Transport Error ...', err))
            print(
                f"[LokiHandler] Failed to send logs to Loki: {exc}",
                flush=True,
            )

    def _run(self) -> None:
        """Background loop: flush every batch_interval seconds."""
        while not self._stop.wait(timeout=self.batch_interval):
            self._push(self._drain())
        # Final flush on graceful shutdown
        self._push(self._drain())

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def close(self) -> None:
        self._stop.set()
        self._worker.join(timeout=10)
        super().close()


# ── Public API ────────────────────────────────────────────────────────────────

def setup_logging(level: int = logging.INFO) -> None:
    """
    Call once at application startup (before the FastAPI app object is built).

    Attaches two handlers to the root logger:
      1. StreamHandler  – human-readable output on stdout (local dev / kubectl logs)
      2. LokiHandler    – batched JSON stream sent to Grafana Loki on the cluster

    Usage in main.py:
        from app.logger import setup_logging
        setup_logging()
    """
    loki = LokiHandler(
        url=LOKI_PUSH_URL,
        labels={"env": ENV, "service": SERVICE_NAME},
        tenant_id=LOKI_TENANT_ID,
    )
    loki.setFormatter(logging.Formatter("%(message)s"))  # raw message; labels carry metadata

    console = logging.StreamHandler()
    console.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s – %(message)s")
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(loki)


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Return a named logger.  Use this everywhere instead of print().

    Example:
        from app.logger import get_logger
        logger = get_logger(__name__)
        logger.info("order created")
        logger.error("payment failed", extra={"order_id": "abc", "amount": 99})
    """
    return logging.getLogger(name)
