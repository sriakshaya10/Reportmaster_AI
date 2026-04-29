# ReportMaster AI – Technical Architecture

## System Overview

ReportMaster AI is a Retrieval-Augmented Generation (RAG) system designed with a layered, modular architecture. It converts PDF financial manuals into an intelligent Q&A platform using semantic search and optional LLM-based answer generation.

## Prior Knowledge Required

To work effectively on this project, you should already be comfortable with programming language fundamentals, especially Python and JavaScript, along with web basics such as HTML, CSS, DOM manipulation, and asynchronous client-side code. You should also understand framework basics for FastAPI, Pydantic, and Python package/module structure, plus database fundamentals such as indexing, persistence formats, and basic search concepts. Networking and cloud concepts are important too, including HTTP, REST APIs, file uploads, CORS, environment variables, and API keys. Finally, you should have AI/ML fundamentals such as embeddings, chunking, semantic search, cosine similarity, and retrieval-augmented generation.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER LAYER                               │
│  Web Browser (HTML, CSS, JavaScript SPA)                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│  Frontend (app/frontend/)                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│  FastAPI Server + Routes + Configuration                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RAG SERVICE LAYER                            │
│  RAG Pipeline Orchestration                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                          │
│  Document Processing + Vector Search + LLM Generation           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                            │
│  Vector Store & Persistence                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENCE LAYER                            │
│  Local File Storage (JSON + NumPy)                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Breakdown

### 1. USER LAYER
**Component:** Web Browser
- HTML/CSS/JavaScript Single Page Application
- Responsive design for desktop and mobile
- Real-time status updates and progress indicators

---

### 2. PRESENTATION LAYER
**Location:** `app/frontend/`

**Components:**

#### index.html
- Main SPA structure with three tabs
- Tab 1: Upload Manual (drag-drop, file validation)
- Tab 2: Ask Question (query input, results display)
- Tab 3: About (system information)
- Semantic markup with accessibility support

#### app.js
- Tab switching logic with event delegation
- File upload handling (validation, FormData)
- API call abstraction (uploadFile, askQuestion)
- Result rendering with dynamic DOM manipulation
- Status message management (success, error, info)
- Character count tracking for question input
- Spinner animation and progress bar control

#### styles.css
- CSS Variables for consistent theming
- Dark theme (primary: #0b5fff, secondary: #7c3aed)
- Sidebar navigation with 280px fixed width
- Responsive layout with flexbox
- Animations (fade-in, spin, slide-up)
- Mobile breakpoint at 768px
- Form controls styling (textarea, select)
- Result cards with hover effects

**Features:**
- Upload Tab: Drag-drop zone, file preview, upload button, progress bar
- Ask Tab: Question textarea (1000 char max), top-k selector, answer display
- About Tab: FAQs and system documentation

---

### 3. APPLICATION LAYER
**Location:** `app/`

#### main.py
- FastAPI application factory
- API router registration with `/api/v1` prefix
- Static file mounting for `/static` (CSS, JS)
- Frontend SPA mounting at `/` (html=True for fallback)
- CORS configuration
- Request/response validation via Pydantic

#### routes.py (`app/api/`)
**Endpoints:**

```python
GET /health
- Returns: {"status": "ok", "app": "ReportMaster AI"}
- Purpose: Health check for monitoring and uptime tracking

POST /api/v1/documents/upload
- Input: file (multipart/form-data, PDF only)
- Validation: Filename required, .pdf extension checked
- Processing: 
  1. Saves to data/uploads/ (no deletion of previous files)
  2. Generates unique document_id
  3. Calls RAGService.ingest_document()
  4. Stores index in documents/[doc_id]/
- Output: UploadResponse (document_id, document_name, chunks_indexed, message)
- Error Handling: 400 for invalid files, 500 for processing errors

GET /api/v1/documents
- Returns: DocumentListResponse (documents[], total_documents, total_chunks)
- Purpose: List all uploaded documents with metadata
- No input required
- Output includes upload timestamps and chunk counts per document

DELETE /api/v1/documents/{document_id}
- Input: document_id (path parameter)
- Purpose: Delete a specific document from the index
- Processing:
  1. Removes documents/[doc_id]/ directory
  2. Updates documents.json metadata
  3. Rebuilds global search index
- Output: {"message": "Document deleted successfully"}
- Error Handling: 404 if document not found

POST /api/v1/query
- Input: QueryRequest (question: str, top_k: int | None, document_id: str | None)
- Validation: question min_length=3, top_k 1-10 range, document_id optional
- Processing:
  1. If document_id provided: search only in that document
  2. If not provided: search across all documents
  3. Calls RAGService.answer_question()
- Output: QueryResponse (answer, grounded, model_used, sources[])
- Error Handling: 400 for invalid input, 500 for processing errors
- Source metadata now includes document_id for tracking
```

#### config.py (`app/core/`)
**Settings Class:**
```python
app_name: str = "ReportMaster AI"
api_v1_prefix: str = "/api/v1"

# Directories
data_dir: Path = Path("./data")
upload_dir: Path = Path("./data/uploads")
index_dir: Path = Path("./data/index")

# Processing Parameters
top_k: int = 3  # Default results to retrieve
chunk_size: int = 800  # Characters per chunk
chunk_overlap: int = 120  # Overlap between chunks

# LLM Configuration
groq_api_key: str = ""  # Optional
groq_model: str = "llama-3.1-8b-instant"
local_embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"

# Methods
ensure_directories()  # Creates required folders on startup
```

#### schemas.py (`app/models/`)
**Data Models (Pydantic):**

```python
class QueryRequest:
  question: str  # min_length=3
  top_k: int | None  # range 1-10
  document_id: str | None  # optional: search in specific document

class SourceSnippet:
  chunk_id: str
  source_file: str
  page_number: int
  score: float  # 0.0-1.0
  text: str
  document_id: str | None  # identifies which document source came from

class QueryResponse:
  answer: str
  grounded: bool  # True if sources exist
  model_used: str  # "llama-3.1-8b-instant" or "retrieval-only"
  sources: list[SourceSnippet]

class UploadResponse:
  document_id: str  # unique document identifier
  document_name: str
  chunks_indexed: int
  message: str

class DocumentMetadata:
  id: str  # unique document identifier
  filename: str
  chunks_count: int
  uploaded_at: float  # Unix timestamp

class DocumentListResponse:
  documents: list[DocumentMetadata]
  total_documents: int
  total_chunks: int  # sum across all documents
```

---

### 4. RAG SERVICE LAYER
**Location:** `app/services/rag_service.py`

**RAGService Class:**
```python
def __init__(settings):
    self.processor = DocumentProcessor(chunk_size, chunk_overlap)
    self.llm = LLMClient(settings)
    self.store = VectorStore(settings.index_dir)
    self.settings = settings

def ingest_document(file_path, document_id=None):
    # 1. Extract chunks from PDF
    chunks = self.processor.extract_chunks(file_path)
    
    # 2. Add document to store (no clearing of previous docs)
    doc_id, count = self.store.add_document(
        document_id=document_id,
        chunks=chunks,
        embedder=self.llm.embed_texts,
        filename=file_path.name
    )
    
    return doc_id, count

def delete_document(document_id):
    # Remove document from index and rebuild
    return self.store.delete_document(document_id)

def list_documents():
    # Get metadata for all indexed documents
    return self.store.get_documents()

def answer_question(question, top_k=None, document_id=None):
    # 1. Determine number of results
    k = top_k or self.settings.top_k
    
    # 2. Retrieve relevant chunks (optionally filtered by document_id)
    contexts = self.store.search(
        question, k, 
        self.llm.embed_texts,
        document_id=document_id
    )
    
    # 3. Generate answer
    answer, model_used = self.llm.generate_answer(question, contexts)
    
    # 4. Build response
    return {
        "answer": answer,
        "grounded": len(contexts) > 0,
        "model_used": model_used,
        "sources": contexts
    }
```

**Responsibilities:**
- Orchestrates multi-document ingestion pipeline
- Manages document deletion and index rebuilding
- Provides scoped query capabilities (all documents or specific document)
- Manages query processing workflow
- Coordinates between processors, stores, and LLM

---

### 5. BUSINESS LOGIC LAYER

#### DocumentProcessor (`app/services/document_processor.py`)

**Purpose:** Extract and chunk PDF text

```python
def __init__(chunk_size=800, chunk_overlap=120):
    self.chunk_size = chunk_size
    self.chunk_overlap = chunk_overlap

def extract_chunks(file_path):
    # 1. Read PDF using pypdf.PdfReader
    reader = PdfReader(str(file_path))
    chunks = []
    
    # 2. Iterate pages
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text:
            continue
        
        # 3. Chunk page text
        page_chunks = self._chunk_text(text)
        
        # 4. Create metadata
        for idx, chunk_text in enumerate(page_chunks):
            chunks.append({
                "chunk_id": f"{filename}_p{page_index}_c{idx}",
                "source_file": filename,
                "page_number": page_index,
                "text": chunk_text
            })
    
    return chunks

def _chunk_text(text):
    # Sliding window algorithm
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    stride = max(1, chunk_size - chunk_overlap)
    start = 0
    
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += stride
    
    return chunks
```

**Features:**
- Handles multi-page PDFs
- Skips empty pages
- Preserves page numbers for traceability
- Overlapping chunks preserve context

---

#### LLMClient (`app/services/llm_client.py`)

**Purpose:** Generate embeddings and answers

```python
def __init__(settings):
    self.settings = settings
    self._local_embedder = None
    self._groq_client = None
    
    if settings.groq_api_key:
        self._groq_client = Groq(api_key=settings.groq_api_key)

def embed_texts(texts):
    # Lazy initialization of embedding model
    if self._local_embedder is None:
        self._local_embedder = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    
    # Generate embeddings
    embeddings = self._local_embedder.encode(
        texts, 
        convert_to_numpy=True
    )
    
    return np.array(embeddings, dtype=np.float32)

def generate_answer(question, contexts):
    # Handle no-results case
    if not contexts:
        return (
            "No relevant content found in indexed manuals.",
            "retrieval-only"
        )
    
    # Limit to top-3 contexts
    contexts = contexts[:3]
    
    # Build context block
    context_block = "\n\n".join([
        f"Source: {c['source_file']} | Page: {c['page_number']}\n"
        f"Content: {c['text']}"
        for c in contexts
    ])
    
    # If Groq configured
    if self._groq_client:
        prompt = (
            "You are a financial reporting assistant. "
            "Answer only using the provided context. "
            "If insufficient, say: 'I could not find that in the indexed manual.' "
            "Write 2-3 short sentences. Include inline source references.\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context_block}"
        )
        
        try:
            response = self._groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                temperature=0,
                max_tokens=180,
                messages=[
                    {
                        "role": "system",
                        "content": "You produce grounded answers. Never invent facts."
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            
            answer = response.choices[0].message.content.strip()
            answer = self._limit_sentences(answer, 3)
            return answer, "llama-3.1-8b-instant"
        
        except Exception as e:
            # Fallback on error
            fallback = self._build_fallback(contexts)
            return fallback, "retrieval-only"
    
    # Fallback if no Groq
    fallback = self._build_fallback(contexts)
    return fallback, "retrieval-only"

def _build_fallback(contexts):
    return "\n\n".join([
        f"[{c['source_file']} p.{c['page_number']}] {c['text'][:280]}"
        for c in contexts[:3]
    ])

def _limit_sentences(text, max_sentences):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(parts) <= max_sentences:
        return text.strip()
    return " ".join(parts[:max_sentences]).strip()
```

**Features:**
- Lazy loads embedding model
- Optional Groq LLM integration
- Graceful degradation to retrieval-only
- Temperature=0 for deterministic output
- Max 180 tokens per answer (2-3 sentences)
- Inline source references in prompts

---

#### VectorStore (`app/services/vector_store.py`)

**Purpose:** Semantic similarity search

```python
def __init__(index_dir):
    self.index_dir = index_dir
    self.meta_path = index_dir / "chunks.json"
    self.vec_path = index_dir / "embeddings.npy"
    self.records = []
    self.embeddings = None
    self.load()

def load():
    # Restore from disk
    if self.meta_path.exists() and self.vec_path.exists():
        self.records = json.loads(self.meta_path.read_text())
        self.embeddings = np.load(self.vec_path)

def save():
    # Persist to disk
    self.meta_path.write_text(
        json.dumps(self.records, ensure_ascii=True, indent=2)
    )
    if self.embeddings is not None:
        np.save(self.vec_path, self.embeddings)

def clear():
    # Reset index
    self.records = []
    self.embeddings = None
    if self.meta_path.exists():
        self.meta_path.unlink()
    if self.vec_path.exists():
        self.vec_path.unlink()

def add_records(chunks, embedder):
    # 1. Generate embeddings
    vectors = embedder([c["text"] for c in chunks])
    vectors = self._normalize(vectors)
    
    # 2. Append to existing embeddings
    if self.embeddings is None:
        self.embeddings = vectors
    else:
        self.embeddings = np.vstack([self.embeddings, vectors])
    
    # 3. Extend records
    self.records.extend(chunks)
    
    # 4. Persist
    self.save()
    
    return len(chunks)

def search(question, top_k, embedder):
    # 1. Handle empty index
    if self.embeddings is None or not self.records:
        return []
    
    # 2. Embed question
    q_vec = embedder([question])
    q_vec = self._normalize(q_vec)[0]
    
    # 3. Compute cosine similarity
    scores = self.embeddings @ q_vec
    
    # 4. Get top-k indices
    indices = np.argsort(scores)[::-1][:top_k]
    
    # 5. Build results with scores
    results = []
    for idx in indices:
        rec = dict(self.records[int(idx)])
        rec["score"] = float(scores[int(idx)])
        results.append(rec)
    
    return results

@staticmethod
def _normalize(matrix):
    # L2 normalization for cosine similarity
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12  # Avoid division by zero
    return matrix / norms
```

**Algorithm:**
- **Indexing:** Extract → Embed → Normalize → Store per-document → Merge to global index
- **Search:** Embed question → Normalize → Dot product across relevant chunks → Filter by doc_id if specified → Sort → Return top-k

**Performance:**
- Cosine similarity: O(n) with n=number of chunks (all documents combined)
- Sub-100ms for typical indexes
- Per-document filtering adds negligible overhead
- Normalized dot product ensures numerical stability
- Multi-document support: scales linearly with total chunks across all documents

---

### 6. DATA ACCESS LAYER

**VectorStore** handles all data persistence and retrieval operations with multi-document support.

**Storage Format:**
- `documents.json`: Metadata mapping document_id → {filename, chunks_count, uploaded_at}
- `documents/[doc_id]/chunks.json`: Metadata (chunk_id, source_file, page_number, text, document_id)
- `documents/[doc_id]/embeddings.npy`: Binary NumPy matrix (n_chunks × 384 dimensions) per document

**Operations:**
- `load()`: Restore all documents from disk, merge into global index (~100-200ms for multiple docs)
- `save()`: Persist index to disk (~50ms)
- `search()`: Find similar chunks (<10ms)
- `add_records()`: Add new chunks with embeddings
- `clear()`: Reset index

---

### 7. PERSISTENCE LAYER

**Storage Structure:**
```
data/
├── uploads/
│   ├── manual1.pdf
│   ├── manual2.pdf
│   └── *.pdf  (All uploaded PDFs stored here)
└── index/
    ├── documents.json  (Metadata for all documents)
    └── documents/
        ├── doc_1/
        │   ├── chunks.json
        │   └── embeddings.npy
        ├── doc_2/
        │   ├── chunks.json
        │   └── embeddings.npy
        └── doc_N/  (Namespaced by document_id)
```

**File Formats:**
- **documents.json:** JSON object mapping document_id to metadata (filename, chunks_count, uploaded_at)
- **documents/[doc_id]/chunks.json:** JSON array with chunk metadata (includes document_id field)
- **documents/[doc_id]/embeddings.npy:** NumPy binary format (float32, row-major)

**Characteristics:**
- **Multi-document support:** Each document stored in isolated directory
- **Global index:** Chunks combined into single search index in memory
- **Per-document retrieval:** Can search all documents or filter by document_id
- **Metadata tracking:** Upload timestamps, chunk counts preserved per document
- **Local-only storage:** No external database required

---

## Multi-Document Architecture

### Document Management Features

**Upload & Indexing:**
- Multiple files can be uploaded without clearing previous indexes
- Each upload receives unique document_id (UUID-based)
- Chunks tagged with document_id for tracking and filtering
- Metadata persisted to documents.json

**Document Operations:**
```
POST /api/v1/documents/upload
  ├─ File validation (PDF only)
  ├─ Save to data/uploads/
  ├─ Extract and chunk text
  ├─ Generate embeddings
  ├─ Create documents/[doc_id]/ directory
  ├─ Store chunks.json and embeddings.npy
  ├─ Update documents.json metadata
  └─ Return (document_id, chunks_indexed)

GET /api/v1/documents
  ├─ Load documents.json
  ├─ Return list of all documents with metadata
  └─ Include total_documents and total_chunks counts

DELETE /api/v1/documents/{document_id}
  ├─ Remove documents/[doc_id]/ directory
  ├─ Update documents.json
  ├─ Rebuild in-memory index
  └─ Return success confirmation
```

**Query Scope:**
```
POST /api/v1/query
  ├─ Input: question, top_k, optional document_id
  ├─ If document_id provided:
  │   └─ Search only in specified document
  └─ If not provided:
      └─ Search across all documents
```

### VectorStore Multi-Document Methods

```python
add_document(document_id, chunks, embedder, filename)
  └─ Store document index in isolated directory

delete_document(document_id)
  └─ Remove document and rebuild global index

get_documents()
  └─ Return list of all document metadata

search(question, top_k, embedder, document_id=None)
  └─ Search all or filtered by document_id
```

---

## Data Flow Diagrams

### Upload & Indexing Flow (Multi-Document)
```
User Uploads PDF
       ↓
FastAPI /upload endpoint
       ↓
Validate & Save to data/uploads/
       ↓
Generate unique document_id (UUID-based)
       ↓
DocumentProcessor.extract_chunks()
   ├─ Read PDF pages
   ├─ Extract text
   ├─ Chunk with overlap
   ├─ Add document_id to each chunk
   └─ Return metadata list
       ↓
LLMClient.embed_texts()
   ├─ Load SentenceTransformer
   ├─ Generate 384-dim vectors
   └─ Return np.ndarray
       ↓
VectorStore.add_document()
   ├─ Create documents/[doc_id]/ directory
   ├─ Normalize vectors (L2)
   ├─ Save to documents/[doc_id]/chunks.json
   ├─ Save to documents/[doc_id]/embeddings.npy
   ├─ Merge with global index in memory
   ├─ Update documents.json metadata
   └─ Return (document_id, chunk_count)
       ↓
Response: UploadResponse (document_id, chunks_indexed)
       ↓
Frontend refreshes document list with new file
```

### Query & Answer Flow (Multi-Document)
```
User Asks Question (Optional: Select Document)
       ↓
FastAPI /query endpoint
       ↓
QueryRequest validation (includes optional document_id)
       ↓
RAGService.answer_question()
   ├─ VectorStore.search(document_id=provided_or_none)
   │   ├─ Embed question
   │   ├─ Normalize
   │   ├─ Cosine similarity across relevant chunks
   │   ├─ If document_id: filter results to that document
   │   └─ Return top-k chunks with document_id
   ├─ LLMClient.generate_answer()
   │   ├─ If Groq configured:
   │   │   ├─ Build prompt
   │   │   ├─ Call Groq API
   │   │   └─ Parse response
   │   └─ Else: Build fallback excerpts
   └─ Build response dict
       ↓
Response: QueryResponse (answer, sources with document_id)
       ↓
Frontend renders answer + source cards showing which document each source came from
```

### Delete Document Flow
```
User Clicks Delete Button on Document
       ↓
Frontend Confirmation Dialog
       ↓
DELETE /api/v1/documents/{document_id}
       ↓
RAGService.delete_document()
   ├─ VectorStore.delete_document(document_id)
   │   ├─ Remove documents/[doc_id]/ directory
   │   ├─ Update documents.json
   │   ├─ Reload and rebuild global index
   │   │   (from remaining documents)
   │   └─ Return success
   └─ Return success response
       ↓
Response: Confirmation message
       ↓
Frontend refreshes document list and document selector
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend Framework | FastAPI 0.116.1 | REST API with async support |
| ASGI Server | Uvicorn 0.35.0 | Production-grade server |
| Data Validation | Pydantic 2.11.7 | Type-safe request/response |
| PDF Processing | pypdf 5.9.0 | Text extraction from PDFs |
| Embeddings | sentence-transformers 3.0.1 | Local semantic vectors |
| Vector Ops | NumPy 2.3.2 | Similarity calculations |
| LLM Generation | Groq 0.30.0 | Optional answer generation |
| File Upload | python-multipart 0.0.20 | Multipart form data |
| Environment Config | pydantic-settings 2.10.1 | .env file management |
| Frontend | HTML/CSS/JavaScript | Single Page Application |

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| PDF Indexing | 5-15s | 20-30 page manual |
| Question Embedding | ~5ms | SentenceTransformer on CPU |
| Vector Search | <10ms | Cosine similarity O(n) |
| LLM Generation | 1-2s | Groq API call |
| Retrieval-Only Response | <50ms | No LLM call |
| Index Load | <100ms | From disk files |
| Total Query (with LLM) | 1-3s | Full end-to-end |
| Total Query (no LLM) | <100ms | Retrieval only |

---

## Key Design Patterns

1. **Service Layer Pattern** – RAGService orchestrates components
2. **Dependency Injection** – Settings passed to services
3. **Factory Pattern** – Lazy initialization of LLMClient
4. **Repository Pattern** – VectorStore abstracts data access
5. **Adapter Pattern** – LLMClient adapts Groq API
6. **Fallback Pattern** – Graceful degradation without LLM

---

## Security & Reliability

- **Input Validation:** Pydantic models validate all API inputs
- **Error Handling:** Try-catch blocks with descriptive errors
- **Graceful Degradation:** Works without Groq API key
- **Local Storage:** No external data transfer required
- **File Validation:** PDF extension check, size limits
- **Isolation:** Each upload clears previous indexes

---

## Future Enhancement Points

1. **Vector Database Integration** – Replace local storage with Pinecone/Weaviate for production scaling
2. **OCR Capability** – Support scanned PDFs with text extraction via Tesseract
3. **Authentication & Authorization** – User login, access control, per-user document isolation
4. **Query History & Analytics** – Log queries/answers, query patterns, usage statistics
5. **Advanced Search Filters** – Date ranges, chunk metadata, document type filters
6. **Export Functionality** – Download answers as PDF/DOCX with source citations
7. **Batch Processing** – Upload multiple files simultaneously
8. **Custom LLM Models** – Support for alternative LLM providers beyond Groq
9. **Semantic Document Clustering** – Auto-organize documents by topic
10. **Performance Optimizations** – Approximate nearest neighbor search for large indexes
