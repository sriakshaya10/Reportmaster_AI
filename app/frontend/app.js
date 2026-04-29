// Mirror of the served static app.js — supports multi-file and multi-format uploads
const API_PREFIX = '/api/v1';

// DOM utilities
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// State
let documentsIndexed = 0;

// API calls
async function uploadFile(file) {
  const form = new FormData();
  form.append('file', file, file.name);

  const res = await fetch(`${API_PREFIX}/documents/upload`, {
    method: 'POST',
    body: form,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Upload failed');
  }

  return res.json();
}

async function listDocuments() {
  const res = await fetch(`${API_PREFIX}/documents?t=${Date.now()}`, {
    method: 'GET',
    headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' }
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to list documents');
  }

  return res.json();
}

async function deleteDocument(documentId) {
  const res = await fetch(`${API_PREFIX}/documents/${documentId}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Delete failed');
  }

  return res.json();
}

async function askQuestion(question, top_k, documentId = null) {
  const body = { question, top_k };
  if (documentId) {
    body.document_id = documentId;
  }

  const res = await fetch(`${API_PREFIX}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Query failed');
  }

  return res.json();
}

// UI: Tab switching
function initTabs() {
  const navBtns = $$('.nav-btn');
  navBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tabName = btn.dataset.tab;
      
      // Update active nav button
      navBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      
      // Update active tab content
      $$('.tab-content').forEach((tab) => tab.classList.remove('active'));
      $(`#${tabName}`).classList.add('active');

      // Refresh documents list when opening ask tab
      if (tabName === 'ask') {
        loadAndDisplayDocuments();
      }
    });
  });
}

// UI: Documents List
async function loadAndDisplayDocuments() {
  try {
    const resp = await listDocuments();
    const docList = $('#documents-list');
    const docSelect = $('#document-select');
    
    if (!resp.documents || resp.documents.length === 0) {
      docList.innerHTML = '<p class="empty-msg">No documents uploaded yet.</p>';
      docSelect.innerHTML = '<option value="">All Documents</option>';
      documentsIndexed = 0;
      return;
    }

    documentsIndexed = resp.documents.length;

    // Update documents list
    docList.innerHTML = resp.documents.map(doc => {
      const uploadDate = new Date(doc.uploaded_at * 1000).toLocaleString();
      return `
        <div class="document-item">
          <div class="document-info">
            <strong>📄 ${doc.filename}</strong>
            <div class="document-meta">
              ${doc.chunks_count} chunks • ${uploadDate}
            </div>
          </div>
          <button class="btn-delete" data-doc-id="${doc.id}" title="Delete document">
            ✕
          </button>
        </div>
      `;
    }).join('');

    // Add delete event listeners
    $$('.btn-delete').forEach(btn => {
      btn.addEventListener('click', async () => {
        const docId = btn.dataset.docId;
        if (confirm('Delete this document? This cannot be undone.')) {
          try {
            await deleteDocument(docId);
            await loadAndDisplayDocuments();
          } catch (err) {
            alert(`Delete failed: ${err.message}`);
          }
        }
      });
    });

    // Update document selector
    docSelect.innerHTML = '<option value="">All Documents</option>';
    resp.documents.forEach(doc => {
      const opt = document.createElement('option');
      opt.value = doc.id;
      opt.textContent = doc.filename;
      docSelect.appendChild(opt);
    });

  } catch (err) {
    console.error('Error loading documents:', err);
  }
}

// UI: Upload zone
function initUploadZone() {
  const zone = $('#upload-zone');
  const fileInput = $('#pdf-file');
  const uploadBtn = $('#upload-btn');
  const fileName = $('#file-name');
  const status = $('#upload-status');

  zone.addEventListener('click', () => fileInput.click());

  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('dragover');
  });

  zone.addEventListener('dragleave', () => {
    zone.classList.remove('dragover');
  });

  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      handleFilesSelected(e.dataTransfer.files);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
      handleFilesSelected(e.target.files);
    }
  });

  uploadBtn.addEventListener('click', async () => {
    const files = Array.from(fileInput.files || []);
    if (files.length === 0) {
      setStatus(status, 'Pick one or more files first.', 'error');
      return;
    }

    uploadBtn.disabled = true;
    setStatus(status, `Uploading ${files.length} file(s)...`, 'info');
    $('#upload-progress').classList.remove('hidden');

    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      try {
        setStatus(status, `Uploading ${f.name} (${i + 1}/${files.length})...`, 'info');
        const resp = await uploadFile(f);
        setStatus(status, `✓ Indexed ${resp.chunks_indexed} chunks from ${resp.document_name}`, 'success');
      } catch (err) {
        setStatus(status, `✗ ${f.name}: ${err.message}`, 'error');
      }
    }

    fileInput.value = '';
    fileName.classList.add('hidden');
    uploadBtn.disabled = true;
    $('#upload-progress').classList.add('hidden');

    // Reload documents list
    await loadAndDisplayDocuments();
  });

  function handleFilesSelected(files) {
    const allowed = ['.pdf'];
    const list = Array.from(files);
    // Validate
    for (const f of list) {
      const name = f.name.toLowerCase();
      if (!allowed.some(ext => name.endsWith(ext))) {
        setStatus(status, `Unsupported file type: ${f.name}`, 'error');
        fileInput.value = '';
        return;
      }
    }

    fileName.innerHTML = `<div style="margin-bottom: 8px;"><strong>${list.length} file${list.length > 1 ? 's' : ''} selected:</strong></div>` + 
                         list.map(f => `<div style="margin-top: 4px; padding-left: 8px;">📄 ${f.name}</div>`).join('');
    fileName.classList.remove('hidden');
    uploadBtn.disabled = false;
    status.textContent = '';
  }
}

// UI: Query
function initQuery() {
  const textarea = $('#question');
  const askBtn = $('#ask-btn');
  const topK = $('#topk');
  const docSelect = $('#document-select');
  const charCount = $('#char-count');
  const results = $('#results');
  const emptyState = $('#empty-state');

  textarea.addEventListener('input', () => {
    charCount.textContent = textarea.value.length;
  });

  askBtn.addEventListener('click', async () => {
    const q = textarea.value.trim();
    if (!q) {
      alert('Please enter a question');
      return;
    }

    if (documentsIndexed === 0) {
      emptyState.classList.remove('hidden');
      results.classList.add('hidden');
      return;
    }

    const topk = parseInt(topK.value || '4', 10);
    const selectedDocId = docSelect.value || null;
    askBtn.disabled = true;
    const spinner = $('#spinner');
    spinner.classList.remove('hidden');
    emptyState.classList.add('hidden');

    try {
      const resp = await askQuestion(q, topk, selectedDocId);
      renderResults(resp);
      results.classList.remove('hidden');
    } catch (err) {
      renderError(err.message);
    } finally {
      askBtn.disabled = false;
      spinner.classList.add('hidden');
    }
  });

  function renderResults(resp) {
    const answerEl = $('#answer');
    const sourcesEl = $('#sources');
    const groundedBadge = $('#grounded-badge');

    answerEl.textContent = resp.answer || 'No answer generated.';
    sourcesEl.innerHTML = '';

    if (resp.grounded) {
      groundedBadge.classList.remove('hidden');
    } else {
      groundedBadge.classList.add('hidden');
    }

    (resp.sources || []).forEach((s, idx) => {
      const div = document.createElement('div');
      div.className = 'source';
      const text = s.text.length > 300 ? s.text.slice(0, 300) + '...' : s.text;
      div.innerHTML = `
        <strong>📄 ${s.source_file}</strong>
        <div class="meta">
          Page ${s.page_number} • Relevance: ${(s.score * 100).toFixed(1)}%
        </div>
        <div class="text">"${text}"</div>
      `;
      sourcesEl.appendChild(div);
    });
  }

  function renderError(msg) {
    const answerEl = $('#answer');
    answerEl.textContent = `⚠️ ${msg}`;
    $('#sources').innerHTML = '';
    $('#grounded-badge').classList.add('hidden');
    $('#results').classList.remove('hidden');
  }
}

// Helper: Set status message
function setStatus(el, msg, type) {
  el.textContent = msg;
  el.className = `status-message ${type}`;
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initUploadZone();
  initQuery();
  loadAndDisplayDocuments();
});
