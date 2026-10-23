from contextvars import ContextVar
from functools import wraps
import json
import logging
from time import perf_counter

from app.errors import ApiError, unavailable

request_id = ContextVar("request_id", default="startup")
logger = logging.getLogger("fixture.api")


def emit(**fields):
    logger.info(json.dumps({"request_id": request_id.get(), **fields}, ensure_ascii=True))


def guarded(source, exceptions):
    def decorate(method):
        @wraps(method)
        def wrapped(*args, **kwargs):
            start = perf_counter()
            result = "ok"
            error_type = None
            try:
                return method(*args, **kwargs)
            except ApiError as exc:
                result = exc.code
                raise
            except exceptions as exc:
                result = "dependency_error"
                error_type = type(exc).__name__
                raise unavailable(source) from None
            except Exception as exc:
                result = "internal_error"
                error_type = type(exc).__name__
                raise
            finally:
                emit(dependency=source, operation=method.__name__, result=result,
                     error_type=error_type, duration_ms=round((perf_counter()-start)*1000, 2))
        return wrapped
    return decorate
