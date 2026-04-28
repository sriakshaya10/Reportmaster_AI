from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.models.schemas import QueryRequest, QueryResponse, SourceSnippet, UploadResponse
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

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    for existing_file in settings.upload_dir.iterdir():
        if existing_file.is_file():
            existing_file.unlink()

    destination = settings.upload_dir / file.filename
    data = await file.read()
    destination.write_bytes(data)

    try:
        chunks_count = rag_service.ingest_document(Path(destination))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to index document: {exc}") from exc

    return UploadResponse(
        document_name=file.filename,
        chunks_indexed=chunks_count,
        message="Document uploaded and indexed successfully.",
    )


@router.post("/query", response_model=QueryResponse)
def ask_question(payload: QueryRequest) -> QueryResponse:
    result = rag_service.answer_question(payload.question, payload.top_k)
    sources = [SourceSnippet(**item) for item in result["sources"]]
    return QueryResponse(
        answer=result["answer"],
        grounded=result["grounded"],
        model_used=result["model_used"],
        sources=sources,
    )
