import time
from functools import wraps
from observability import get_logger

log = get_logger()


def with_retry(max_attempts: int = 3, delay_seconds: float = 1.0):
    """
    Reintenta una tool hasta max_attempts veces con exponential backoff.

    Intento 1 falla -> espera 1s  -> intento 2
    Intento 2 falla -> espera 2s  -> intento 3
    Intento 3 falla -> lanza la excepcion al caller (run_tool la captura)

    Por que exponential backoff y no retry inmediato:
    Si la API esta saturada, reintentar inmediatamente la satura mas.
    Esperar tiempo creciente da chance de que se recupere.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts:
                        wait = delay_seconds * (2 ** (attempt - 1))
                        log.warning(
                            "tool.retry",
                            tool=fn.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            wait_seconds=wait,
                            error=str(e),
                        )
                        time.sleep(wait)
                    else:
                        log.error(
                            "tool.exhausted",
                            tool=fn.__name__,
                            attempts=max_attempts,
                            error=str(e),
                        )

            raise last_error

        return wrapper
    return decorator
