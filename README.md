# unicode-normalization-predicate

Reports which Unicode normalization form (NFC, NFD, NFKC, NFKD) a given string is already in, so callers can skip redundant re-normalization.

```python
from unicode_normalization_predicate import is_normalized, which_forms

# Ask for all four forms at once:
forms = which_forms("\u00e9")              # U+00E9 (precomposed é)
list(forms)                                # -> ['NFC', 'NFKC']
forms.NFC                                  # -> True
forms.NFD                                  # -> False

# Or ask about a single form:
is_normalized("e\u0301", "NFC")            # -> False (decomposed, not NFC)
```

## Why this exists

When ingesting text from many sources, the question "is this string already normalized?" arises repeatedly. Re-normalizing a string that is already in the target form is pure overhead. The standard library exposes `unicodedata.normalize`, which performs the transformation; this library answers the predicate instead, and does so for all four forms in one call so a caller can pick the cheapest acceptable target.

The trade-off: each check delegates to `unicodedata.normalize`, so it pays for a full re-normalization per form. For inputs checked once and discarded this is fine; for hot loops over repeated identical strings, cache the returned `NormalizationForms` (it is frozen and hashable).

## Awkward edge

A string may satisfy several forms at once — `list(which_forms(s))` yields the *names* of every satisfied form, not a single winner. Pure ASCII returns all four. Conversely, a precomposed compatibility character (e.g. `U+FF21` FULLWIDTH LATIN CAPITAL LETTER A) is `NFKC`/`NFKD` but not `NFC`/`NFD`. Do not assume the four booleans collapse to one choice.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

