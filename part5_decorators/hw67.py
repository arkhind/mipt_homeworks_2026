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
        failure_count = 0
        blocked_at: datetime | None = None

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal failure_count, blocked_at

            func_name = f"{func.__module__}.{func.__name__}"

            if blocked_at is not None:
                now = datetime.now(UTC)
                elapsed = (now - blocked_at).total_seconds()
                if elapsed >= self.time_to_recover:
                    blocked_at = None
                    failure_count = 0
                else:
                    raise BreakerError(TOO_MUCH, func_name, blocked_at)

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, self.triggers_on):
                    failure_count += 1
                    if failure_count >= self.critical_count:
                        blocked_at = datetime.now(UTC)
                        raise BreakerError(TOO_MUCH, func_name, blocked_at) from e
                raise
            else:
                failure_count = 0
                return result

        return wrapper  # type: ignore[return-value]


circuit_breaker = CircuitBreaker(5, 30, Exception)


def get_comments(post_id: int) -> Any:
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
