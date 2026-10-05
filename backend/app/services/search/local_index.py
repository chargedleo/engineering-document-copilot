import math
import re
from typing import List, Dict, Any, Optional
import numpy as np

from app.services.search.base import BaseSearchIndex, SearchHit


def tokenize(text: str) -> List[str]:
    """Tokenize technical text into lowercase terms, preserving part numbers and units."""
    if not text:
        return []
    return re.findall(r"\b[A-Za-z0-9_\-\.\/+]+\b", text.lower())


class LocalSearchIndex(BaseSearchIndex):
    """
    Lightweight, in-process hybrid search index for local development and tests.

    Supports:
    - BM25 lexical keyword retrieval
    - Dense vector cosine similarity retrieval
    - Hybrid Reciprocal Rank Fusion (RRF)
    - Metadata filtering (document_id, document_type, part_number, revision, page_number)
    """

    def __init__(self):
        # Maps chunk_id -> chunk record
        self._store: Dict[str, Dict[str, Any]] = {}

    def clear(self) -> None:
        self._store.clear()

    async def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        count = 0
        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            self._store[chunk_id] = chunk
            count += 1
        return count

    async def delete_document_chunks(self, document_id: str) -> None:
        to_delete = [
            cid for cid, c in self._store.items()
            if c.get("document_id") == document_id
        ]
        for cid in to_delete:
            del self._store[cid]

    async def search(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        mode: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchHit]:
        candidates = self._apply_filters(list(self._store.values()), filters)
        if not candidates:
            return []

        mode = (mode or "hybrid").lower()

        if mode == "keyword":
            return self._keyword_search(query, candidates, top_k)
        elif mode == "vector":
            if not query_vector:
                return []
            return self._vector_search(query_vector, candidates, top_k)
        elif mode == "hybrid":
            return self._hybrid_search(query, query_vector, candidates, top_k)
        else:
            return self._hybrid_search(query, query_vector, candidates, top_k)

    def _apply_filters(
        self,
        docs: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not filters:
            return docs

        filtered = []
        for d in docs:
            match = True
            for k, val in filters.items():
                if val is None:
                    continue
                doc_val = d.get(k)
                if doc_val is None:
                    meta = d.get("metadata", {})
                    doc_val = meta.get(k)
                if doc_val is None or str(doc_val).lower() != str(val).lower():
                    match = False
                    break
            if match:
                filtered.append(d)
        return filtered

    def _keyword_search(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[SearchHit]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        N = len(candidates)
        avgdl = sum(len(tokenize(c.get("content", ""))) for c in candidates) / (N or 1)
        k1 = 1.5
        b = 0.75

        # Compute document frequencies
        df: Dict[str, int] = {}
        candidate_tokens: Dict[str, List[str]] = {}
        for c in candidates:
            cid = c["chunk_id"]
            toks = tokenize(c.get("content", ""))
            candidate_tokens[cid] = toks
            seen = set(toks)
            for t in query_terms:
                if t in seen:
                    df[t] = df.get(t, 0) + 1

        scores: List[tuple[Dict[str, Any], float]] = []

        for c in candidates:
            cid = c["chunk_id"]
            doc_tokens = candidate_tokens[cid]
            doc_len = len(doc_tokens)
            score = 0.0

            # Count term frequencies in this document
            tf: Dict[str, int] = {}
            for t in doc_tokens:
                tf[t] = tf.get(t, 0) + 1

            for term in query_terms:
                if term in tf:
                    term_df = df.get(term, 0)
                    idf = math.log(1.0 + (N - term_df + 0.5) / (term_df + 0.5))
                    term_tf = tf[term]
                    denom = term_tf + k1 * (1.0 - b + b * (doc_len / (avgdl or 1)))
                    score += idf * (term_tf * (k1 + 1.0)) / (denom or 1)

            if score > 0:
                scores.append((c, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]

        return [
            self._to_hit(doc, score, "keyword")
            for doc, score in top_results
        ]

    def _vector_search(
        self,
        query_vector: List[float],
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[SearchHit]:
        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm < 1e-6:
            return []

        scores: List[tuple[Dict[str, Any], float]] = []

        for c in candidates:
            c_emb = c.get("embedding")
            if not c_emb:
                continue
            doc_vec = np.array(c_emb, dtype=np.float32)
            d_norm = np.linalg.norm(doc_vec)
            if d_norm < 1e-6:
                continue
            sim = float(np.dot(q_vec, doc_vec) / (q_norm * d_norm))
            scores.append((c, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_results = scores[:top_k]

        return [
            self._to_hit(doc, score, "vector")
            for doc, score in top_results
        ]

    def _hybrid_search(
        self,
        query: str,
        query_vector: Optional[List[float]],
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[SearchHit]:
        """
        Reciprocal Rank Fusion (RRF):
        Combines keyword ranks and vector similarity ranks to surface the most relevant chunks.
        """
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {c["chunk_id"]: c for c in candidates}
        RRF_K = 60.0

        # 1. Rank by keyword
        kw_hits = self._keyword_search(query, candidates, top_k=len(candidates))
        for rank, hit in enumerate(kw_hits, start=1):
            rrf_scores[hit.chunk_id] = rrf_scores.get(hit.chunk_id, 0.0) + (1.0 / (RRF_K + rank))

        # 2. Rank by vector if query_vector provided
        if query_vector:
            vec_hits = self._vector_search(query_vector, candidates, top_k=len(candidates))
            for rank, hit in enumerate(vec_hits, start=1):
                rrf_scores[hit.chunk_id] = rrf_scores.get(hit.chunk_id, 0.0) + (1.0 / (RRF_K + rank))

        # Sort candidate IDs by RRF score
        sorted_cids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        return [
            self._to_hit(chunk_map[cid], score, "hybrid")
            for cid, score in sorted_cids
        ]

    def _to_hit(self, doc: Dict[str, Any], score: float, mode: str) -> SearchHit:
        return SearchHit(
            chunk_id=doc["chunk_id"],
            document_id=doc.get("document_id", ""),
            page_id=doc.get("page_id"),
            page_number=doc.get("page_number", 1),
            chunk_index=doc.get("chunk_index", 0),
            filename=doc.get("filename", ""),
            document_type=doc.get("document_type", "SPECIFICATION"),
            part_number=doc.get("part_number"),
            revision=doc.get("revision"),
            content=doc.get("content", ""),
            score=round(float(score), 4),
            retrieval_mode=mode,
            metadata=doc.get("metadata", {})
        )
