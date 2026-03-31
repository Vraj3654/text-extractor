/* =============================================
   AI Text Extractor Pro — Main Script
   ============================================= */

let currentDocId = null;
let cameraStream = null;
let liveOcrInterval = null;
let uploadInProgress = false;

// =====================
// AUTH STATE & HELPERS
// =====================
let authToken = localStorage.getItem('token') || null;

async function authFetch(url, options = {}) {
  if (!options.headers) options.headers = {};
  if (authToken) options.headers['Authorization'] = `Bearer ${authToken}`;
  
  const res = await fetch(url, options);
  if (res.status === 401 || res.status === 403) {
      if (res.status === 403) alert("Usage limit reached/exceeded!");
      if (res.status === 401 && !url.includes('/api/token')) logout();
  }
  return res;
}

document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
       document.getElementById('auth-overlay').style.display = 'none';
       document.getElementById('main-app').style.display = 'block';
       document.getElementById('logout-btn').style.display = 'inline-block';
       fetchUsage();
    }
});

async function handleLogin() {
    const u = document.getElementById('auth-username').value;
    const p = document.getElementById('auth-password').value;
    const err = document.getElementById('auth-error');
    err.style.display = 'none';

    const fd = new URLSearchParams();
    fd.append('username', u);
    fd.append('password', p);

    try {
        const res = await fetch('/api/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: fd
        });
        if (!res.ok) throw new Error("Invalid credentials");
        const data = await res.json();
        
        authToken = data.access_token;
        localStorage.setItem('token', authToken);
        
        document.getElementById('auth-overlay').style.display = 'none';
        document.getElementById('main-app').style.display = 'block';
        document.getElementById('logout-btn').style.display = 'inline-block';
        updateUsage(data.usage_count, data.max_limit);
        
    } catch (e) {
        err.textContent = e.message;
        err.style.display = 'block';
    }
}

async function handleRegister() {
    const u = document.getElementById('auth-username').value;
    const p = document.getElementById('auth-password').value;
    const err = document.getElementById('auth-error');
    err.style.display = 'none';

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: u, password: p})
        });
        if (!res.ok) {
            const d = await res.json();
            throw new Error(d.detail);
        }
        alert("Registered! Logging in...");
        handleLogin();
    } catch(e) {
        err.textContent = e.message;
        err.style.display = 'block';
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('token');
    document.getElementById('main-app').style.display = 'none';
    document.getElementById('logout-btn').style.display = 'none';
    document.getElementById('auth-overlay').style.display = 'flex';
}

async function fetchUsage() {
    try {
        const res = await authFetch('/api/me');
        if (res.ok) {
            const data = await res.json();
            updateUsage(data.usage_count, data.max_limit);
        }
    } catch(e){}
}

function updateUsage(used, max) {
    const badge = document.getElementById('usage-badge');
    badge.style.display = 'inline-block';
    badge.textContent = `Credits: ${used}/${max}`;
    if (used >= max) {
       badge.style.background = 'rgba(255,100,100,0.2)';
       badge.style.borderColor = '#ff6464';
       badge.style.color = '#ff6464';
    } else {
       badge.style.background = 'rgba(124,110,245,0.2)';
       badge.style.borderColor = 'var(--primary)';
       badge.style.color = 'var(--text-muted)';
    }
}

// =====================
// TABS
// =====================
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const target = tab.dataset.tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(`tab-content-${target}`).classList.add('active');
    if (target === 'history') loadHistory();
  });
});

// =====================
// DRAG & DROP
// =====================
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');

dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) handleFileUpload(e.dataTransfer.files[0]);
});
dropzone.addEventListener('click', e => {
  if (!e.target.closest('label')) fileInput.click();
});
fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) handleFileUpload(fileInput.files[0]);
});

// =====================
// UPLOAD & OCR
// =====================
async function handleFileUpload(file) {
  if (uploadInProgress) return;
  if (file.size > 10 * 1024 * 1024) { alert('File too large (max 10MB)'); return; }

  uploadInProgress = true;
  showProgress(true);

  const language = document.getElementById('language-select').value;
  const formData = new FormData();
  formData.append('file', file);
  formData.append('language', language);

  try {
    animateProgress(0, 60, 1200);
    const res = await authFetch('/api/upload', { method: 'POST', body: formData });
    animateProgress(60, 90, 400);

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    const data = await res.json();
    animateProgress(90, 100, 300);

    currentDocId = data.id;
    displayOCRResult(data);
    await runAnalysis(data.id);
    showProgress(false);
  } catch (err) {
    showProgress(false);
    alert('❌ Error: ' + err.message);
  } finally {
    uploadInProgress = false;
    fileInput.value = '';
  }
}

function displayOCRResult(data) {
  document.getElementById('results-panel').style.display = 'block';
  document.getElementById('raw-text').textContent = data.raw_text || '(no text detected)';
  document.getElementById('corrected-text').textContent = data.corrected_text || '(no text)';

  const conf = data.confidence || 0;
  const badge = document.getElementById('confidence-badge');
  badge.textContent = `${conf.toFixed(1)}% confidence`;
  badge.style.color = conf > 70 ? '#4ade80' : conf > 40 ? '#facc15' : '#f87171';

  buildExportButtons(data.id, data.filename);

  // Reset translation
  document.getElementById('translated-text').style.display = 'none';
  document.getElementById('translate-actions').style.display = 'none';
  document.getElementById('translate-loading').style.display = 'none';
}

// =====================
// ANALYSIS (Classification + Key Info)
// =====================
async function runAnalysis(docId) {
  const classifyLoading = document.getElementById('classify-loading');
  classifyLoading.style.display = 'inline';

  try {
    const res = await authFetch(`/api/analyze/${docId}`);
    if (!res.ok) return;
    const data = await res.json();
    classifyLoading.style.display = 'none';
    renderClassification(data.classification);
    renderKeyInfo(data.key_info);
    renderAutoFillForm(data.key_info);
  } catch (e) {
    classifyLoading.textContent = 'Analysis unavailable';
  }
}

function renderClassification(c) {
  const el = document.getElementById('classify-result');
  if (!c || c.type === 'Unknown') {
    el.innerHTML = '<span class="muted">Could not classify document.</span>';
    return;
  }
  el.innerHTML = `
    <div class="classify-icon">${c.icon}</div>
    <div class="classify-info">
      <h4>${c.type}</h4>
      <p>Document type identified by AI keyword analysis</p>
    </div>
    <div class="classify-confidence">
      <div class="big-num">${c.confidence.toFixed(0)}%</div>
      <div class="label">match score</div>
    </div>
  `;
}

function renderKeyInfo(info) {
  const el = document.getElementById('key-info-result');
  if (!info || Object.keys(info).length === 0) {
    el.innerHTML = '<span class="no-info">No key data detected in this document.</span>';
    return;
  }

  const LABELS = {
    dates: '📅 Dates',
    emails: '📧 Emails',
    phone_numbers: '📞 Phone Numbers',
    amounts: '💰 Amounts',
    urls: '🔗 URLs',
    pan_numbers: '🪪 PAN Numbers',
    aadhaar_numbers: '🪪 Aadhaar',
    percentages: '📊 Percentages',
    names: '👤 Names',
  };

  el.innerHTML = Object.entries(info).map(([key, vals]) => `
    <div class="info-chip">
      <div class="chip-label">${LABELS[key] || key}</div>
      <div class="chip-value">${(Array.isArray(vals) ? vals : [vals]).join(', ')}</div>
    </div>
  `).join('');
}

// =====================
// TRANSLATION
// =====================
async function translateDoc() {
  if (!currentDocId) { alert('Please upload a document first.'); return; }
  const langCode = document.getElementById('translate-lang').value;
  if (!langCode) { alert('Please select a target language.'); return; }

  const loading = document.getElementById('translate-loading');
  const output = document.getElementById('translated-text');
  const actions = document.getElementById('translate-actions');

  loading.style.display = 'inline';
  output.style.display = 'none';
  actions.style.display = 'none';

  try {
    const fd = new FormData();
    fd.append('doc_id', currentDocId);
    fd.append('target_language', langCode);

    const res = await authFetch('/api/translate', { method: 'POST', body: fd });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Translation failed');
    }
    const data = await res.json();
    loading.style.display = 'none';
    output.textContent = data.translated || '(empty)';
    output.style.display = 'block';
    actions.style.display = 'block';
    if (data.truncated) {
      output.textContent += '\n\n[Note: Text was truncated to 4500 characters for translation]';
    }
  } catch (err) {
    loading.style.display = 'none';
    output.textContent = '❌ ' + err.message;
    output.style.display = 'block';
  }
}

// =====================
// EXPORT
// =====================
function buildExportButtons(docId, filename) {
  const container = document.getElementById('export-buttons');
  const formats = [
    { type: 'txt', label: '📝 TXT' },
    { type: 'json', label: '🗂 JSON' },
    { type: 'docx', label: '📘 DOCX' },
    { type: 'pdf', label: '📕 PDF' },
  ];
  container.innerHTML = formats.map(f => `
    <button class="btn btn-export" onclick="downloadExport(${docId},'${f.type}')">${f.label}</button>
  `).join('');
}

function downloadExport(docId, format) {
  window.open(`/api/export/${docId}/${format}`, '_blank');
}

// =====================
// CAMERA OCR
// =====================
async function toggleCamera() {
  const btn = document.getElementById('camera-btn');
  const snapBtn = document.getElementById('snapshot-btn');
  const overlay = document.getElementById('camera-overlay');
  const scanLine = document.getElementById('scan-line');
  const status = document.getElementById('camera-status');

  if (cameraStream) {
    // Stop camera
    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
    document.getElementById('camera-feed').srcObject = null;
    if (liveOcrInterval) { clearInterval(liveOcrInterval); liveOcrInterval = null; }
    btn.textContent = '📷 Start Camera';
    snapBtn.style.display = 'none';
    overlay.style.display = 'flex';
    scanLine.style.display = 'none';
    status.textContent = 'Camera stopped';
    document.getElementById('live-desc').textContent = 'Live OCR will appear here when camera is active';
    return;
  }

  try {
    status.textContent = 'Requesting camera access...';
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
    document.getElementById('camera-feed').srcObject = cameraStream;
    overlay.style.display = 'none';
    scanLine.style.display = 'block';
    btn.textContent = '⏹ Stop Camera';
    snapBtn.style.display = 'inline-flex';
    status.textContent = '🟢 Camera active';

    // Start live OCR every 3.5 seconds
    liveOcrInterval = setInterval(runLiveOCR, 3500);
  } catch (err) {
    status.textContent = '❌ Camera access denied: ' + err.message;
  }
}

function captureFrame() {
  const video = document.getElementById('camera-feed');
  const canvas = document.getElementById('camera-canvas');
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  canvas.getContext('2d').drawImage(video, 0, 0);
  return canvas.toDataURL('image/jpeg', 0.85);
}

async function runLiveOCR() {
  if (!cameraStream) return;
  const dataUrl = captureFrame();
  try {
    const res = await authFetch('/api/camera-ocr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: dataUrl })
    });
    if (!res.ok) return;
    const data = await res.json();
    const liveText = document.getElementById('live-text');
    const liveDesc = document.getElementById('live-desc');
    liveText.textContent = data.text || '(no text detected in frame)';
    liveDesc.textContent = `Live OCR — Confidence: ${(data.confidence || 0).toFixed(1)}%`;
  } catch (e) {
    // Silently fail live OCR
  }
}

async function takeSnapshot() {
  if (!cameraStream) return;
  const dataUrl = captureFrame();
  const card = document.getElementById('camera-result-card');
  const textEl = document.getElementById('camera-text');
  const confEl = document.getElementById('camera-confidence');

  card.style.display = 'block';
  textEl.textContent = 'Processing snapshot...';

  try {
    const res = await authFetch('/api/camera-ocr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: dataUrl })
    });
    if (!res.ok) throw new Error('OCR failed');
    const data = await res.json();
    textEl.textContent = data.text || '(no text detected)';
    confEl.textContent = `${(data.confidence || 0).toFixed(1)}% confidence`;
  } catch (err) {
    textEl.textContent = '❌ ' + err.message;
  }
}

// =====================
// HISTORY
// =====================
async function loadHistory() {
  const list = document.getElementById('history-list');
  list.innerHTML = '<p class="muted">Loading...</p>';
  try {
    const res = await authFetch('/api/history');
    const docs = await res.json();
    if (!docs.length) {
      list.innerHTML = '<p class="muted">No processing history yet.</p>';
      return;
    }
    list.innerHTML = docs.slice(0, 30).map(d => `
      <div class="history-item">
        <div class="history-icon">📄</div>
        <div class="history-info">
          <div class="fname">${d.filename}</div>
          <div class="fmeta">Language: ${d.language || '–'} · ${new Date(d.created_at).toLocaleString()}</div>
        </div>
        <div class="history-conf">${(d.confidence || 0).toFixed(1)}%</div>
        <button class="btn btn-sm" onclick="exportHistoryDoc(${d.id})">↓ TXT</button>
      </div>
    `).join('');
  } catch (e) {
    list.innerHTML = '<p class="muted">Failed to load history.</p>';
  }
}

function exportHistoryDoc(id) {
  window.open(`/api/export/${id}/txt`, '_blank');
}

// =====================
// PROGRESS BAR
// =====================
function showProgress(visible) {
  const bar = document.getElementById('progress-bar');
  bar.style.display = visible ? 'block' : 'none';
  if (!visible) document.getElementById('progress-fill').style.width = '0';
}

function animateProgress(from, to, duration) {
  const fill = document.getElementById('progress-fill');
  const start = performance.now();
  function step(now) {
    const ratio = Math.min((now - start) / duration, 1);
    fill.style.width = (from + (to - from) * ratio) + '%';
    if (ratio < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// =====================
// COPY HELPERS
// =====================
function copyText() {
  const text = document.getElementById('corrected-text').textContent;
  navigator.clipboard.writeText(text).then(() => showToast('Copied!'));
}
function copyTranslation() {
  const text = document.getElementById('translated-text').textContent;
  navigator.clipboard.writeText(text).then(() => showToast('Copied!'));
}
function copyCameraText() {
  const text = document.getElementById('camera-text').textContent;
  navigator.clipboard.writeText(text).then(() => showToast('Copied!'));
}
function showToast(msg) {
  const t = document.createElement('div');
  t.textContent = msg;
  Object.assign(t.style, {
    position: 'fixed', bottom: '2rem', right: '2rem',
    background: 'linear-gradient(135deg, #7c6ef5, #e86bdf)',
    color: '#fff', padding: '0.6rem 1.2rem', borderRadius: '8px',
    fontWeight: '600', fontSize: '0.85rem', zIndex: '9999',
    animation: 'fadeIn 0.3s ease', boxShadow: '0 4px 20px rgba(0,0,0,0.4)'
  });
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2200);
}

// =====================
// FORM AUTO-FILL
// =====================
function renderAutoFillForm(info) {
  if (!info) return;

  const fFill = info.form_fill || {};
  
  // Set direct single-value extracts
  document.getElementById('fill-name').value = fFill.name || '';
  document.getElementById('fill-dob').value = fFill.dob || '';
  document.getElementById('fill-gender').value = fFill.gender || '';
  document.getElementById('fill-address').value = fFill.address || '';

  // For arrays, pick the first item
  const emails = info.emails || [];
  document.getElementById('fill-email').value = emails.length > 0 ? emails[0] : '';

  const phones = info.phone_numbers || [];
  document.getElementById('fill-phone').value = phones.length > 0 ? phones[0] : '';
}

function copyFormData() {
  const data = {
    name: document.getElementById('fill-name').value,
    dob: document.getElementById('fill-dob').value,
    gender: document.getElementById('fill-gender').value,
    phone: document.getElementById('fill-phone').value,
    email: document.getElementById('fill-email').value,
    address: document.getElementById('fill-address').value
  };
  
  const jsonStr = JSON.stringify(data, null, 2);
  navigator.clipboard.writeText(jsonStr).then(() => showToast('Form JSON Copied!'));
}

// =====================
// WORKFLOW BUILDER
// =====================
async function executeWorkflow() {
    const file = document.getElementById('wf-file-input').files[0];
    if (!file) { alert('Please select a trigger file.'); return; }

    const loading = document.getElementById('wf-loading');
    const resultBox = document.getElementById('wf-result');
    const outputText = document.getElementById('wf-output-text');
    
    loading.style.display = 'block';
    resultBox.style.display = 'none';
    
    const steps = [];
    const a1 = document.getElementById('wf-action-1').value;
    const a2 = document.getElementById('wf-action-2').value;
    
    if (a1 && a1 !== 'none') steps.push(a1);
    if (a2 && a2 !== 'none') steps.push(a2);

    const fd = new FormData();
    fd.append('file', file);
    fd.append('steps_json', JSON.stringify(steps));

    try {
        const res = await authFetch('/api/workflow/execute', {
            method: 'POST',
            body: fd
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail);
        }
        const data = await res.json();
        
        loading.style.display = 'none';
        resultBox.style.display = 'flex';
        outputText.textContent = JSON.stringify(data, null, 2);
        
        fetchUsage(); // update token limits

    } catch (e) {
        loading.style.display = 'none';
        alert("Workflow Error: " + e.message);
    }
}

function copyWfData() {
    const t = document.getElementById('wf-output-text').textContent;
    navigator.clipboard.writeText(t).then(()=>showToast('Pipeline Result Copied'));
}

