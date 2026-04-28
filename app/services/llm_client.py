import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer
import re

from app.core.config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._local_embedder: SentenceTransformer | None = None
        self._groq_client: Groq | None = None

        if settings.groq_api_key:
            self._groq_client = Groq(api_key=settings.groq_api_key)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings using local sentence-transformers model."""
        if self._local_embedder is None:
            self._local_embedder = SentenceTransformer(self.settings.local_embed_model)

        embeddings = self._local_embedder.encode(texts, convert_to_numpy=True)
        return np.array(embeddings, dtype=np.float32)

    def generate_answer(self, question: str, contexts: list[dict]) -> tuple[str, str]:
        if not contexts:
            return (
                "No relevant content was found in the indexed manuals for this question.",
                "retrieval-only",
            )

        contexts = contexts[:3]

        context_block = "\n\n".join(
            [
                f"Source: {c['source_file']} | Page: {c['page_number']}\nContent: {c['text']}"
                for c in contexts
            ]
        )

        prompt = (
            "You are a financial reporting assistant. "
            "Answer only using the provided context. "
            "If the context is insufficient, say: 'I could not find that in the indexed manual.' "
            "Do not add filler, explanations, or unrelated advice. "
            "Write exactly 2 to 3 short sentences. Include source references inline like "
            "(source: <file>, page <n>).\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context_block}"
        )

        if not self._groq_client:
            joined = "\n\n".join(
                [
                    f"[{c['source_file']} p.{c['page_number']}] {c['text'][:280]}"
                    for c in contexts
                ]
            )
            fallback = (
                "Groq API key is not configured. Here are the most relevant extracted passages:\n\n"
                f"{joined}"
            )
            return fallback, "retrieval-only"

        try:
            response = self._groq_client.chat.completions.create(
                model=self.settings.groq_model,
                temperature=0,
                max_tokens=180,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You produce grounded financial-reporting answers in exactly 2 to 3 sentences. "
                            "Never invent facts. If the context is insufficient, say so."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            answer = response.choices[0].message.content if response.choices else ""
            answer = (answer or "").strip()
            if not answer:
                answer = "No answer generated."
            answer = self._limit_sentences(answer, 3)
            return answer, self.settings.groq_model
        except Exception as e:
            joined = "\n\n".join(
                [
                    f"[{c['source_file']} p.{c['page_number']}] {c['text'][:280]}"
                    for c in contexts[:3]
                ]
            )
            fallback = (
                f"Error generating answer: {str(e)}\n\n"
                "Here are the most relevant extracted passages instead:\n\n"
                f"{joined}"
            )
            return fallback, "retrieval-only"

    @staticmethod
    def _limit_sentences(text: str, max_sentences: int) -> str:
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        if len(parts) <= max_sentences:
            return text.strip()
        return " ".join(parts[:max_sentences]).strip()
