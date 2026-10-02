"""
RAG Service for MAHA-GR (महाराष्ट्र शासन निर्णय AI).
Orchestrates:
1. End-to-end background document processing:
   - PDF extraction (digital + Tesseract Devanagari OCR fallback + Gemini multimodal).
   - Quality checks to avoid silently accepting empty or failed extractions.
   - Metadata enrichment (non-destructive; preserves user-supplied fields).
   - Section-aware, page-preserving chunking with stable IDs.
   - Batch embeddings with gemini-embedding-001.
   - Pinecone upsert with strict metadata schema.
   - Relational chunk registry in Supabase.
   - Document status update to COMPLETED or FAILED.
2. Multilingual Semantic Search across Devanagari (Marathi, Hindi) and English.
3. Grounded Conversational Q&A with strict evidence validation, citation construction,
   and insufficient-evidence handling.
"""
import uuid
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.documents import DocumentCreate, DocumentUpdate
from backend.app.schemas.chunks import ChunkCreate
from backend.app.schemas.search import SearchResultItem, SearchResponse
from backend.app.schemas.chat import ChatResponse, ChatCitation
from backend.app.services.document_service import DocumentService
from backend.app.services.chunk_service import ChunkService
from backend.app.services.storage_service import StorageService
from backend.app.services.pdf_extractor import PDFExtractor
from backend.app.services.metadata_extractor import MetadataExtractor
from backend.app.services.chunking_service import ChunkingService, DocumentChunk
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.vector_store_service import VectorStoreService, _mock_pinecone_store
from backend.app.services.gemini_service import GeminiService

# Legacy mock vector store alias for backwards compatibility with tests
_mock_vector_store = []


class RAGService:
    SIMILARITY_THRESHOLD = 0.35  # Threshold below which evidence is deemed insufficient

    @staticmethod
    def process_document_background(
        doc_id: UUID,
        file_bytes: bytes,
        original_filename: str,
        subject: Optional[str] = None,
        gr_number: Optional[str] = None,
        department: Optional[str] = None,
        language: Optional[str] = "mr",
        category: Optional[str] = "Policy",
        document_type: Optional[str] = "Government Resolution",
    ):
        """
        Asynchronous background pipeline for resolution processing.
        Handles extraction, quality check, metadata enrichment, chunking,
        vector embedding, Pinecone upsert, and relational chunk registration.
        """
        logger.info(f"Starting background processing for document {doc_id} ({original_filename})...")
        try:
            # 1. Extract text with multi-tier fallback (Digital -> Tesseract OCR -> Gemini Multimodal)
            extraction = PDFExtractor.extract(file_bytes)
            total_pages = extraction.total_pages or 1

            if extraction.warnings:
                for w in extraction.warnings:
                    logger.warning(f"Doc {doc_id} extraction warning: {w}")

            # Quality Check: If no text could be extracted at all, fail early
            if not extraction.has_text:
                logger.error(f"Extraction failed for doc {doc_id}: No readable text found.")
                DocumentService.update_document(
                    doc_id,
                    DocumentUpdate(status="FAILED"),
                )
                return

            full_text = extraction.full_text

            # 2. Extract and enrich metadata without overwriting user-supplied fields
            user_meta = {
                "department": department,
                "gr_number": gr_number,
                "subject": subject,
                "category": category,
                "document_type": document_type,
                "language": language,
                "original_filename": original_filename,
            }
            enriched = MetadataExtractor.enrich_document_metadata(
                document_text=full_text,
                user_supplied=user_meta,
                page_count=total_pages,
            )

            # 3. Section-aware, page-preserving chunking
            doc_chunks: List[DocumentChunk] = ChunkingService.chunk_pages(
                document_id=doc_id,
                pages=extraction.pages,
                document_metadata={
                    "filename": original_filename,
                    "original_filename": original_filename,
                    "gr_number": enriched.get("gr_number"),
                    "department": enriched.get("department"),
                    "subject": enriched.get("subject"),
                },
                language=enriched.get("language") or "mr",
            )

            if not doc_chunks:
                logger.warning(f"No chunks generated for doc {doc_id}, creating fallback chunk.")
                doc_chunks = [
                    DocumentChunk(
                        chunk_id=f"{doc_id}_p1_c1",
                        document_id=doc_id,
                        text=full_text[:800] if full_text else original_filename,
                        page=1,
                        section="General",
                        language=enriched.get("language") or "mr",
                        metadata={
                            "filename": original_filename,
                            "original_filename": original_filename,
                            "gr_number": enriched.get("gr_number") or "",
                            "department": enriched.get("department") or "",
                            "subject": enriched.get("subject") or "",
                        },
                    )
                ]

            # 4. Generate Gemini Embeddings in batches
            chunk_texts = [c.text for c in doc_chunks]
            embeddings = EmbeddingService.get_batch_document_embeddings(chunk_texts, batch_size=10)

            # 5. Prepare vectors and metadata for Pinecone upsert
            pinecone_vectors = []
            relational_chunks: List[ChunkCreate] = []

            for chk, emb in zip(doc_chunks, embeddings):
                pinecone_vector_id = f"vec_{chk.chunk_id}"

                vector_item = {
                    "id": pinecone_vector_id,
                    "values": emb,
                    "metadata": {
                        "document_id": str(doc_id),
                        "chunk_id": chk.chunk_id,
                        "text": chk.text,
                        "page": chk.page,
                        "section": chk.section,
                        "language": chk.language,
                        "filename": original_filename,
                        "gr_number": enriched.get("gr_number") or "",
                        "department": enriched.get("department") or "",
                    },
                }
                pinecone_vectors.append(vector_item)

                # Keep legacy module-level list updated for any backward-compat references
                _mock_vector_store.append(vector_item)

                # Relational chunk (matches Supabase 'chunks' table strictly)
                relational_chunks.append(
                    ChunkCreate(
                        chunk_id=chk.chunk_id,
                        document_id=doc_id,
                        page=chk.page,
                        section=chk.section,
                        pinecone_id=pinecone_vector_id,
                    )
                )

            # 6. Upsert into Pinecone Vector Store
            VectorStoreService.upsert_chunks(pinecone_vectors)

            # 7. Register relational chunks in Supabase
            ChunkService.create_chunks_batch(relational_chunks)

            # 8. Update Document record to COMPLETED with enriched metadata
            DocumentService.update_document(
                doc_id,
                DocumentUpdate(
                    status="COMPLETED",
                    pages=total_pages,
                    chunk_count=len(doc_chunks),
                    department=enriched.get("department"),
                    gr_number=enriched.get("gr_number"),
                    subject=enriched.get("subject"),
                    category=enriched.get("category"),
                    language=enriched.get("language"),
                ),
            )
            logger.info(f"Document {doc_id} successfully indexed with {len(doc_chunks)} chunks.")

        except Exception as e:
            logger.error(f"Failed processing document {doc_id}: {e}", exc_info=True)
            DocumentService.update_document(doc_id, DocumentUpdate(status="FAILED"))

    @staticmethod
    def process_and_index_pdf(
        file_bytes: bytes,
        original_filename: str,
        department: Optional[str] = None,
        gr_number: Optional[str] = None,
        subject: Optional[str] = None,
        category: Optional[str] = "Policy",
        language: Optional[str] = "mr",
        document_type: Optional[str] = "Government Resolution",
    ):
        """Synchronous wrapper for legacy callers."""
        storage_path = StorageService.generate_safe_storage_path(original_filename)
        StorageService.upload_file(file_bytes, storage_path)

        doc_in = DocumentCreate(
            filename=storage_path.split("/")[-1],
            original_filename=original_filename,
            storage_path=storage_path,
            status="PROCESSING",
            category=category,
            department=department,
            language=language or "mr",
            document_type=document_type,
            subject=subject or original_filename,
            gr_number=gr_number,
        )
        created_doc = DocumentService.create_document(doc_in)
        RAGService.process_document_background(
            doc_id=created_doc.id,
            file_bytes=file_bytes,
            original_filename=original_filename,
            subject=subject,
            gr_number=gr_number,
            department=department,
            language=language,
            category=category,
            document_type=document_type,
        )
        return DocumentService.get_document_by_id(created_doc.id) or created_doc

    @staticmethod
    def search_semantic(
        query: str,
        language: Optional[str] = None,
        department: Optional[str] = None,
        top_k: int = 10,
    ) -> SearchResponse:
        """
        Multilingual semantic retrieval in Pinecone vector index.
        Finds the most relevant chunk passages and hydrates document metadata.
        """
        detected_lang = language or MetadataExtractor.detect_language(query)
        query_vector = EmbeddingService.get_query_embedding(query)

        raw_matches = VectorStoreService.query_similar(
            query_vector=query_vector,
            top_k=top_k,
            department=department,
        )

        results: List[SearchResultItem] = []
        for match in raw_matches:
            meta = match.get("metadata", {})
            doc_id_str = meta.get("document_id")

            doc_response = None
            doc_uuid = uuid.uuid4()
            if doc_id_str:
                try:
                    doc_uuid = UUID(doc_id_str)
                    doc_response = DocumentService.get_document_by_id(doc_uuid)
                except Exception:
                    pass

            results.append(
                SearchResultItem(
                    chunk_id=meta.get("chunk_id", match.get("id")),
                    pinecone_id=match.get("id"),
                    document_id=doc_uuid,
                    score=float(match.get("score", 0.0)),
                    text=meta.get("text", ""),
                    page=meta.get("page"),
                    section=meta.get("section"),
                    document=doc_response,
                )
            )

        return SearchResponse(
            results=results,
            total=len(results),
            query=query,
            language=detected_lang,
        )

    @classmethod
    def answer_query(
        cls,
        query: str,
        language: Optional[str] = None,
        history: Optional[List[dict]] = None,
        department: Optional[str] = None,
        top_k: int = 5,
    ) -> ChatResponse:
        """
        Complete Grounded Conversational RAG with:
        - Language detection / selection
        - Pinecone semantic retrieval
        - Evidence sufficiency verification
        - Grounded Gemini Flash prompt engineering
        - Programmatically constructed source citations (verifiable provenance)
        """
        target_lang = language or MetadataExtractor.detect_language(query)

        search_res = cls.search_semantic(
            query=query,
            language=target_lang,
            department=department,
            top_k=top_k,
        )

        # Retrieval sufficiency check
        has_matches = len(search_res.results) > 0
        top_score = search_res.results[0].score if has_matches else 0.0
        insufficient_evidence = (not has_matches) or (top_score < cls.SIMILARITY_THRESHOLD)

        context_passages: List[Dict[str, Any]] = []
        citations: List[ChatCitation] = []

        if not insufficient_evidence:
            for item in search_res.results:
                doc_title = (
                    item.document.subject
                    if item.document and item.document.subject
                    else (item.document.original_filename if item.document else "Maharashtra GR")
                )
                gr_num = item.document.gr_number if item.document else None
                dept = item.document.department if item.document else None

                context_passages.append({
                    "document_title": doc_title,
                    "gr_number": gr_num,
                    "department": dept,
                    "page": item.page,
                    "section": item.section,
                    "text": item.text,
                })

                citations.append(
                    ChatCitation(
                        document_id=item.document_id,
                        document_title=doc_title,
                        gr_number=gr_num,
                        department=dept,
                        page=item.page,
                        section=item.section,
                        snippet=item.text[:280] + ("..." if len(item.text) > 280 else ""),
                        score=item.score,
                    )
                )

        generated_answer = GeminiService.generate_grounded_answer(
            query=query,
            context_passages=context_passages,
            language=target_lang,
            insufficient_evidence=insufficient_evidence,
            conversation_history=history,
        )

        return ChatResponse(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            role="assistant",
            answer=generated_answer,
            content=generated_answer,
            language=target_lang,
            insufficient_evidence=insufficient_evidence,
            citations=citations,
            timestamp=datetime.now(timezone.utc),
        )
