import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../agents")))

import logging
import pytest


@pytest.fixture(autouse=True)
def reset_logging():
    """Ensure logging handlers are clean and levels are correct between tests."""
    # Store original state
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    yield

    # Restore original state
    root_logger.handlers = original_handlers
    root_logger.setLevel(original_level)

    # Also clean up any mock handlers that might have been added to other loggers
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        if hasattr(logger, "handlers"):
            for handler in logger.handlers[:]:
                if not isinstance(handler, logging.Handler) or "MagicMock" in str(type(handler.level)):
                    logger.removeHandler(handler)
