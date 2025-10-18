"""
Qdrant Vector Database Client
"""

from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)
import logging

logger = logging.getLogger(__name__)


class VectorDatabase:
    """Wrapper for Qdrant vector database"""

    def __init__(
        self,
        host: str,
        port: int = 6333,
        api_key: Optional[str] = None,
        collection_name: str = "valyrion_documents",
        vector_size: int = 3072,  # OpenAI text-embedding-3-large
    ):
        """
        Initialize Qdrant client

        Args:
            host: Qdrant server host
            port: Qdrant server port
            api_key: API key for Qdrant Cloud (optional)
            collection_name: Name of the collection
            vector_size: Dimension of embeddings
        """
        self.client = QdrantClient(host=host, port=port, api_key=api_key)
        self.collection_name = collection_name
        self.vector_size = vector_size

        # Create collection if it doesn't exist
        self._initialize_collection()

    def _initialize_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise

    def upsert_chunks(
        self, chunk_ids: List[str], embeddings: List[List[float]], metadata: List[Dict]
    ) -> bool:
        """
        Upsert document chunks with embeddings

        Args:
            chunk_ids: List of unique chunk IDs
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries

        Returns:
            bool: Success status
        """
        try:
            points = [
                PointStruct(id=chunk_id, vector=embedding, payload=meta)
                for chunk_id, embedding, meta in zip(chunk_ids, embeddings, metadata)
            ]

            self.client.upsert(collection_name=self.collection_name, points=points)

            logger.info(f"Upserted {len(points)} chunks to Qdrant")
            return True
        except Exception as e:
            logger.error(f"Error upserting chunks: {e}")
            return False

    def search(
        self,
        query_vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 50,
        score_threshold: float = 0.7,
    ) -> List[Dict]:
        """
        Search for similar vectors

        Args:
            query_vector: Query embedding vector
            filters: Metadata filters (company, date range, etc.)
            top_k: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            List of results with metadata
        """
        try:
            # Build Qdrant filter
            qdrant_filter = self._build_filter(filters) if filters else None

            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                score_threshold=score_threshold,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "id": result.id,
                        "score": result.score,
                        "metadata": result.payload,
                        "text": result.payload.get("text", ""),
                    }
                )

            logger.info(f"Found {len(formatted_results)} results from Qdrant")
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []

    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from dictionary"""
        conditions = []

        # Company filter
        if "company" in filters:
            conditions.append(
                FieldCondition(
                    key="company_ticker", match=MatchValue(value=filters["company"])
                )
            )

        # Document type filter
        if "document_type" in filters:
            conditions.append(
                FieldCondition(
                    key="document_type", match=MatchValue(value=filters["document_type"])
                )
            )

        # Date range filter
        if "date_from" in filters or "date_to" in filters:
            date_range = {}
            if "date_from" in filters:
                date_range["gte"] = filters["date_from"]
            if "date_to" in filters:
                date_range["lte"] = filters["date_to"]

            conditions.append(
                FieldCondition(key="filing_date", range=Range(**date_range))
            )

        return Filter(must=conditions) if conditions else None

    def delete_by_document_id(self, document_id: str) -> bool:
        """Delete all chunks belonging to a document"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=document_id)
                        )
                    ]
                ),
            )
            logger.info(f"Deleted chunks for document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False

    def get_collection_info(self) -> Dict:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
