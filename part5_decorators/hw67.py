import functools
import json
from datetime import UTC, datetime
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, message: str, func_name: str, block_time: datetime) -> None:
        super().__init__(message)
        self.func_name = func_name
        self.block_time = block_time


class _BreakerWrapper:
    __name__: str
    __module__: str
    __doc__: str | None

    def __init__(
        self,
        func: CallableWithMeta,  # type: ignore[type-arg]
        critical_count: int,
        time_to_recover: int,
        triggers_on: type[Exception],
    ) -> None:
        functools.update_wrapper(self, func)
        self._func = func
        self._func_name = f"{func.__module__}.{func.__name__}"
        self._critical_count = critical_count
        self._time_to_recover = time_to_recover
        self._triggers_on = triggers_on
        self._failure_count = 0
        self._blocked_at: datetime | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self._check_blocked()
        try:
            result = self._func(*args, **kwargs)
        except Exception as exc:
            self._on_error(exc)
            raise
        else:
            self._failure_count = 0
            return result

    def _check_blocked(self) -> None:
        if self._blocked_at is None:
            return
        elapsed = (datetime.now(UTC) - self._blocked_at).total_seconds()
        if elapsed >= self._time_to_recover:
            self._blocked_at = None
            self._failure_count = 0
        else:
            raise BreakerError(TOO_MUCH, self._func_name, self._blocked_at)

    def _on_error(self, exc: Exception) -> None:
        if not isinstance(exc, self._triggers_on):
            return
        self._failure_count += 1
        if self._failure_count >= self._critical_count:
            self._blocked_at = datetime.now(UTC)
            raise BreakerError(TOO_MUCH, self._func_name, self._blocked_at) from exc


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int,
        time_to_recover: int,
        triggers_on: type[Exception],
    ) -> None:
        errors = []
        if not isinstance(critical_count, int) or isinstance(critical_count, bool) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not isinstance(time_to_recover, int) or isinstance(time_to_recover, bool) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        return _BreakerWrapper(
            func, self.critical_count, self.time_to_recover, self.triggers_on,
        )


circuit_breaker = CircuitBreaker(5, 30, Exception)


def get_comments(post_id: int) -> Any:
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
