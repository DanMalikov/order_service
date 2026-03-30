import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config import settings


def setup_glitchtip() -> None:
    """Конфиг для glitchtip"""
    if not settings.sentry_dsn:
        return

    logging_integration = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR,
    )

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[logging_integration],
        send_default_pii=False,
        enable_tracing=False,
        environment="production",
    )
