import logging
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings
from app.services.search.base import BaseSearchIndex, SearchHit

logger = logging.getLogger("engineering_copilot.search.azure")


class AzureSearchIndex(BaseSearchIndex):
    """
    Azure AI Search implementation of BaseSearchIndex.
    Uses official REST endpoints for hybrid retrieval.
    Requires AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None,
        api_version: str = "2023-11-01",
    ):
        self.endpoint = (endpoint or settings.AZURE_SEARCH_ENDPOINT or "").rstrip("/")
        self.api_key = api_key or settings.AZURE_SEARCH_API_KEY or ""
        self.index_name = (
            index_name
            or settings.AZURE_SEARCH_DOCUMENTS_INDEX_NAME
            or settings.AZURE_SEARCH_INDEX_NAME
            or "engineering-docs-index"
        )
        self.api_version = api_version

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    async def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        if not self.is_configured():
            raise ValueError(
                "Azure AI Search is not configured. Set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY in .env."
            )

        url = f"{self.endpoint}/indexes/{self.index_name}/docs/index?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        actions = []
        for c in chunks:
            action: Dict[str, Any] = {
                "@search.action": "mergeOrUpload",
                "id": str(c["chunk_id"]),
                "document_id": str(c["document_id"]),
                "page_id": str(c.get("page_id") or ""),
                "chunk_index": int(c.get("chunk_index", 0)),
                "page_number": int(c.get("page_number", 1)),
                "filename": str(c.get("filename", "")),
                "document_type": str(c.get("document_type", "SPECIFICATION")),
                "part_number": str(c.get("part_number") or ""),
                "revision": str(c.get("revision") or ""),
                "content": str(c.get("content", "")),
            }
            if c.get("embedding"):
                action["embedding"] = c["embedding"]
            actions.append(action)

        payload = {"value": actions}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return len(data.get("value", []))

    async def delete_document_chunks(self, document_id: str) -> None:
        if not self.is_configured():
            logger.warning("Azure AI Search not configured; skipping chunk deletion.")
            return

        # Query chunk IDs matching document_id
        search_url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        search_payload = {
            "search": "*",
            "filter": f"document_id eq '{document_id}'",
            "select": "id",
            "top": 1000,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(search_url, headers=headers, json=search_payload)
            if resp.status_code != 200:
                logger.error(f"Failed to find chunks for deletion in Azure Search: {resp.text}")
                return

            results = resp.json().get("value", [])
            if not results:
                return

            actions = [{"@search.action": "delete", "id": item["id"]} for item in results]
            del_url = f"{self.endpoint}/indexes/{self.index_name}/docs/index?api-version={self.api_version}"
            del_resp = await client.post(del_url, headers=headers, json={"value": actions})
            del_resp.raise_for_status()

    async def search(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        mode: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchHit]:
        if not self.is_configured():
            raise ValueError(
                "Azure AI Search is not configured. Set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY in .env."
            )

        url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version={self.api_version}"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        mode = (mode or "hybrid").lower()
        payload: Dict[str, Any] = {
            "top": top_k,
            "count": True,
        }

        # Build filter string
        filter_exprs = []
        if filters:
            for k, val in filters.items():
                if val is not None:
                    # Escape single quotes
                    safe_val = str(val).replace("'", "''")
                    filter_exprs.append(f"{k} eq '{safe_val}'")
        if filter_exprs:
            payload["filter"] = " and ".join(filter_exprs)

        if mode == "keyword":
            payload["search"] = query or "*"
        elif mode == "vector":
            if not query_vector:
                return []
            payload["vectors"] = [
                {
                    "value": query_vector,
                    "fields": "embedding",
                    "k": top_k,
                }
            ]
        else:  # hybrid
            payload["search"] = query or "*"
            if query_vector:
                payload["vectors"] = [
                    {
                        "value": query_vector,
                        "fields": "embedding",
                        "k": top_k,
                    }
                ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            hits = []
            for item in data.get("value", []):
                score = float(item.get("@search.score", 0.0))
                hits.append(
                    SearchHit(
                        chunk_id=item.get("id", ""),
                        document_id=item.get("document_id", ""),
                        page_id=item.get("page_id") or None,
                        page_number=int(item.get("page_number", 1)),
                        chunk_index=int(item.get("chunk_index", 0)),
                        filename=item.get("filename", ""),
                        document_type=item.get("document_type", "SPECIFICATION"),
                        part_number=item.get("part_number") or None,
                        revision=item.get("revision") or None,
                        content=item.get("content", ""),
                        score=round(score, 4),
                        retrieval_mode=mode,
                        metadata={
                            k: v for k, v in item.items()
                            if not k.startswith("@") and k not in ("id", "content", "embedding")
                        },
                    )
                )
            return hits
