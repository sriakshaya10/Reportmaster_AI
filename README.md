# ReportMaster AI

ReportMaster AI is a FastAPI-based Retrieval-Augmented Generation (RAG) backend for financial reporting manuals.

## What this starter includes

- Document upload API for PDF manuals
- Chunking and indexing pipeline
- Semantic retrieval using embeddings
- Grounded answer generation with source citations
- Groq-powered generation if API key is set
- Local fallback answer mode if no API key is set

## Project structure

- `app/main.py`: FastAPI app entrypoint
- `app/api/routes.py`: API routes
- `app/core/config.py`: environment configuration
- `app/models/schemas.py`: request/response schemas
- `app/services/document_processor.py`: PDF parsing + chunking
- `app/services/vector_store.py`: local vector index persistence
- `app/services/llm_client.py`: generation and embedding client
- `app/services/rag_service.py`: retrieval + answer orchestration
- `data/uploads`: uploaded source files
- `data/index`: persisted embeddings and metadata

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies.
3. Copy `.env.example` to `.env` and set optional keys.
4. Run the API.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API docs will be available at:

- `http://127.0.0.1:8000/docs`

## Main endpoints

- `GET /health`: health check
- `POST /api/v1/documents/upload`: upload and index a PDF
- `POST /api/v1/query`: ask grounded questions

## Example query payload

```json
{
  "question": "What is the rule for revenue recognition?",
  "top_k": 4
}
```

## Notes

- For best answer quality, set `GROQ_API_KEY`.
- Without OpenAI credentials, the API still returns retrieval-backed extractive answers.
