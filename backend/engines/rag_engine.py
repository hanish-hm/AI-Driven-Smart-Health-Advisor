"""
Lightweight RAG pipeline: embeds WHO/NCDC guidelines at startup,
retrieves top-k matches via cosine similarity for any user query.
If user country matches a guideline's country tag, those results are prioritized.
"""
import json
import logging
import re
import numpy as np
from pathlib import Path
from typing import Optional

_MODEL_NAME      = "all-MiniLM-L6-v2"
_GUIDELINES_PATH = Path(__file__).parent.parent / "data" / "guidelines.json"
_TOP_K           = 2
_UNAVAILABLE_MESSAGE = (
    "Guideline-based advice is temporarily unavailable. "
    "Please try again later."
)

logger = logging.getLogger(__name__)

_model:             object | None              = None
_guideline_texts:   list[str]                  = []
_guideline_sources: list[str]                  = []
_guideline_countries: list[str | None]         = []
_embeddings:        np.ndarray | None          = None


def _load_guidelines_from_disk() -> list[dict]:
    with open(_GUIDELINES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return b_norm @ a_norm


def load_rag_engine() -> None:
    global _model, _guideline_texts, _guideline_sources, _guideline_countries, _embeddings

    from sentence_transformers import SentenceTransformer

    guidelines = _load_guidelines_from_disk()
    model = _model or SentenceTransformer(_MODEL_NAME)

    guideline_texts = [g["text"] for g in guidelines]
    guideline_sources = [g["source"] for g in guidelines]
    guideline_countries = [g.get("country") for g in guidelines]
    embeddings = model.encode(guideline_texts, convert_to_numpy=True)

    _model = model
    _guideline_texts = guideline_texts
    _guideline_sources = guideline_sources
    _guideline_countries = guideline_countries
    _embeddings = embeddings
    logger.info("Embedding-based guideline engine loaded successfully.")


def _query_guidelines_lexical(question: str, country: Optional[str] = None) -> str:
    guidelines = _load_guidelines_from_disk()
    user_country = (country or "").lower().strip()
    query_tokens = _tokenize(question)

    scored = []
    for guideline in guidelines:
        text = guideline.get("text", "")
        source = guideline.get("source", "Guideline")
        guideline_country = (guideline.get("country") or "").lower().strip()
        text_tokens = _tokenize(text)

        overlap = len(query_tokens & text_tokens)
        score = float(overlap)

        if user_country and guideline_country == user_country:
            score += 2.0

        if score > 0:
            scored.append((score, source, text))

    if not scored:
        fallback = guidelines[:_TOP_K]
        return "\n\n".join(
            f"[{item.get('source', 'Guideline')}]\n{item.get('text', '')}"
            for item in fallback
        ) or _UNAVAILABLE_MESSAGE

    scored.sort(key=lambda item: item[0], reverse=True)
    top_results = scored[:_TOP_K]
    return "\n\n".join(f"[{source}]\n{text}" for _, source, text in top_results)


def query_guidelines(question: str, country: Optional[str] = None) -> str:
    if _model is None or _embeddings is None:
        return _query_guidelines_lexical(question, country)

    user_country = (country or "").lower().strip()
    q_embedding = _model.encode(question, convert_to_numpy=True)
    scores = _cosine_similarity(q_embedding, _embeddings).copy()

    if user_country:
        for i, gc in enumerate(_guideline_countries):
            if gc and gc.lower() == user_country:
                scores[i] += 0.3

    top_indices = np.argsort(scores)[::-1][:_TOP_K]
    results = []
    for idx in top_indices:
        results.append(f"[{_guideline_sources[idx]}]\n{_guideline_texts[idx]}")

    return "\n\n".join(results)
