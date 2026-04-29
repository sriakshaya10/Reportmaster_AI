from pathlib import Path

from app.core.config import Settings
from app.services.document_processor import DocumentProcessor
from app.services.llm_client import LLMClient
from app.services.vector_store import VectorStore


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.processor = DocumentProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.llm = LLMClient(settings)
        self.store = VectorStore(settings.index_dir)

    def ingest_document(self, file_path: Path, document_id: str | None = None) -> tuple[str, int]:
        """Add a new document to the index. Returns (document_id, chunks_count)."""
        chunks = self.processor.extract_chunks(file_path)
        return self.store.add_document(
            document_id=document_id,
            chunks=chunks,
            embedder=self.llm.embed_texts,
            filename=file_path.name
        )

    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the index."""
        return self.store.delete_document(document_id)

    def list_documents(self) -> list[dict]:
        """Get list of all indexed documents."""
        return self.store.get_documents()

    def answer_question(self, question: str, top_k: int | None = None, 
                       document_id: str | None = None) -> dict:
        """Answer a question, optionally scoped to a specific document."""
        k = top_k or self.settings.top_k
        contexts = self.store.search(question, k, self.llm.embed_texts, document_id=document_id)
        answer, model_used = self.llm.generate_answer(question, contexts)

        return {
            "answer": answer,
            "grounded": len(contexts) > 0,
            "model_used": model_used,
            "sources": contexts,
        }
