import json
from pathlib import Path
from typing import Callable

import numpy as np


class VectorStore:
    def __init__(self, index_dir: Path) -> None:
        self.index_dir = index_dir
        self.meta_path = self.index_dir / "chunks.json"
        self.vec_path = self.index_dir / "embeddings.npy"

        self.records: list[dict] = []
        self.embeddings: np.ndarray | None = None
        self.load()

    def load(self) -> None:
        if self.meta_path.exists() and self.vec_path.exists():
            self.records = json.loads(self.meta_path.read_text(encoding="utf-8"))
            self.embeddings = np.load(self.vec_path)

    def save(self) -> None:
        self.meta_path.write_text(json.dumps(self.records, ensure_ascii=True, indent=2), encoding="utf-8")
        if self.embeddings is not None:
            np.save(self.vec_path, self.embeddings)

    def clear(self) -> None:
        self.records = []
        self.embeddings = None

        if self.meta_path.exists():
            self.meta_path.unlink()

        if self.vec_path.exists():
            self.vec_path.unlink()

    def add_records(self, chunks: list[dict], embedder: Callable[[list[str]], np.ndarray]) -> int:
        if not chunks:
            return 0

        vectors = embedder([c["text"] for c in chunks])
        vectors = self._normalize(vectors)

        if self.embeddings is None:
            self.embeddings = vectors
        else:
            self.embeddings = np.vstack([self.embeddings, vectors])

        self.records.extend(chunks)
        self.save()
        return len(chunks)

    def search(self, question: str, top_k: int, embedder: Callable[[list[str]], np.ndarray]) -> list[dict]:
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
            results.append(rec)

        return results

    @staticmethod
    def _normalize(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-12
        return matrix / norms
