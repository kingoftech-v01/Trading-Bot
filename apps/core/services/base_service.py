"""
Base Service - Abstract base class for all services.

This module provides a base service class that other services can extend.
Services encapsulate business logic and keep views thin.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger('trading_bot')


class BaseService(ABC):
    """
    Abstract base class for all services.

    Services should:
    - Encapsulate business logic
    - Be stateless when possible
    - Handle errors gracefully
    - Log important operations
    """

    def __init__(self):
        self.logger = logger

    def log_info(self, message: str, **kwargs):
        """Log an info message with context."""
        self.logger.info(f"[{self.__class__.__name__}] {message}", extra=kwargs)

    def log_error(self, message: str, exc: Optional[Exception] = None, **kwargs):
        """Log an error message with context."""
        self.logger.error(
            f"[{self.__class__.__name__}] {message}",
            exc_info=exc,
            extra=kwargs
        )

    def log_debug(self, message: str, **kwargs):
        """Log a debug message with context."""
        self.logger.debug(f"[{self.__class__.__name__}] {message}", extra=kwargs)


class ServiceResult:
    """
    Wrapper for service operation results.

    Provides a consistent way to return success/failure status
    along with data or error messages.
    """

    def __init__(
        self,
        success: bool,
        data: Optional[Any] = None,
        error: Optional[str] = None,
        errors: Optional[Dict[str, str]] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.errors = errors or {}

    @classmethod
    def ok(cls, data: Any = None) -> 'ServiceResult':
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str, errors: Optional[Dict[str, str]] = None) -> 'ServiceResult':
        """Create a failed result."""
        return cls(success=False, error=error, errors=errors)

    def __bool__(self) -> bool:
        """Allow using result in boolean context."""
        return self.success
