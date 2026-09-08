from __future__ import annotations


class Png2SvgError(Exception):
    """Expected domain error with a stable process exit code."""

    exit_code = 9

    def __init__(self, message: str, *, code: str = "INTERNAL_ERROR") -> None:
        super().__init__(message)
        self.code = code


class ConfigurationError(Png2SvgError):
    exit_code = 2


class ImageReadError(Png2SvgError):
    exit_code = 3


class EmptyImageError(Png2SvgError):
    exit_code = 4


class BudgetError(Png2SvgError):
    exit_code = 5


class VectorizationError(Png2SvgError):
    exit_code = 6


class ValidationError(Png2SvgError):
    exit_code = 7


class IntegrationError(Png2SvgError):
    exit_code = 8

