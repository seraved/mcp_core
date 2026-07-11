from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(service: str, level: str = "INFO") -> None:
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    structlog.contextvars.bind_contextvars(service=service)
