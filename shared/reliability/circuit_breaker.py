import time
import logging
from enum import Enum
from typing import Callable, Any
from django.core.cache import cache

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

class RedisCircuitBreaker:
    """
    A Circuit Breaker that uses Redis via Django's cache framework to share state
    across multiple Celery worker processes.
    """
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        success_threshold: int = 2,
    ):
        self.name = f"cb_{name}"
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.success_threshold = success_threshold

    def _get_state(self):
        state = cache.get(f"{self.name}_state", CircuitState.CLOSED.value)
        return CircuitState(state)

    def _set_state(self, state: CircuitState):
        cache.set(f"{self.name}_state", state.value, timeout=None)

    def _get_failures(self):
        return cache.get(f"{self.name}_failures", 0)

    def _increment_failures(self):
        try:
            return cache.incr(f"{self.name}_failures")
        except ValueError:
            cache.set(f"{self.name}_failures", 1, timeout=None)
            return 1

    def _reset_failures(self):
        cache.set(f"{self.name}_failures", 0, timeout=None)

    def _get_successes(self):
        return cache.get(f"{self.name}_successes", 0)

    def _increment_successes(self):
        try:
            return cache.incr(f"{self.name}_successes")
        except ValueError:
            cache.set(f"{self.name}_successes", 1, timeout=None)
            return 1

    def _reset_successes(self):
        cache.set(f"{self.name}_successes", 0, timeout=None)

    def _get_last_failure_time(self):
        return cache.get(f"{self.name}_last_failure_time", 0)

    def _set_last_failure_time(self, timestamp: float):
        cache.set(f"{self.name}_last_failure_time", timestamp, timeout=None)

    def call(self, fn: Callable, fallback: Callable = None, *args, **kwargs) -> Any:
        state = self._get_state()

        if state == CircuitState.OPEN:
            last_failure = self._get_last_failure_time()
            if time.time() - last_failure > self.reset_timeout:
                self._set_state(CircuitState.HALF_OPEN)
                logger.info(f"Circuit {self.name} transitioned to HALF_OPEN")
            else:
                if fallback:
                    logger.warning(f"Circuit {self.name} is OPEN. Using fallback.")
                    return fallback(*args, **kwargs)
                raise Exception(f"Circuit {self.name} OPEN: service unavailable")

        try:
            result = fn(*args, **kwargs)
            
            # If successful and we were in HALF_OPEN, increment successes
            current_state = self._get_state()
            if current_state == CircuitState.HALF_OPEN:
                successes = self._increment_successes()
                if successes >= self.success_threshold:
                    self._set_state(CircuitState.CLOSED)
                    self._reset_failures()
                    self._reset_successes()
                    logger.info(f"Circuit {self.name} transitioned to CLOSED")
            else:
                self._reset_failures()
                
            return result

        except Exception as e:
            failures = self._increment_failures()
            self._set_last_failure_time(time.time())
            logger.error(f"Circuit {self.name} failure {failures}/{self.failure_threshold}: {e}")
            
            if failures >= self.failure_threshold:
                self._set_state(CircuitState.OPEN)
                logger.error(f"Circuit {self.name} transitioned to OPEN")
                
            if fallback:
                return fallback(*args, **kwargs)
            raise
