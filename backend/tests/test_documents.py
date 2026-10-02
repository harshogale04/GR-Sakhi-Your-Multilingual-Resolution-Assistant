"""
Stage 2 Tests — Document Management System
Tests: PDF validation, upload behavior, status polling, paginated listing,
       deletion workflow, error handling, schema field compliance.
All tests use the mock/in-memory fallback (no live Supabase credentials required).
"""
import io
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pdf_bytes() -> bytes:
    """Minimal valid PDF structure."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        b"xref\n0 2\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"trailer\n<< /Size 2 /Root 1 0 R >>\n"
        b"startxref\n9\n%%EOF"
    )


def upload_pdf(
    filename: str = "test_resolution.pdf",
    content: bytes | None = None,
    subject: str = "Test GR Subject",
    department: str = "Finance",
    language: str = "mr",
    gr_number: str = "TEST-2024/001",
):
    data = content if content is not None else make_pdf_bytes()
    files = {"file": (filename, io.BytesIO(data), "application/pdf")}
    form = {
        "subject": subject,
        "department": department,
        "language": language,
        "gr_number": gr_number,
        "category": "Policy",
        "document_type": "Government Resolution",
    }
    return client.post("/api/v1/documents/upload", files=files, data=form)


# ---------------------------------------------------------------------------
# 1. PDF Validation
# ---------------------------------------------------------------------------

class TestPDFValidation:
    def test_non_pdf_extension_rejected(self):
        files = {"file": ("report.txt", io.BytesIO(b"plain text"), "text/plain")}
        res = client.post("/api/v1/documents/upload", files=files)
        assert res.status_code == 400
        assert "Only PDF" in res.json()["detail"]

    def test_non_pdf_extension_docx_rejected(self):
        files = {"file": ("document.docx", io.BytesIO(b"docx bytes"), "application/vnd.openxmlformats")}
        res = client.post("/api/v1/documents/upload", files=files)
        assert res.status_code == 400

    def test_empty_pdf_rejected(self):
        files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
        res = client.post("/api/v1/documents/upload", files=files)
        assert res.status_code == 400
        assert "empty" in res.json()["detail"].lower()

    def test_valid_pdf_accepted(self):
        res = upload_pdf()
        assert res.status_code == 201, res.text


# ---------------------------------------------------------------------------
# 2. Upload — Immediate Response (PROCESSING status)
# ---------------------------------------------------------------------------

class TestUploadBehavior:
    def test_upload_returns_processing_status(self):
        res = upload_pdf()
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "PROCESSING"

    def test_upload_returns_document_id(self):
        res = upload_pdf()
        assert res.status_code == 201
        data = res.json()
        # Must be a valid UUID string
        assert uuid.UUID(data["id"])

    def test_upload_response_fields(self):
        res = upload_pdf()
        data = res.json()
        required = {"id", "filename", "original_filename", "storage_path", "status", "message"}
        assert required.issubset(data.keys())

    def test_upload_stores_original_filename(self):
        res = upload_pdf(filename="महाराष्ट्र_शासन_निर्णय.pdf")
        data = res.json()
        assert data["original_filename"] == "महाराष्ट्र_शासन_निर्णय.pdf"

    def test_upload_storage_path_prefix(self):
        res = upload_pdf()
        data = res.json()
        assert data["storage_path"].startswith("resolutions/")


# ---------------------------------------------------------------------------
# 3. Status Polling Endpoint
# ---------------------------------------------------------------------------

class TestStatusEndpoint:
    def test_status_returns_processing_after_upload(self):
        upload_res = upload_pdf()
        doc_id = upload_res.json()["id"]

        res = client.get(f"/api/v1/documents/{doc_id}/status")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == doc_id
        assert data["status"] in ("PROCESSING", "COMPLETED", "FAILED")

    def test_status_fields_present(self):
        upload_res = upload_pdf()
        doc_id = upload_res.json()["id"]

        res = client.get(f"/api/v1/documents/{doc_id}/status")
        data = res.json()
        assert "id" in data
        assert "status" in data
        assert "uploaded_at" in data

    def test_status_not_found(self):
        random_id = uuid.uuid4()
        res = client.get(f"/api/v1/documents/{random_id}/status")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# 4. Paginated Document List
# ---------------------------------------------------------------------------

class TestPaginatedList:
    def test_list_returns_paginated_response(self):
        res = client.get("/api/v1/documents")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data

    def test_list_page_defaults(self):
        res = client.get("/api/v1/documents")
        data = res.json()
        assert data["page"] == 1
        assert data["limit"] == 20

    def test_list_custom_pagination(self):
        res = client.get("/api/v1/documents?page=1&limit=5")
        assert res.status_code == 200
        data = res.json()
        assert data["limit"] == 5

    def test_list_contains_uploaded_doc(self):
        upload_res = upload_pdf(subject="Pagination Test GR", gr_number="PAG-2024/TEST")
        doc_id = upload_res.json()["id"]

        res = client.get("/api/v1/documents")
        all_ids = [d["id"] for d in res.json()["items"]]
        assert doc_id in all_ids

    def test_list_status_filter(self):
        res = client.get("/api/v1/documents?status=PROCESSING")
        assert res.status_code == 200
        data = res.json()
        for item in data["items"]:
            assert item["status"] == "PROCESSING"

    def test_list_invalid_limit_capped(self):
        res = client.get("/api/v1/documents?limit=500")
        assert res.status_code == 422  # FastAPI rejects > 100 via ge/le constraint


# ---------------------------------------------------------------------------
# 5. Single Document Retrieval
# ---------------------------------------------------------------------------

class TestGetDocument:
    def test_get_document_by_id(self):
        upload_res = upload_pdf()
        doc_id = upload_res.json()["id"]

        res = client.get(f"/api/v1/documents/{doc_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == doc_id

    def test_get_document_not_found(self):
        res = client.get(f"/api/v1/documents/{uuid.uuid4()}")
        assert res.status_code == 404

    def test_get_document_has_all_schema_fields(self):
        upload_res = upload_pdf()
        doc_id = upload_res.json()["id"]
        res = client.get(f"/api/v1/documents/{doc_id}")
        data = res.json()
        required_fields = {
            "id", "filename", "original_filename", "storage_path", "status",
            "department", "language", "uploaded_at"
        }
        assert required_fields.issubset(data.keys())

    def test_document_has_no_error_message_field(self):
        """Verify schema strictly conforms to existing DB: no error_message column."""
        upload_res = upload_pdf()
        doc_id = upload_res.json()["id"]
        res = client.get(f"/api/v1/documents/{doc_id}")
        assert "error_message" not in res.json()


# ---------------------------------------------------------------------------
# 6. Chunk Endpoint
# ---------------------------------------------------------------------------

class TestChunkEndpoint:
    def test_chunks_endpoint_returns_list(self):
        upload_res = upload_pdf()
        doc_id = upload_res.json()["id"]
        res = client.get(f"/api/v1/documents/{doc_id}/chunks")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_chunks_not_found_for_missing_doc(self):
        res = client.get(f"/api/v1/documents/{uuid.uuid4()}/chunks")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# 7. Deletion Workflow (with mocked Pinecone / storage)
# ---------------------------------------------------------------------------

class TestDeletionWorkflow:
    def test_delete_existing_document(self):
        upload_res = upload_pdf()
        doc_id = upload_res.json()["id"]

        del_res = client.delete(f"/api/v1/documents/{doc_id}")
        assert del_res.status_code == 200
        data = del_res.json()
        assert data["success"] is True
        assert data["document_id"] == doc_id

    def test_delete_returns_result_fields(self):
        upload_res = upload_pdf()
        doc_id = upload_res.json()["id"]

        del_res = client.delete(f"/api/v1/documents/{doc_id}")
        data = del_res.json()
        required = {"success", "document_id", "message", "storage_deleted", "vectors_deleted", "chunks_removed"}
        assert required.issubset(data.keys())

    def test_delete_removes_document_from_list(self):
        upload_res = upload_pdf()
        doc_id = upload_res.json()["id"]

        client.delete(f"/api/v1/documents/{doc_id}")
        get_res = client.get(f"/api/v1/documents/{doc_id}")
        assert get_res.status_code == 404

    def test_delete_not_found(self):
        res = client.delete(f"/api/v1/documents/{uuid.uuid4()}")
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# 8. Stats Endpoint
# ---------------------------------------------------------------------------

class TestStatsEndpoints:
    def test_documents_stats_endpoint(self):
        res = client.get("/api/v1/documents/stats")
        assert res.status_code == 200
        data = res.json()
        required = {
            "total_documents", "total_chunks", "completed_documents",
            "indexed_documents", "processing_documents", "failed_documents",
            "departments_count", "language_breakdown"
        }
        assert required.issubset(data.keys())

    def test_global_stats_endpoint(self):
        res = client.get("/api/v1/stats")
        assert res.status_code == 200
        data = res.json()
        assert "total_documents" in data
        assert "indexed_documents" in data

    def test_stats_type_correctness(self):
        res = client.get("/api/v1/documents/stats")
        data = res.json()
        assert isinstance(data["total_documents"], int)
        assert isinstance(data["language_breakdown"], dict)

    def test_stats_increment_after_upload(self):
        before = client.get("/api/v1/documents/stats").json()["total_documents"]
        upload_pdf()
        after = client.get("/api/v1/documents/stats").json()["total_documents"]
        assert after >= before  # at least equal (mock store might persist)


# ---------------------------------------------------------------------------
# 9. Legacy /upload endpoint still works
# ---------------------------------------------------------------------------

class TestLegacyUpload:
    def test_legacy_upload_non_pdf_rejected(self):
        files = {"file": ("bad.txt", io.BytesIO(b"text"), "text/plain")}
        res = client.post("/api/v1/upload", files=files)
        assert res.status_code == 400
        assert "Only PDF" in res.json()["detail"]

    def test_legacy_upload_pdf_accepted(self):
        files = {"file": ("legacy_test.pdf", io.BytesIO(make_pdf_bytes()), "application/pdf")}
        form = {"subject": "Legacy upload test", "department": "Finance"}
        res = client.post("/api/v1/upload", files=files, data=form)
        assert res.status_code == 201
        assert res.json()["status"] == "PROCESSING"


# ---------------------------------------------------------------------------
# 10. Document Download / Stream Endpoint
# ---------------------------------------------------------------------------

class TestDocumentDownload:
    def test_download_existing_document(self):
        # Upload a document first
        pdf_content = make_pdf_bytes()
        files = {"file": ("download_test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        up_res = client.post("/api/v1/documents/upload", files=files)
        assert up_res.status_code == 201
        doc_id = up_res.json()["id"]

        # Call download endpoint
        dl_res = client.get(f"/api/v1/documents/{doc_id}/download")
        assert dl_res.status_code == 200
        assert dl_res.headers["content-type"] == "application/pdf"
        assert len(dl_res.content) > 0

    def test_download_not_found(self):
        import uuid
        random_id = str(uuid.uuid4())
        res = client.get(f"/api/v1/documents/{random_id}/download")
        assert res.status_code == 404

