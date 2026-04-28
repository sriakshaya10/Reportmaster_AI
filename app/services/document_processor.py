from pathlib import Path

from pypdf import PdfReader


class DocumentProcessor:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_chunks(self, file_path: Path) -> list[dict]:
        reader = PdfReader(str(file_path))
        chunks: list[dict] = []

        for page_index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue

            page_chunks = self._chunk_text(text)
            for idx, chunk_text in enumerate(page_chunks):
                chunks.append(
                    {
                        "chunk_id": f"{file_path.stem}_p{page_index}_c{idx}",
                        "source_file": file_path.name,
                        "page_number": page_index,
                        "text": chunk_text,
                    }
                )

        return chunks

    def _chunk_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        out: list[str] = []
        start = 0
        stride = max(1, self.chunk_size - self.chunk_overlap)

        while start < len(text):
            end = min(len(text), start + self.chunk_size)
            out.append(text[start:end])
            if end == len(text):
                break
            start += stride

        return out
