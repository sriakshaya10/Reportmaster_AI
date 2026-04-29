import json
import uuid
from pathlib import Path
from typing import Callable

import numpy as np


class VectorStore:
    def __init__(self, index_dir: Path) -> None:
        self.index_dir = index_dir
        self.documents_dir = index_dir / "documents"
        self.docs_meta_path = index_dir / "documents.json"
        
        # Global index that combines all documents
        self.records: list[dict] = []
        self.embeddings: np.ndarray | None = None
        self.document_metadata: dict = {}  # Maps document_id to metadata
        
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self) -> None:
        """Load all documents and their indexes into memory."""
        self.records = []
        self.embeddings = None
        self.document_metadata = {}
        
        # Load document metadata
        if self.docs_meta_path.exists():
            self.document_metadata = json.loads(self.docs_meta_path.read_text(encoding="utf-8"))
        
        # Load all documents' indexes
        if self.documents_dir.exists():
            for doc_dir in sorted(self.documents_dir.iterdir()):
                if doc_dir.is_dir():
                    doc_id = doc_dir.name
                    meta_path = doc_dir / "chunks.json"
                    vec_path = doc_dir / "embeddings.npy"
                    
                    if meta_path.exists() and vec_path.exists():
                        records = json.loads(meta_path.read_text(encoding="utf-8"))
                        vectors = np.load(vec_path)
                        
                        # Combine into global index
                        self.records.extend(records)
                        if self.embeddings is None:
                            self.embeddings = vectors
                        else:
                            self.embeddings = np.vstack([self.embeddings, vectors])

    def save_metadata(self) -> None:
        """Save document metadata."""
        self.docs_meta_path.write_text(
            json.dumps(self.document_metadata, ensure_ascii=True, indent=2),
            encoding="utf-8"
        )

    def add_document(self, document_id: str | None, chunks: list[dict], 
                    embedder: Callable[[list[str]], np.ndarray], 
                    filename: str) -> tuple[str, int]:
        """Add a new document with its chunks. Returns (document_id, chunk_count)."""
        if not chunks:
            return ("", 0)
        
        # Generate document ID if not provided
        if not document_id:
            document_id = str(uuid.uuid4())[:8]
        
        # Create document directory
        doc_dir = self.documents_dir / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate embeddings
        vectors = embedder([c["text"] for c in chunks])
        vectors = self._normalize(vectors)
        
        # Add document_id to each chunk for tracking
        for chunk in chunks:
            chunk["document_id"] = document_id
        
        # Save document-specific index
        meta_path = doc_dir / "chunks.json"
        vec_path = doc_dir / "embeddings.npy"
        
        meta_path.write_text(json.dumps(chunks, ensure_ascii=True, indent=2), encoding="utf-8")
        np.save(vec_path, vectors)
        
        # Update document metadata
        import time
        self.document_metadata[document_id] = {
            "id": document_id,
            "filename": filename,
            "chunks_count": len(chunks),
            "uploaded_at": time.time(),
        }
        self.save_metadata()
        
        # Add to global index
        self.records.extend(chunks)
        if self.embeddings is None:
            self.embeddings = vectors
        else:
            self.embeddings = np.vstack([self.embeddings, vectors])
        
        return (document_id, len(chunks))

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its index. Returns True if successful."""
        doc_dir = self.documents_dir / document_id
        
        if not doc_dir.exists():
            return False
        
        # Remove directory
        import shutil
        shutil.rmtree(doc_dir)
        
        # Remove metadata
        if document_id in self.document_metadata:
            del self.document_metadata[document_id]
            self.save_metadata()
        
        # Reload to rebuild global index without this document
        self.load()
        
        return True

    def get_documents(self) -> list[dict]:
        """Get list of all documents."""
        return list(self.document_metadata.values())

    def search(self, question: str, top_k: int, 
               embedder: Callable[[list[str]], np.ndarray],
               document_id: str | None = None) -> list[dict]:
        """Search across all documents or a specific document if document_id is provided."""
        if self.embeddings is None or not self.records:
            return []

        q_vec = embedder([question])
        q_vec = self._normalize(q_vec)[0]

        scores = self.embeddings @ q_vec
        indices = np.argsort(scores)[::-1][:top_k]

        results: list[dict] = []
        for idx in indices:
            rec = dict(self.records[int(idx)])
            rec["score"] = float(scores[int(idx)])
            
            # Filter by document_id if specified
            if document_id is None or rec.get("document_id") == document_id:
                results.append(rec)
                if len(results) >= top_k:
                    break
        
        return results

    @staticmethod
    def _normalize(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-12
        return matrix / norms
