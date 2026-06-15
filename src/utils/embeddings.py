"""
SteelMind AI Wizard — Embeddings Utility
==========================================
Singleton loader for the embeddings model.
Uses HuggingFace sentence-transformers if available,
otherwise falls back to langchain's fake embeddings for cloud deployments.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Embedding model name
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Singleton instance
_embeddings_instance = None


def get_embeddings():
    """
    Get or create the embeddings model singleton.

    Tries HuggingFace sentence-transformers first (local, high quality).
    Falls back to FakeEmbeddings for cloud deployments where PyTorch is not installed.

    Returns:
        Embeddings instance compatible with langchain
    """
    global _embeddings_instance

    if _embeddings_instance is None:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            logger.info(f"🧠 Loading embedding model: {EMBEDDING_MODEL}")
            _embeddings_instance = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info("✅ HuggingFace embedding model loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ HuggingFace embeddings unavailable ({e}). Using FakeEmbeddings fallback.")
            try:
                from langchain_community.embeddings import FakeEmbeddings
                _embeddings_instance = FakeEmbeddings(size=384)
                logger.info("✅ FakeEmbeddings loaded (cloud fallback mode — RAG results will be approximate)")
            except Exception as e2:
                logger.error(f"❌ Even FakeEmbeddings failed: {e2}")
                raise

    return _embeddings_instance


def embed_text(text: str) -> list:
    """
    Embed a single text string into a vector.

    Args:
        text: Text to embed

    Returns:
        List of floats (384-dimensional vector)
    """
    embeddings = get_embeddings()
    return embeddings.embed_query(text)


def embed_documents(texts: list) -> list:
    """
    Embed a list of text strings into vectors.

    Args:
        texts: List of texts to embed

    Returns:
        List of vectors (each 384-dimensional)
    """
    embeddings = get_embeddings()
    return embeddings.embed_documents(texts)
