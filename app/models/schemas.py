from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="User question about reporting rules")
    top_k: int | None = Field(default=None, ge=1, le=10)
    document_id: str | None = Field(default=None, description="Optional: Search in specific document")


class SourceSnippet(BaseModel):
    chunk_id: str
    source_file: str
    page_number: int
    score: float
    text: str
    document_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    grounded: bool
    model_used: str
    sources: list[SourceSnippet]


class UploadResponse(BaseModel):
    document_id: str
    document_name: str
    chunks_indexed: int
    message: str


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    chunks_count: int
    uploaded_at: float


class DocumentListResponse(BaseModel):
    documents: list[DocumentMetadata]
    total_documents: int
    total_chunks: int
