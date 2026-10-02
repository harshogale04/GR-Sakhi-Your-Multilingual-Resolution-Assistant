# MAHA-GR API Reference

**Multilingual AI-Powered RAG System for Maharashtra Government Resolutions**  
*Base URL*: `http://localhost:8000/api/v1` (Local) / `${BACKEND_URL}/api/v1` (Cloud)  
*Interactive Documentation*: `/docs` (Swagger UI) · `/redoc` (ReDoc)

---

## 1. Overview & Conventions

All endpoints return JSON responses unless otherwise noted (such as the binary PDF download endpoint).

### Headers
| Header | Value | Description |
|---|---|---|
| `Content-Type` | `application/json` | Standard for JSON payloads |
| `Content-Type` | `multipart/form-data` | Required for PDF uploads (`/documents/upload`) |
| `Accept` | `application/json` | Preferred client response format |

### Standard Status Codes
- `200 OK`: Request succeeded.
- `202 Accepted`: File upload accepted for asynchronous background processing.
- `400 Bad Request`: Invalid file format (non-PDF) or malformed payload.
- `404 Not Found`: Document or chunk not found.
- `422 Unprocessable Entity`: Request body failed Pydantic validation.
- `500 Internal Server Error`: Server-side unhandled exception.

---

## 2. Health & System Status

### `GET /health`
Checks the operational status of the service and external dependencies.

#### Response `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "supabase_connected": false,
  "pinecone_connected": false,
  "gemini_configured": false,
  "is_demo_mode": true
}
```

*Note: In Demo Mode, `supabase_connected` and `pinecone_connected` are false, and `is_demo_mode` is true. The API serves in-memory sample Maharashtra GRs.*

---

## 3. Document Management Endpoints

### `POST /documents/upload`
Uploads a Maharashtra Government Resolution PDF and initiates asynchronous ingestion (text extraction, OCR, chunking, embedding, and Pinecone indexing).

#### Request (Multipart Form-Data)
| Field | Type | Required | Description |
|---|---|---|---|
| `file` | `UploadFile` | Yes | PDF file binary (`.pdf` only) |
| `department` | `string` | No | Maharashtra Govt department (e.g. `Agriculture`) |
| `category` | `string` | No | Category (e.g. `Scheme`, `Policy`, `Recruitment`) |
| `language` | `string` | No | Default language (`mr`, `hi`, `en`) |

#### Sample Request
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@gr_drip_subsidy.pdf" \
  -F "department=Agriculture" \
  -F "category=Scheme"
```

#### Response `202 Accepted`
```json
{
  "id": "c1f7b889-4972-4682-824a-d9962a396e95",
  "filename": "c1f7b88949724682824ad9962a396e95.pdf",
  "original_filename": "gr_drip_subsidy.pdf",
  "status": "PROCESSING",
  "message": "Document uploaded successfully. Processing started in background."
}
```

---

### `GET /documents`
Retrieves a paginated list of uploaded Maharashtra Government Resolutions with optional filtering.

#### Query Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | `integer` | `1` | Page number (1-indexed) |
| `limit` | `integer` | `10` | Items per page (max 100) |
| `department` | `string` | `null` | Filter by department name |
| `language` | `string` | `null` | Filter by document language (`mr`, `hi`, `en`) |
| `status` | `string` | `null` | Filter by status (`PROCESSING`, `COMPLETED`, `FAILED`) |
| `search` | `string` | `null` | Text search across subject, filename, or gr_number |

#### Sample Request
```bash
curl "http://localhost:8000/api/v1/documents?page=1&limit=5&department=Agriculture"
```

#### Response `200 OK`
```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "filename": "sample_agri_gr_2024_drip_subsidy.pdf",
      "original_filename": "AGRI_GR_2024_08_15_Drip_Subsidy.pdf",
      "storage_path": "resolutions/demo_agri_drip_subsidy_2024.pdf",
      "status": "COMPLETED",
      "category": "Scheme",
      "department": "Agriculture",
      "language": "mr",
      "document_type": "Government Resolution",
      "subject": "[नमुना GR] महात्मा ज्योतिराव फुले शेतकरी कर्जमुक्ती योजना व ठिबक सिंचन अनुदान नियमावली २०२४",
      "gr_number": "कृषी-२०२४/प्र.क्र.८८/१२-अ",
      "pages": 3,
      "chunk_count": 4,
      "uploaded_at": "2024-08-15T10:30:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 5,
  "pages": 1
}
```

---

### `GET /documents/stats` (also available as `GET /stats`)
Returns aggregate document and chunk metrics across departments and languages.

#### Response `200 OK`
```json
{
  "total_documents": 3,
  "total_chunks": 8,
  "completed_documents": 3,
  "indexed_documents": 3,
  "processing_documents": 0,
  "failed_documents": 0,
  "departments_count": {
    "Agriculture": 1,
    "School Education": 1,
    "Public Health": 1
  },
  "language_breakdown": {
    "mr": 3
  }
}
```

---

### `GET /documents/{doc_id}`
Retrieves complete metadata for a single document.

#### Response `200 OK`
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "filename": "sample_agri_gr_2024_drip_subsidy.pdf",
  "original_filename": "AGRI_GR_2024_08_15_Drip_Subsidy.pdf",
  "storage_path": "resolutions/demo_agri_drip_subsidy_2024.pdf",
  "status": "COMPLETED",
  "category": "Scheme",
  "department": "Agriculture",
  "language": "mr",
  "document_type": "Government Resolution",
  "subject": "[नमुना GR] महात्मा ज्योतिराव फुले शेतकरी कर्जमुक्ती योजना व ठिबक सिंचन अनुदान नियमावली २०२४",
  "gr_number": "कृषी-२०२४/प्र.क्र.८८/१२-अ",
  "pages": 3,
  "chunk_count": 4,
  "uploaded_at": "2024-08-15T10:30:00Z"
}
```

---

### `GET /documents/{doc_id}/status`
Lightweight status endpoint for frontend polling during background ingestion.

#### Response `200 OK`
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "status": "COMPLETED",
  "pages": 3,
  "chunk_count": 4
}
```

---

### `GET /documents/{doc_id}/chunks`
Lists all relational chunk entries registered for the given document from the Supabase `chunks` table.

#### Response `200 OK`
```json
[
  {
    "id": "a0000001-0000-0000-0000-000000000001",
    "chunk_id": "11111111-1111-4111-8111-111111111111_p1_c1",
    "document_id": "11111111-1111-4111-8111-111111111111",
    "page": 1,
    "section": "शासन निर्णय / Resolution",
    "pinecone_id": "11111111-1111-4111-8111-111111111111_0",
    "created_at": "2024-08-15T10:30:00Z"
  }
]
```

---

### `GET /documents/{doc_id}/download`
Streams the original PDF file from Supabase Storage or demo storage for inline preview or download.

#### Response `200 OK`
- `Content-Type`: `application/pdf`
- `Content-Disposition`: `inline; filename="AGRI_GR_2024_08_15_Drip_Subsidy.pdf"`

---

### `DELETE /documents/{doc_id}`
Deletes the document record and relational chunks from PostgreSQL, cleans up Pinecone vectors, and deletes the PDF from Storage.

#### Response `200 OK`
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "success": true,
  "message": "Document and associated vectors deleted successfully."
}
```

---

## 4. Semantic Search

### `POST /search`
Performs vector similarity search against Pinecone embeddings with optional department filtering.

#### Request Body
```json
{
  "query": "ठिबक सिंचनासाठी किती अनुदान मिळते?",
  "language": "mr",
  "department": "Agriculture",
  "top_k": 5
}
```

#### Response `200 OK`
```json
{
  "query": "ठिबक सिंचनासाठी किती अनुदान मिळते?",
  "total": 1,
  "results": [
    {
      "chunk_id": "11111111-1111-4111-8111-111111111111_p1_c1",
      "document_id": "11111111-1111-4111-8111-111111111111",
      "document_name": "[नमुना GR] महात्मा ज्योतिराव फुले शेतकरी कर्जमुक्ती योजना व ठिबक सिंचन अनुदान नियमावली २०२४",
      "gr_number": "कृषी-२०२४/प्र.क्र.८८/१२-अ",
      "department": "Agriculture",
      "page": 1,
      "section": "शासन निर्णय / Resolution",
      "text": "शासन निर्णय: राज्यातील दुष्काळग्रस्त व अवकाळी पाऊस बाधित तालुक्यांमधील शेतकऱ्यांसाठी ठिबक सिंचन योजनेअंतर्गत विशेष अनुदान मंजूर करण्यात येत आहे. अल्प व अत्यल्प भूधारक शेतकऱ्यांना ८०% अनुदान आणि इतर शेतकऱ्यांना ७०% अनुदान थेट बँक खात्यात (DBT) जमा केले जाईल.",
      "score": 0.8842
    }
  ]
}
```

---

## 5. Grounded Q&A / Ask AI

### `POST /chat/ask` (Canonical) · `POST /chat` (Alias)
Answers user queries grounded in retrieved Maharashtra Government Resolutions with citations and hallucination protection.

#### Request Body
```json
{
  "query": "अल्प भूधारक शेतकऱ्यांना ठिबक सिंचनासाठी किती टक्के अनुदान मिळते?",
  "language": "mr",
  "department": "Agriculture"
}
```

#### Response `200 OK` (Evidence Found)
```json
{
  "answer": "महाराष्ट्र शासनाच्या निर्णयानुसार अल्प व अत्यल्प भूधारक शेतकऱ्यांना ठिबक सिंचन योजनेअंतर्गत ८०% अनुदान थेट बँक खात्यात (DBT) जमा केले जाईल.",
  "content": "महाराष्ट्र शासनाच्या निर्णयानुसार अल्प व अत्यल्प भूधारक शेतकऱ्यांना ठिबक सिंचन योजनेअंतर्गत ८०% अनुदान थेट बँक खात्यात (DBT) जमा केले जाईल.",
  "citations": [
    {
      "document_id": "11111111-1111-4111-8111-111111111111",
      "document_name": "[नमुना GR] महात्मा ज्योतिराव फुले शेतकरी कर्जमुक्ती योजना व ठिबक सिंचन अनुदान नियमावली २०२४",
      "gr_number": "कृषी-२०२४/प्र.क्र.८८/१२-अ",
      "page": 1,
      "section": "शासन निर्णय / Resolution",
      "snippet": "अल्प व अत्यल्प भूधारक शेतकऱ्यांना ८०% अनुदान आणि इतर शेतकऱ्यांना ७०% अनुदान थेट बँक खात्यात (DBT) जमा केले जाईल."
    }
  ],
  "insufficient_evidence": false,
  "language": "mr"
}
```

#### Response `200 OK` (Insufficient Evidence / Unrelated Query)
When the question cannot be answered from the indexed resolutions (e.g. query about Chandrayaan):
```json
{
  "answer": "माफ करा, उपलब्ध शासन निर्णयांमध्ये या प्रश्नाचे उत्तर देण्यासाठी पुरेसा पुरावा उपलब्ध नाही.",
  "content": "माफ करा, उपलब्ध शासन निर्णयांमध्ये या प्रश्नाचे उत्तर देण्यासाठी पुरेसा पुरावा उपलब्ध नाही.",
  "citations": [],
  "insufficient_evidence": true,
  "language": "mr"
}
```

---

## 6. Demo Mode Controls

### `GET /demo/status`
Returns whether Demo Mode is active and how many sample resolutions are currently seeded.

#### Response `200 OK`
```json
{
  "is_demo_mode": true,
  "seeded_documents": 3,
  "message": "Demo mode is active (using in-memory store with sample Maharashtra GRs)."
}
```

### `POST /demo/seed`
Forces re-seeding of the 3 authentic sample Maharashtra GRs.

#### Response `200 OK`
```json
{
  "seeded": 3,
  "already_seeded": false,
  "message": "Successfully seeded 3 sample Maharashtra Government Resolutions."
}
```

### `POST /demo/reset`
Clears in-memory sample documents and vectors.

#### Response `200 OK`
```json
{
  "removed": 3,
  "message": "Demo sample documents reset successfully."
}
```
