"""Package entry point for unicode_normalization_predicate."""

from .core import (
    NormalizationForms,
    is_normalized,
    which_forms,
)

__all__ = [
    "NormalizationForms",
    "is_normalized",
    "which_forms",
]
