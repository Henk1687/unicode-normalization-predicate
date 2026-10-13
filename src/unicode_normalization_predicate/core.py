"""Core logic for reporting which Unicode normalization forms a string satisfies.

Design decisions
----------------
This module deliberately returns a small frozen dataclass (``NormalizationForms``)
rather than a plain ``set`` or ``list``. A frozen dataclass is hashable, so callers
can cache results in a ``set``/``dict`` keyed by the value, which matters when
normalization status is checked repeatedly for the same input (e.g. streaming
text where each chunk is inspected). Returning a structured object with named
fields also keeps intent obvious at call sites compared to positional booleans.

We re-``normalize`` the input once per form (NFC, NFD, NFKC, NFKD) and compare.
``unicodedata.normalize`` is the Python standard library implementation of
UAX #15, so correctness is delegated to CPython. The cost is four full
re-normalizations per query when every flag is requested; callers who only need
one or two forms should pass the ``forms`` argument to avoid the rest.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Iterable
from typing import Iterator

#: The four Unicode normalization forms, in stable alphabetical order by short name.
ALL_FORMS: tuple[str, ...] = ("NFC", "NFD", "NFKC", "NFKD")


class UnknownFormError(ValueError):
    """Raised when a form name is requested that is not one of NFC, NFD, NFKC, NFKD."""


@dataclass(frozen=True)
class NormalizationForms:
    """Immutable record of which normalization forms a string already satisfies.

    Each attribute is ``True`` when the inspected string is already in the
corresponding form and thus re-normalization to that form is a no-op.
    """

    NFC: bool
    NFD: bool
    NFKC: bool
    NFKD: bool

    def __iter__(self) -> Iterator[str]:
        """Iterate the form names that are ``True``, in ``ALL_FORMS`` order.

        Iteration yields the *names* of the satisfied forms, not booleans, so
        ``list(forms)`` reads naturally as ``['NFC', 'NFD']``.
        """
        for form in ALL_FORMS:
            if getattr(self, form):
                yield form

    def __bool__(self) -> bool:
        """Truthy when the string satisfies at least one normalization form."""
        return any(getattr(self, f) for f in ALL_FORMS)


def _validate_forms(forms: Iterable[str]) -> list[str]:
    """Return a list of validated, uppercased form names from the input iterable."""
    out: list[str] = []
    for f in forms:
        if not isinstance(f, str):
            raise UnknownFormError(
                "Form names must be strings; got " + type(f).__name__,
            )
        fu = f.upper()
        if fu not in ALL_FORMS:
            raise UnknownFormError(
                "Unknown normalization form: " + repr(f) +
                ". Expected one of " + ", ".join(ALL_FORMS) + ".",
            )
        out.append(fu)
    if not out:
        raise UnknownFormError("At least one form must be requested.")
    return out


def which_forms(text: str, forms: Iterable[str] | None = None) -> NormalizationForms:
    """Report which of the four Unicode normalization forms ``text`` already satisfies.

    Args:
        text: The string to inspect.
        forms: Optional iterable of form names to check. Defaults to all four.
            Accepted case-insensitively (``nfc`` and ``NFC`` are identical).

    Returns:
        A :class:`NormalizationForms` with ``True`` for each requested form that
        ``text`` already satisfies and ``False`` for each requested form it does
        not. Non-requested forms are reported ``False``.

    Raises:
        TypeError: if ``text`` is not a ``str``.
        UnknownFormError: if ``forms`` is empty or contains an unknown name.

    Edge cases:
        * Empty and ASCII-only strings satisfy all four forms.
        * A string may satisfy multiple forms at once — the returned object is
          a record of four independent booleans, not a single choice.
    """
    if not isinstance(text, str):
        raise TypeError(
            "text must be a str; got " + type(text).__name__,
        )

    requested = _validate_forms(forms) if forms is not None else list(ALL_FORMS)

    flags: dict[str, bool] = {f: False for f in ALL_FORMS}
    for form in requested:
        flags[form] = unicodedata.normalize(form, text) == text

    return NormalizationForms(
        NFC=flags["NFC"],
        NFD=flags["NFD"],
        NFKC=flags["NFKC"],
        NFKD=flags["NFKD"],
    )


def is_normalized(text: str, form: str) -> bool:
    """Return ``True`` iff ``text`` is already in ``form``.

    Convenience wrapper around :func:`which_forms` for callers who only care
    about a single form. ``form`` is matched case-insensitively.

    Raises:
        TypeError: if ``text`` is not a ``str``.
        UnknownFormError: if ``form`` is not one of NFC, NFD, NFKC, NFKD.
    """
    return getattr(which_forms(text, [form]), form.upper())
