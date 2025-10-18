"""
Unit tests for Qdrant Vector Database client
"""

import pytest
from unittest.mock import Mock, patch
from valyrion.rag.storage.vector_db import VectorDatabase


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client"""
    with patch("valyrion.rag.storage.vector_db.QdrantClient") as mock:
        yield mock


def test_vector_db_initialization(mock_qdrant_client):
    """Test VectorDatabase initialization"""
    db = VectorDatabase(host="localhost", port=6333)

    assert db.collection_name == "valyrion_documents"
    assert db.vector_size == 3072
    mock_qdrant_client.assert_called_once()


def test_upsert_chunks(mock_qdrant_client):
    """Test upserting chunks to vector database"""
    db = VectorDatabase(host="localhost")

    chunk_ids = ["chunk_1", "chunk_2"]
    embeddings = [[0.1] * 3072, [0.2] * 3072]
    metadata = [
        {"text": "Sample text 1", "company": "AAPL"},
        {"text": "Sample text 2", "company": "MSFT"},
    ]

    result = db.upsert_chunks(chunk_ids, embeddings, metadata)

    assert result == True
    db.client.upsert.assert_called_once()


def test_search(mock_qdrant_client):
    """Test vector similarity search"""
    db = VectorDatabase(host="localhost")

    # Mock search results
    mock_result = Mock()
    mock_result.id = "chunk_1"
    mock_result.score = 0.95
    mock_result.payload = {"text": "Sample text", "company": "AAPL"}

    db.client.search.return_value = [mock_result]

    query_vector = [0.1] * 3072
    results = db.search(query_vector, filters={"company": "AAPL"}, top_k=10)

    assert len(results) == 1
    assert results[0]["id"] == "chunk_1"
    assert results[0]["score"] == 0.95
    assert results[0]["metadata"]["company"] == "AAPL"


def test_delete_by_document_id(mock_qdrant_client):
    """Test deleting chunks by document ID"""
    db = VectorDatabase(host="localhost")

    result = db.delete_by_document_id("doc_123")

    assert result == True
    db.client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_search_with_filters(mock_qdrant_client):
    """Test search with metadata filters"""
    db = VectorDatabase(host="localhost")

    filters = {"company": "AAPL", "date_from": "2023-01-01", "date_to": "2023-12-31"}

    query_vector = [0.1] * 3072
    results = db.search(query_vector, filters=filters)

    # Verify filter was applied
    db.client.search.assert_called_once()
    call_args = db.client.search.call_args

    assert call_args.kwargs["query_filter"] is not None
