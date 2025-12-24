"""Performance monitoring and metrics collection utilities."""

import functools
import logging
import time
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and track performance metrics.

    Tracks execution times, call counts, and other metrics
    for performance analysis and optimization.
    """

    def __init__(self) -> None:
        """Initialize performance monitor."""
        self.metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "errors": 0,
            }
        )

    def record(
        self,
        operation: str,
        duration: float,
        success: bool = True,
    ) -> None:
        """Record a performance metric.

        Args:
            operation: Name of the operation
            duration: Execution duration in seconds
            success: Whether operation succeeded
        """
        metric = self.metrics[operation]
        metric["count"] += 1
        metric["total_time"] += duration
        metric["min_time"] = min(metric["min_time"], duration)
        metric["max_time"] = max(metric["max_time"], duration)

        if not success:
            metric["errors"] += 1

    def get_stats(self, operation: str) -> dict[str, Any]:
        """Get statistics for an operation.

        Args:
            operation: Name of the operation

        Returns:
            Performance statistics
        """
        metric = self.metrics[operation]
        if metric["count"] == 0:
            return {}

        return {
            "operation": operation,
            "count": metric["count"],
            "total_time": f"{metric['total_time']:.3f}s",
            "avg_time": f"{metric['total_time'] / metric['count']:.3f}s",
            "min_time": f"{metric['min_time']:.3f}s",
            "max_time": f"{metric['max_time']:.3f}s",
            "error_rate": f"{(metric['errors'] / metric['count']) * 100:.1f}%",
        }

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all operations.

        Returns:
            Dictionary of all performance statistics
        """
        return {op: self.get_stats(op) for op in self.metrics.keys()}

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(operation_name: str | None = None):
    """Decorator to monitor function performance.

    Args:
        operation_name: Custom name for the operation (defaults to function name)

    Example:
        @monitor_performance("user_creation")
        def create_user(data: UserCreate) -> User:
            # Implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                performance_monitor.record(op_name, duration, success)

                # Log slow operations (> 1 second)
                if duration > 1.0:
                    logger.warning(
                        f"Slow operation detected: {op_name}",
                        extra={"duration": f"{duration:.3f}s"},
                    )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                performance_monitor.record(op_name, duration, success)

                # Log slow operations (> 1 second)
                if duration > 1.0:
                    logger.warning(
                        f"Slow operation detected: {op_name}",
                        extra={"duration": f"{duration:.3f}s"},
                    )

        # Return appropriate wrapper based on function type
        if functools.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_performance_report() -> dict[str, Any]:
    """Get comprehensive performance report.

    Returns:
        Performance statistics for all monitored operations
    """
    stats = performance_monitor.get_all_stats()

    # Sort by average time (slowest first)
    sorted_stats = dict(
        sorted(
            stats.items(),
            key=lambda x: float(x[1].get("avg_time", "0s").rstrip("s")),
            reverse=True,
        )
    )

    return {
        "timestamp": time.time(),
        "operations": sorted_stats,
        "summary": {
            "total_operations": len(sorted_stats),
            "total_calls": sum(s["count"] for s in stats.values()),
        },
    }
