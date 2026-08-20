"""Embedding generation for semantic clustering of qualitative extracted reasons."""

import os
import hashlib
import logging
from typing import List, Dict, Optional, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

from app.config import settings

logger = logging.getLogger("pulse.aggregation.embeddings")


class EmbeddingGenerator:
    """Computes dense vector representations for qualitative extraction reasons.
    
    Supports Google Gemini 'text-embedding-004' via google-genai SDK, with
    an in-memory cache and a deterministic TF-IDF / LSA fallback for offline/test execution.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-004"):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model
        self._cache: Dict[str, np.ndarray] = {}
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize genai client for embeddings: {e}")
                self._client = None
        return self._client

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()

    def generate_embeddings(self, texts: List[str], batch_size: int = 50) -> np.ndarray:
        """Generate dense unit-normalized embedding matrix for a list of texts.
        
        Args:
            texts: List of reason texts to embed.
            batch_size: Batch size for Gemini API calls.
            
        Returns:
            np.ndarray of shape (len(texts), embedding_dim) unit normalized.
        """
        if not texts:
            return np.empty((0, 768), dtype=np.float32)

        # Check what needs computation vs what's in cache
        uncached_indices = []
        uncached_texts = []
        result_embeddings = [None] * len(texts)

        for idx, text in enumerate(texts):
            h = self._get_hash(text)
            if h in self._cache:
                result_embeddings[idx] = self._cache[h]
            else:
                uncached_indices.append(idx)
                uncached_texts.append(text)

        if not uncached_texts:
            return np.vstack(result_embeddings)

        # Try Gemini text-embedding-004 first if client is available
        computed_vectors = []
        used_gemini = False

        if self.client and len(uncached_texts) <= 200:
            try:
                logger.info(f"Generating embeddings via Gemini ({self.model}) for {len(uncached_texts)} texts...")
                for i in range(0, len(uncached_texts), batch_size):
                    batch = uncached_texts[i : i + batch_size]
                    
                    # Gemini embed content call
                    try:
                        resp = self.client.models.embed_content(
                            model=self.model,
                            contents=batch,
                        )
                        # Extract embedding vectors
                        if hasattr(resp, "embeddings") and resp.embeddings:
                            for item in resp.embeddings:
                                vec = np.array(item.values, dtype=np.float32)
                                norm = np.linalg.norm(vec)
                                if norm > 0:
                                    vec = vec / norm
                                computed_vectors.append(vec)
                        elif hasattr(resp, "embedding") and resp.embedding:
                            vec = np.array(resp.embedding.values, dtype=np.float32)
                            norm = np.linalg.norm(vec)
                            if norm > 0:
                                vec = vec / norm
                            computed_vectors.append(vec)
                    except Exception as batch_err:
                        logger.warning(f"Gemini embedding batch call failed: {batch_err}. Falling back to TF-IDF.")
                        break

                if len(computed_vectors) == len(uncached_texts):
                    used_gemini = True
            except Exception as e:
                logger.warning(f"Gemini embedding failed: {e}. Utilizing fallback embedding.")

        # Fallback to TF-IDF + TruncatedSVD if Gemini wasn't used or completed
        if not used_gemini:
            logger.info(f"Generating {len(texts)} embeddings via TF-IDF + SVD semantic vectorizer fallback.")
            computed_matrix = self._compute_tfidf_embeddings(texts)
            # Cache all
            for idx, text in enumerate(texts):
                h = self._get_hash(text)
                self._cache[h] = computed_matrix[idx]
            return computed_matrix

        # If Gemini succeeded, populate cache and full array
        for idx, text in zip(uncached_indices, uncached_texts):
            vec = computed_vectors.pop(0)
            h = self._get_hash(text)
            self._cache[h] = vec
            result_embeddings[idx] = vec

        return np.vstack(result_embeddings)

    def _compute_tfidf_embeddings(self, texts: List[str]) -> np.ndarray:
        """Deterministic TF-IDF + SVD unit-normalized embedding fallback."""
        if len(texts) == 1:
            return np.ones((1, 64), dtype=np.float32) / np.sqrt(64)

        vectorizer = TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 2),
            stop_words="english",
            min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Reduce dimensionality to 64 or min(features, n_samples - 1)
        n_components = min(64, tfidf_matrix.shape[1], max(2, len(texts) - 1))
        if tfidf_matrix.shape[1] > n_components and n_components >= 2:
            svd = TruncatedSVD(n_components=n_components, random_state=42)
            dense_vectors = svd.fit_transform(tfidf_matrix)
        else:
            dense_vectors = tfidf_matrix.toarray().astype(np.float32)

        # Normalize to unit vectors
        norms = np.linalg.norm(dense_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return (dense_vectors / norms).astype(np.float32)


# Global singleton
embedding_generator = EmbeddingGenerator()
