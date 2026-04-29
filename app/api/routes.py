from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.models.schemas import (
    DocumentListResponse,
    DocumentMetadata,
    QueryRequest,
    QueryResponse,
    SourceSnippet,
    UploadResponse,
)
from app.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService(settings)


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "app": settings.app_name}


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file name is required.")

    allowed = (".pdf",)
    lower = file.filename.lower()
    if not any(lower.endswith(ext) for ext in allowed):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

    # Store in upload directory (no deletion of previous files)
    destination = settings.upload_dir / file.filename
    data = await file.read()
    destination.write_bytes(data)

    try:
        document_id, chunks_count = rag_service.ingest_document(Path(destination))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to index document: {exc}") from exc

    return UploadResponse(
        document_id=document_id,
        document_name=file.filename,
        chunks_indexed=chunks_count,
        message="Document uploaded and indexed successfully.",
    )


@router.get("/documents", response_model=DocumentListResponse)
def list_documents() -> DocumentListResponse:
    """Get list of all uploaded documents."""
    docs = rag_service.list_documents()
    total_chunks = sum(doc["chunks_count"] for doc in docs)
    return DocumentListResponse(
        documents=[DocumentMetadata(**doc) for doc in docs],
        total_documents=len(docs),
        total_chunks=total_chunks,
    )


@router.delete("/documents/{document_id}")
def delete_document(document_id: str) -> dict:
    """Delete a document from the index."""
    success = rag_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")
    return {"message": f"Document {document_id} deleted successfully."}


@router.post("/query", response_model=QueryResponse)
def ask_question(payload: QueryRequest) -> QueryResponse:
    result = rag_service.answer_question(
        payload.question,
        payload.top_k,
        document_id=payload.document_id
    )
    sources = [SourceSnippet(**item) for item in result["sources"]]
    return QueryResponse(
        answer=result["answer"],
        grounded=result["grounded"],
        model_used=result["model_used"],
        sources=sources,
    )
