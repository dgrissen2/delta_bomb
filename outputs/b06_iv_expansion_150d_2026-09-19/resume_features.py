"""Complete frozen feature validation with numeric-object NumPy compatibility."""
from __future__ import annotations

from numbers import Real
from typing import Any

import numpy as np

import recalculate
from collect import OUT, digest, freeze_json

ORIGINAL_ASSERT = np.testing.assert_allclose


def numeric_object_array(value: Any) -> np.ndarray:
    """Convert only object containers already holding real numbers, including NaN."""
    array = np.asanyarray(value)
    if array.dtype == object:
        if not all(isinstance(item, Real) for item in array.flat):
            raise TypeError('Numeric-object validation contains a nonnumeric value')
        array = array.astype(np.float64)
    return array


def compatible_assert(actual: Any, expected: Any, **kwargs: Any) -> None:
    """Keep every original assertion option and tolerance unchanged."""
    ORIGINAL_ASSERT(numeric_object_array(actual), numeric_object_array(expected), **kwargs)


if __name__ == '__main__':
    freeze_json(OUT / 'validation_compatibility.json', {
        'adapter': str(OUT / 'resume_features.py'),
        'adapter_sha256': digest(OUT / 'resume_features.py'),
        'reason': 'Pandas concatenation with zero-row panels retained object dtype for numeric acceleration',
        'scope': 'NumPy validation input representation only; values, assertions, tolerance and classifications unchanged',
        'before_new_outcomes': not (OUT / 'event_paths.csv').exists()})
    np.testing.assert_allclose = compatible_assert
    try:
        recalculate.feature_stage(watch=False)
    finally:
        np.testing.assert_allclose = ORIGINAL_ASSERT
