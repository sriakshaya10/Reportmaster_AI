from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="User question about reporting rules")
    top_k: int | None = Field(default=None, ge=1, le=10)


class SourceSnippet(BaseModel):
    chunk_id: str
    source_file: str
    page_number: int
    score: float
    text: str


class QueryResponse(BaseModel):
    answer: str
    grounded: bool
    model_used: str
    sources: list[SourceSnippet]


class UploadResponse(BaseModel):
    document_name: str
    chunks_indexed: int
    message: str
