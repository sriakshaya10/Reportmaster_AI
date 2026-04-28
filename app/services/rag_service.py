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

    def ingest_document(self, file_path: Path) -> int:
        self.store.clear()
        chunks = self.processor.extract_chunks(file_path)
        return self.store.add_records(chunks, self.llm.embed_texts)

    def answer_question(self, question: str, top_k: int | None = None) -> dict:
        k = top_k or self.settings.top_k
        contexts = self.store.search(question, k, self.llm.embed_texts)
        answer, model_used = self.llm.generate_answer(question, contexts)

        return {
            "answer": answer,
            "grounded": len(contexts) > 0,
            "model_used": model_used,
            "sources": contexts,
        }
