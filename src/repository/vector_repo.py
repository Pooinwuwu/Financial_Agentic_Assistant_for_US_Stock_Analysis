import json
from typing import Any, Optional
import numpy as np
from openai import OpenAI
from src.config import settings

class VectorRepository:
    def __init__(self, index_path: str = None, client: Optional[OpenAI] = None):
        self.index_path = str(index_path or settings.SEC_INDEX_PATH)
        self.client = client or OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.chunks: list[dict[str, Any]] = []
        self._load_index()

    def _load_index(self):
        with open(self.index_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
        # Pre-convert embeddings to normalized numpy array
        for item in self.chunks:
            vec = np.array(item["embedding"], dtype=np.float32)
            norm = np.linalg.norm(vec)
            item["norm_vector"] = vec / (norm if norm > 0 else 1.0)

    def embed_query(self, query: str) -> np.ndarray:
        resp = self.client.embeddings.create(
            model="bge-m3",
            input=[query]
        )
        q_vec = np.array(resp.data[0].embedding, dtype=np.float32)
        norm = np.linalg.norm(q_vec)
        return q_vec / (norm if norm > 0 else 1.0)

    def search(
        self,
        query: str,
        top_k: int = 3,
        ticker: Optional[str] = None,
        fiscal_year: Optional[int] = None,
        section: Optional[str] = None,
        min_score: float = 0.45
    ) -> list[dict[str, Any]]:
        """
        Executes query construction pre-filtering and cosine similarity ranking with a min_score floor.
        """
        # 1. Structural Metadata Pre-Filtering
        candidates = self.chunks
        if ticker:
            ticker_upper = ticker.strip().upper()
            candidates = [c for c in candidates if c["ticker"] == ticker_upper]
        if fiscal_year:
            candidates = [c for c in candidates if c["fiscal_year"] == int(fiscal_year)]
        if section:
            sec_clean = section.strip().lower()
            candidates = [c for c in candidates if sec_clean in c.get("section", "").lower() or sec_clean in c.get("title", "").lower()]

        if not candidates:
            # Fallback to all candidates if pre-filter returned empty
            candidates = self.chunks

        # 2. Embedding & Cosine Similarity
        q_norm = self.embed_query(query)
        scored_candidates = []
        for c in candidates:
            sim = float(np.dot(q_norm, c["norm_vector"]))
            if sim >= min_score:
                scored_candidates.append({
                    "id": c["id"],
                    "ticker": c["ticker"],
                    "company": c["company"],
                    "fiscal_year": c["fiscal_year"],
                    "section": c["section"],
                    "title": c["title"],
                    "text": c["text"],
                    "score": round(sim, 4)
                })

        # 3. Sort by descending similarity and take top_k
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]
