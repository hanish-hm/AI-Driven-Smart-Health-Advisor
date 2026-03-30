"""
Lightweight RAG pipeline: embeds WHO/NCDC guidelines at startup,
retrieves top-k matches via cosine similarity for any user query.
If user country matches a guideline's country tag, those results are prioritized.
"""
import json
import logging
import threading
import numpy as np
from pathlib import Path
from typing import Optional
from sentence_transformers import SentenceTransformer

_MODEL_NAME      = "all-MiniLM-L6-v2"
_GUIDELINES_PATH = Path(__file__).parent.parent / "data" / "guidelines.json"
_TOP_K           = 2
_UNAVAILABLE_MESSAGE = (
    "Guideline-based advice is temporarily unavailable. "
    "Please try again later."
)

logger = logging.getLogger(__name__)

_model:             SentenceTransformer | None = None
_guideline_texts:   list[str]                  = []
_guideline_sources: list[str]                  = []
_guideline_countries: list[str | None]         = []
_embeddings:        np.ndarray | None          = None
_state_lock = threading.RLock()
_load_in_progress = False


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return b_norm @ a_norm


def load_rag_engine() -> None:
    global _model, _guideline_texts, _guideline_sources, _guideline_countries, _embeddings, _load_in_progress

    with open(_GUIDELINES_PATH, encoding="utf-8") as f:
        guidelines = json.load(f)

    with _state_lock:
        _load_in_progress = True
        model = _model

    try:
        if model is None:
            model = SentenceTransformer(_MODEL_NAME)

        guideline_texts = [g["text"] for g in guidelines]
        guideline_sources = [g["source"] for g in guidelines]
        guideline_countries = [g.get("country") for g in guidelines]
        embeddings = model.encode(guideline_texts, convert_to_numpy=True)

        with _state_lock:
            _model = model
            _guideline_texts = guideline_texts
            _guideline_sources = guideline_sources
            _guideline_countries = guideline_countries
            _embeddings = embeddings
    finally:
        with _state_lock:
            _load_in_progress = False


def _background_load() -> None:
    try:
        load_rag_engine()
        logger.info("RAG engine loaded successfully.")
    except Exception as e:
        logger.exception("Background RAG load failed: %s", e)


def warm_rag_engine_async() -> None:
    with _state_lock:
        if (_model is not None and _embeddings is not None) or _load_in_progress:
            return

    threading.Thread(target=_background_load, daemon=True, name="rag-loader").start()


def query_guidelines(question: str, country: Optional[str] = None) -> str:
    with _state_lock:
        if _model is None or _embeddings is None:
            warm_rag_engine_async()
            return _UNAVAILABLE_MESSAGE

    with _state_lock:
        user_country = (country or "").lower().strip()

        q_embedding = _model.encode(question, convert_to_numpy=True)
        scores = _cosine_similarity(q_embedding, _embeddings).copy()

        # Boost score for guidelines matching user's country
        if user_country:
            for i, gc in enumerate(_guideline_countries):
                if gc and gc.lower() == user_country:
                    scores[i] += 0.3  # boost country-specific guidelines to top

        top_indices = np.argsort(scores)[::-1][:_TOP_K]

        results = []
        for idx in top_indices:
            results.append(f"[{_guideline_sources[idx]}]\n{_guideline_texts[idx]}")

        return "\n\n".join(results)
