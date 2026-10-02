# MAHA-GR Database & Vector Store Specification

**Dual-Store Architecture: Supabase PostgreSQL & Pinecone Vector DB**  
*Hackathon Track: AI for Bharat in Indian Languages*

---

## 1. Architectural Strategy: The Dual-Store Model

MAHA-GR implements a decoupled **Dual-Store Architecture**:
1. **Relational Database (Supabase PostgreSQL)**: Manages transactional records, document lifecycle status (`PROCESSING`, `COMPLETED`, `FAILED`), department classifications, page counts, and relational chunk foreign keys.
2. **Object Storage (Supabase Storage)**: Stores original, unmodified Government Resolution PDF files for citation preview and download.
3. **Vector Database (Pinecone)**: Stores 768-dimensional dense embeddings (`gemini-embedding-001`) and the raw passage text inside vector metadata.

> [!IMPORTANT]
> **Strict Schema Adherence**: The existing Supabase tables (`documents` and `chunks`) are used exactly as provided. No tables or columns have been added, renamed, or modified. Crucially, because the `chunks` table **does not have a `text` column**, the raw text of each chunk is stored safely inside **Pinecone metadata**.

---

## 2. Supabase PostgreSQL Schema

The system connects to your pre-existing Supabase project using the following exact tables:

### 2.1. `documents` Table
Stores high-level metadata for each uploaded Maharashtra Government Resolution.

```sql
create table documents (
    id uuid primary key default gen_random_uuid(),
    filename text not null,
    original_filename text not null,
    storage_path text not null,
    status text not null default 'PROCESSING',
    category text,
    department text,
    language text,
    document_type text,
    subject text,
    gr_number text,
    pages integer,
    chunk_count integer,
    uploaded_at timestamptz not null default now()
);
```

#### Column Descriptions
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `uuid` | Primary Key | Unique document UUID |
| `filename` | `text` | NOT NULL | Sanitized unique storage filename (e.g. `{uuid}.pdf`) |
| `original_filename` | `text` | NOT NULL | Original user-uploaded filename (e.g. `GR_Drip_2024.pdf`) |
| `storage_path` | `text` | NOT NULL | Relative path within the Supabase Storage bucket |
| `status` | `text` | NOT NULL | Lifecycle state: `'PROCESSING'`, `'COMPLETED'`, `'FAILED'` |
| `category` | `text` | Nullable | Policy category (e.g., `Scheme`, `Policy`, `Recruitment`) |
| `department` | `text` | Nullable | Ministry / Department (e.g., `Agriculture`, `Public Health`) |
| `language` | `text` | Nullable | Primary language code (`mr`, `hi`, `en`) |
| `document_type` | `text` | Nullable | Classification (default: `Government Resolution`) |
| `subject` | `text` | Nullable | Official GR subject / title in Marathi or English |
| `gr_number` | `text` | Nullable | Official GR reference number (e.g., `कृषी-२०२४/प्र.क्र.८८/१२-अ`) |
| `pages` | `integer` | Nullable | Total page count |
| `chunk_count` | `integer` | Nullable | Number of text chunks indexed in Pinecone |
| `uploaded_at` | `timestamptz` | NOT NULL | Upload timestamp with timezone |

#### Allowed Status Values
- **`PROCESSING`**: Document uploaded and accepted; background OCR, chunking, and vector indexing are currently running.
- **`COMPLETED`**: Processing succeeded; all chunks are indexed in Pinecone and registered in Supabase.
- **`FAILED`**: Extraction or embedding encountered an unrecoverable error.
- *(Note: `INDEXED` is also supported for backward-compatibility).*

---

### 2.2. `chunks` Table
Acts as a relational registry linking every indexed vector to its parent document and page.

```sql
create table chunks (
    id uuid primary key default gen_random_uuid(),
    chunk_id text not null,
    document_id uuid not null,
    page integer,
    section text,
    pinecone_id text not null,
    created_at timestamptz not null default now(),
    constraint chunks_document_id_fkey
        foreign key (document_id)
        references documents(id)
        on delete cascade
);
```

#### Column Descriptions
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `uuid` | Primary Key | Chunk registry UUID |
| `chunk_id` | `text` | NOT NULL | Human-readable chunk code (`{document_id}_p{page}_c{index}`) |
| `document_id` | `uuid` | Foreign Key | References `documents(id)` with `ON DELETE CASCADE` |
| `page` | `integer` | Nullable | Source page number in the original PDF (1-indexed) |
| `section` | `text` | Nullable | Section heading (*शासन निर्णय*, *पात्रता*, *अटी व शर्ती*) |
| `pinecone_id` | `text` | NOT NULL | Matching vector ID in Pinecone |
| `created_at` | `timestamptz` | NOT NULL | Indexing timestamp |

---

## 3. Supabase Storage Configuration

- **Bucket Name**: `government-resolutions` (customizable via `SUPABASE_STORAGE_BUCKET`).
- **File Hierarchy**: `resolutions/{uuid}.pdf`
- **File Format**: Standard PDF binary (`application/pdf`).
- **Key Handling**: Use the Supabase **Service Role Key** (`SUPABASE_KEY`) on the backend. This allows the backend background ingestion task to write to storage and database tables securely without client-side RLS blocking.

```
Supabase Storage Bucket ('government-resolutions')
└── resolutions/
    ├── 11111111-1111-4111-8111-111111111111.pdf
    ├── 22222222-2222-4222-8222-222222222222.pdf
    └── 33333333-3333-4333-8333-333333333333.pdf
```

---

## 4. Pinecone Vector Database Configuration

### 4.1. Index Specifications
| Parameter | Value | Rationale |
|---|---|---|
| **Index Name** | `maha-gr-index` | Configurable via `PINECONE_INDEX_NAME` |
| **Dimension** | `768` | Required by Google `models/gemini-embedding-001` |
| **Metric** | `cosine` | Normalized angular distance for semantic text matching |
| **Cloud Provider** | AWS / GCP | Standard serverless or pod deployment |

### 4.2. Vector Structure
- **Vector ID**: `{document_id}_{chunk_index}`  
  Example: `11111111-1111-4111-8111-111111111111_0`
- **Values**: Array of 768 floating-point numbers (`List[float]`).
- **Metadata Payload**:
  ```json
  {
    "id": "11111111-1111-4111-8111-111111111111_0",
    "document_id": "11111111-1111-4111-8111-111111111111",
    "page": 1,
    "section": "शासन निर्णय / Resolution",
    "department": "Agriculture",
    "language": "mr",
    "gr_number": "कृषी-२०२४/प्र.क्र.८८/१२-अ",
    "text": "शासन निर्णय: राज्यातील दुष्काळग्रस्त व अवकाळी पाऊस बाधित तालुक्यांमधील शेतकऱ्यांसाठी ठिबक सिंचन योजनेअंतर्गत विशेष अनुदान मंजूर करण्यात येत आहे..."
  }
  ```

---

## 5. Vector Cleanup & Re-indexing Considerations

When a document is deleted (`DELETE /api/v1/documents/{doc_id}`):
1. **Explicit ID Querying**: `DocumentService` reads all `pinecone_id` entries for that document from the Supabase `chunks` table.
2. **Targeted Deletion**: `VectorStoreService.delete_by_document_id(doc_id, vector_ids=vector_ids)` deletes the vectors directly by their IDs (`index.delete(ids=vector_ids)`).
3. **Filter Fallback**: If vector IDs are unavailable, it attempts filter-based deletion (`index.delete(filter={"document_id": doc_id})`).
4. **Relational Cascade**: Foreign-key `ON DELETE CASCADE` automatically removes the corresponding chunk rows in Supabase.
5. **Storage Cleanup**: The original PDF is removed from the Supabase Storage bucket.

This two-tier deletion strategy prevents orphaned vectors in Pinecone and avoids limitations present in certain Pinecone free-tier plans where metadata filter deletion is unsupported.
