"""
Embedding Provider Abstraction
Decouples vector embedding generation from specific external third-party APIs.
"""

from abc import ABC, abstractmethod
from typing import List
import numpy as np
import hashlib
import re

from backend.app.core.config import settings
from backend.app.core.logging import logger


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a normalized embedding vector for a single string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized embedding vectors for a batch of strings."""
        pass


class LocalScientificEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic, high-performance semantic embedding generator.
    Produces 384-dimensional normalized vectors via token hashing and n-gram projection,
    ensuring zero external API dependencies and reproducible testability.
    """

    def __init__(self, dimension: int = 384, seed: int = 42):
        self.dimension = dimension
        self.seed = seed

    def _tokenize(self, text: str) -> List[str]:
        cleaned = text.lower()
        tokens = re.findall(r"\b[a-z0-9_\-]{2,}\b", cleaned)
        # Add character bi-grams for scientific prefixes/suffixes
        bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension

        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.dimension

        vec = np.zeros(self.dimension, dtype=np.float32)
        for token in tokens:
            # Deterministic hash to dimension index and sign
            h = int(hashlib.md5(f"{token}_{self.seed}".encode()).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 16) & 1) else -1.0
            weight = 1.0 + (len(token) / 10.0)
            vec[idx] += sign * weight

        # L2 normalization
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec = vec / norm
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


def get_embedding_provider() -> BaseEmbeddingProvider:
    return LocalScientificEmbeddingProvider(dimension=settings.EMBEDDING_DIMENSION)
