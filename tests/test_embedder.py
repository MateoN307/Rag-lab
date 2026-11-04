import math

import pytest

from embedder import _dot_product, _magnitude, cosine_similarity

# Pure vector math only: nothing here calls Ollama. Small 2D/3D vectors whose
# answers can be checked by hand. Results that go through a square root or a
# division are compared with pytest.approx (floats aren't stored exactly);
# integer-only results use plain ==.


#### cosine_similarity: values ####

# Each case is (vector a, vector b, expected cosine similarity).
COSINE_VALUE_CASES = {
    "scaled_same_direction": ([2, 2], [5, 5], 1.0),
    "identical": ([3, 4], [3, 4], 1.0),
    "perpendicular": ([1, 0], [0, 5], 0.0),
    "opposite": ([1, 2], [-1, -2], -1.0),
    "in_between": ([3, 4], [4, 3], 0.96),
    "three_dimensions": (
        [1, 2, 3],
        [4, 5, 6],
        32 / (math.sqrt(14) * math.sqrt(77)),
    ),
}


@pytest.mark.parametrize(
    "vec_a, vec_b, expected",
    COSINE_VALUE_CASES.values(),
    ids=COSINE_VALUE_CASES.keys(),
)
def test_cosine_similarity(vec_a, vec_b, expected):
    assert cosine_similarity(vec_a, vec_b) == pytest.approx(expected)


#### cosine_similarity: errors ####

# Each case is (vector a, vector b, text the error message must contain).
# All three checks raise ValueError, so `match` proves which one fired.
COSINE_ERROR_CASES = {
    "a_empty": ([], [1, 2], "empty"),
    "b_empty": ([1, 2], [], "empty"),
    "both_empty": ([], [], "empty"),
    "different_lengths": ([1, 2, 3], [1, 2], "same length"),
    "a_zero_vector": ([0, 0], [1, 2], "zero vector"),
    "b_zero_vector": ([1, 2], [0, 0], "zero vector"),
}


@pytest.mark.parametrize(
    "vec_a, vec_b, message",
    COSINE_ERROR_CASES.values(),
    ids=COSINE_ERROR_CASES.keys(),
)
def test_cosine_similarity_errors(vec_a, vec_b, message):
    with pytest.raises(ValueError, match=message):
        cosine_similarity(vec_a, vec_b)


#### _magnitude ####

# Each case is (vector, expected length).
MAGNITUDE_CASES = {
    "zero_vector": ([0, 0], 0.0),
    "three_four_five": ([3, 4], 5.0),
    "negative_entries": ([-3, -4], 5.0),
    "diagonal": ([1, 1], math.sqrt(2)),
}


@pytest.mark.parametrize(
    "vec, expected",
    MAGNITUDE_CASES.values(),
    ids=MAGNITUDE_CASES.keys(),
)
def test_magnitude(vec, expected):
    assert _magnitude(vec) == pytest.approx(expected)


#### _dot_product ####

# Each case is (vector a, vector b, expected dot product). Integers only, so
# the result is exact and plain == is safe.
DOT_PRODUCT_CASES = {
    "perpendicular": ([1, 0], [0, 5], 0),
    "same_direction": ([2, 2], [5, 5], 20),
    "opposite": ([1, 2], [-1, -2], -5),
    "zero_vector": ([3, 4], [0, 0], 0),
    "three_dimensions": ([1, 2, 3], [4, 5, 6], 32),
}


@pytest.mark.parametrize(
    "vec_a, vec_b, expected",
    DOT_PRODUCT_CASES.values(),
    ids=DOT_PRODUCT_CASES.keys(),
)
def test_dot_product(vec_a, vec_b, expected):
    assert _dot_product(vec_a, vec_b) == expected
