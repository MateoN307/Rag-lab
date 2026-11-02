import math

import ollama

EMBED_MODEL = "nomic-embed-text"


def embed_text(text: str) -> list[float]:
    """
    Return the embedding vector for `text`, using Ollama's local
    `nomic-embed-text` model (768-dim, mean-pooled).
    """
    if not text:
        raise ValueError("Cannot embed empty text")

    response = ollama.embed(model=EMBED_MODEL, input=text)
    return response["embeddings"][0]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Return the cosine similarity between two equal-length vectors:
        (A . B) / (||A|| * ||B||)
    Implemented from scratch -- dot product, magnitudes, division.
    """
    if not vec_a or not vec_b:
        raise ValueError("Cannot compute cosine similarity of an empty vector")
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must be the same length")

    mag_a = _magnitude(vec_a)
    mag_b = _magnitude(vec_b)
    if mag_a == 0 or mag_b == 0:
        raise ValueError("Cannot compute cosine similarity of a zero vector")

    return _dot_product(vec_a, vec_b) / (mag_a * mag_b)


#### Private helpers ####

def _dot_product(vec_a: list[float], vec_b: list[float]) -> float:
    """Sum of the products of corresponding elements: A[0]*B[0] + A[1]*B[1] + ..."""
    return sum(a * b for a, b in zip(vec_a, vec_b))


def _magnitude(vec: list[float]) -> float:
    """Length of the vector: sqrt(vec[0]^2 + vec[1]^2 + ...)"""
    return math.sqrt(sum(x ** 2 for x in vec))


#### Tests ####

def _compare_sentences():
    sentence_a = input("Enter the first sentence: ")
    sentence_b = input("Enter the second sentence: ")

    vec_a = embed_text(sentence_a)
    vec_b = embed_text(sentence_b)

    print(f"Cosine similarity: {cosine_similarity(vec_a, vec_b)}")
    print(f"Magnitude A: {_magnitude(vec_a)}")
    print(f"Magnitude B: {_magnitude(vec_b)}")
    print(f"Dot product: {_dot_product(vec_a, vec_b)}")
    print(f"Vector A (first 20 values): {vec_a[:20]}")
    print(f"Vector B (first 20 values): {vec_b[:20]}")


if __name__ == "__main__":
    _compare_sentences()
