"""
Lightweight RAG pipeline: embeds WHO/NCDC guidelines at startup,
retrieves top-k matches via cosine similarity for any user query.
If user country matches a guideline's country tag, those results are prioritized.
"""
import json
import numpy as np
from pathlib import Path
from typing import Optional
from sentence_transformers import SentenceTransformer

_MODEL_NAME      = "all-MiniLM-L6-v2"
_GUIDELINES_PATH = Path(__file__).parent.parent / "data" / "guidelines.json"
_TOP_K           = 2

_model:             SentenceTransformer | None = None
_guideline_texts:   list[str]                  = []
_guideline_sources: list[str]                  = []
_guideline_countries: list[str | None]         = []
_embeddings:        np.ndarray | None          = None


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return b_norm @ a_norm


def load_rag_engine() -> None:
    global _model, _guideline_texts, _guideline_sources, _guideline_countries, _embeddings

    with open(_GUIDELINES_PATH, encoding="utf-8") as f:
        guidelines = json.load(f)

    _guideline_texts     = [g["text"] for g in guidelines]
    _guideline_sources   = [g["source"] for g in guidelines]
    _guideline_countries = [g.get("country") for g in guidelines]

    _model      = SentenceTransformer(_MODEL_NAME)
    _embeddings = _model.encode(_guideline_texts, convert_to_numpy=True)


def query_guidelines(question: str, country: Optional[str] = None) -> str:
    if _model is None or _embeddings is None:
        return "Guideline engine not initialized."

    user_country = (country or "").lower().strip()

    q_embedding = _model.encode(question, convert_to_numpy=True)
    scores      = _cosine_similarity(q_embedding, _embeddings).copy()

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
