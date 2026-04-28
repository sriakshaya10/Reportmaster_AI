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

async function askQuestion(question, top_k) {
  const res = await fetch(`${API_PREFIX}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k }),
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
    });
  });
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
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
      handleFileSelected(e.target.files[0]);
    }
  });

  uploadBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
      setStatus(status, 'Pick a PDF file first.', 'error');
      return;
    }

    uploadBtn.disabled = true;
    setStatus(status, 'Uploading...', 'info');
    $('#upload-progress').classList.remove('hidden');

    try {
      const resp = await uploadFile(file);
      documentsIndexed++;
      setStatus(status, `✓ Indexed ${resp.chunks_indexed} chunks from ${resp.document_name}`, 'success');
      fileInput.value = '';
      fileName.classList.add('hidden');
      uploadBtn.disabled = true;
      $('#upload-progress').classList.add('hidden');
    } catch (err) {
      setStatus(status, `✗ ${err.message}`, 'error');
      uploadBtn.disabled = false;
      $('#upload-progress').classList.add('hidden');
    }
  });

  function handleFileSelected(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setStatus(status, 'Only PDF files are supported.', 'error');
      fileInput.value = '';
      return;
    }
    fileName.textContent = `📄 ${file.name}`;
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
      setStatus(emptyState, 'No documents indexed yet. Upload a manual first.', 'error');
      return;
    }

    const topk = parseInt(topK.value || '4', 10);
    askBtn.disabled = true;
    const spinner = $('#spinner');
    spinner.classList.remove('hidden');

    try {
      const resp = await askQuestion(q, topk);
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
});