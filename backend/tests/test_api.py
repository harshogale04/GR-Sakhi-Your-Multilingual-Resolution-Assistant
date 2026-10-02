"""
Updated Stage 1 API smoke tests — adjusted for Stage 2 changes:
- /documents now returns PaginatedDocumentsResponse (not a plain list)
- /upload returns DocumentUploadResponse with status PROCESSING
- Stats includes completed_documents and failed_documents
"""
import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_documents_list_and_stats():
    # Paginated response
    res = client.get("/api/v1/documents")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data, f"Expected 'items' key in response, got: {data}"
    assert "total" in data
    assert isinstance(data["items"], list)

    # Stats includes canonical COMPLETED + backwards-compat indexed_documents
    stats_res = client.get("/api/v1/documents/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_documents" in stats
    assert "total_chunks" in stats
    assert "indexed_documents" in stats
    assert "completed_documents" in stats
    assert "failed_documents" in stats


def test_search_endpoint():
    payload = {
        "query": "कृषी योजना आणि अनुदान",
        "language": "mr",
        "top_k": 5,
    }
    res = client.post("/api/v1/search", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert "total" in data
    assert data["query"] == "कृषी योजना आणि अनुदान"
    assert data["language"] == "mr"


def test_chat_endpoint():
    payload = {
        "query": "महाराष्ट्र शासन निर्णयांची माहिती सांगा",
        "language": "mr",
    }
    res = client.post("/api/v1/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert data["role"] == "assistant"
    assert "content" in data
    assert "citations" in data
    assert data["language"] == "mr"


def test_upload_validation_non_pdf_via_legacy_endpoint():
    """Legacy /upload endpoint must still reject non-PDF files."""
    files = {"file": ("test.txt", io.BytesIO(b"plain text content"), "text/plain")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 400
    assert "Only PDF" in res.json()["detail"]


def test_upload_validation_non_pdf_via_documents_endpoint():
    """New /documents/upload endpoint must also reject non-PDF files."""
    files = {"file": ("test.docx", io.BytesIO(b"not a pdf"), "application/vnd.openxmlformats")}
    res = client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 400


def test_global_stats_endpoint():
    """Top-level /stats route should return the same stats shape as /documents/stats."""
    res = client.get("/api/v1/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_documents" in data
    assert "total_chunks" in data
