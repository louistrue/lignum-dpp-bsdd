/**
 * UI entry point — wizard-style flow: Upload → Review → Enrich → Export.
 */

import { processIfc, analyzeModel, type Assignment } from './enrichment';
import { parseIfcStep } from './step-parser';

const $ = <T extends HTMLElement>(sel: string) => document.querySelector<T>(sel)!;

let currentFile: File | null = null;
let enrichedBlob: Blob | null = null;
let lastEnrichedText: string | null = null;

// Sections
const stepUpload = $('#step-upload');
const stepReview = $('#step-review');
const stepProcess = $('#step-process');
const stepResults = $('#step-results');

// Elements
const dropzone = $('#dropzone');
const fileInput = $<HTMLInputElement>('#file-input');
const fileName = $('#file-name');
const fileSize = $('#file-size');
const clearBtn = $('#clear-file');
const matchTable = $('#match-table');
const enrichBtn = $('#enrich-btn');
const logPre = $('#log');
const logCopy = $('#log-copy');
const progressFill = $('#progress-fill');
const statsGrid = $('#stats-grid');
const resultsSubtitle = $('#results-subtitle');
const resultsMatchTable = $('#results-match-table');
const downloadBtn = $('#download-btn');
const emissionsBtn = $('#emissions-btn');
const restartBtn = $('#restart-btn');

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// --- Step management ---

function setStep(step: 1 | 2 | 3 | 4) {
  const steps = document.querySelectorAll('.step');
  const lines = document.querySelectorAll('.step-line');

  steps.forEach((el, i) => {
    const s = i + 1;
    el.classList.toggle('active', s === step);
    el.classList.toggle('done', s < step);
  });
  lines.forEach((el, i) => {
    el.classList.toggle('done', i + 1 < step);
  });

  stepUpload.hidden = step !== 1;
  stepReview.hidden = step !== 2;
  stepProcess.hidden = step !== 3;
  stepResults.hidden = step !== 4;
}

// --- Render assignments ---

function renderAssignments(assignments: Assignment[]): string {
  if (assignments.length === 0) return '<p style="color:#999;font-size:14px;">No matching elements found in this IFC file.</p>';

  let html = '<table class="match-table"><thead><tr>';
  html += '<th>DPP Product</th><th>Elements</th><th>Match</th>';
  html += '</tr></thead><tbody>';

  for (const a of assignments) {
    const badge = a.matchReason.includes('random') ? 'badge-random' :
      `badge-${a.component}`;
    const elemNames = a.elements.slice(0, 5).map(e => e.name || e.type).join(', ');
    const more = a.elements.length > 5 ? `, +${a.elements.length - 5} more` : '';

    html += '<tr>';
    html += `<td><span class="badge badge-${a.component}">${a.config.label}</span></td>`;
    html += `<td><span class="elem-list">${elemNames}${more}</span> <span class="elem-count">(${a.elements.length})</span></td>`;
    html += `<td><span class="badge ${badge}">${a.matchReason}</span></td>`;
    html += '</tr>';
  }

  html += '</tbody></table>';
  return html;
}

// --- File handling ---

async function handleFile(file: File) {
  currentFile = file;
  enrichedBlob = null;

  fileName.textContent = file.name;
  fileSize.textContent = formatSize(file.size);
  logPre.textContent = '';

  // Parse and show assignments preview
  matchTable.innerHTML = '<p style="color:#999;">Analyzing IFC model&hellip;</p>';
  setStep(2);

  try {
    const text = await file.text();
    const model = parseIfcStep(text);
    const assignments = analyzeModel(model, () => {});
    matchTable.innerHTML = renderAssignments(assignments);
  } catch (err) {
    matchTable.innerHTML = `<p style="color:#b91c1c;">Error parsing IFC: ${err}</p>`;
  }
}

// Drag & drop
dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('dragover');
});
dropzone.addEventListener('dragleave', () => {
  dropzone.classList.remove('dragover');
});
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  const file = e.dataTransfer?.files[0];
  if (file && file.name.toLowerCase().endsWith('.ifc')) {
    handleFile(file);
  }
});
dropzone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
  const file = fileInput.files?.[0];
  if (file) handleFile(file);
});

clearBtn.addEventListener('click', () => {
  currentFile = null;
  enrichedBlob = null;
  fileInput.value = '';
  setStep(1);
});

// --- Enrichment ---

enrichBtn.addEventListener('click', async () => {
  if (!currentFile) return;

  setStep(3);
  progressFill.classList.add('indeterminate');
  logPre.textContent = '';

  const log = (msg: string) => {
    logPre.textContent += msg + '\n';
    logPre.scrollTop = logPre.scrollHeight;
  };

  try {
    const text = await currentFile.text();
    await new Promise<void>((resolve) => {
      setTimeout(() => {
        try {
          const { enrichedText, assignments } = processIfc(text, log);
          lastEnrichedText = enrichedText;
          enrichedBlob = new Blob([enrichedText], { type: 'application/octet-stream' });

          // Calculate stats
          let totalElements = 0;
          let totalProps = 0;
          let totalDocs = 0;
          const productSet = new Set<string>();

          for (const a of assignments) {
            totalElements += a.elements.length;
            totalProps += a.config.properties.length;
            totalDocs += a.config.documents.length;
            productSet.add(a.component);
          }

          // Show results
          progressFill.classList.remove('indeterminate');
          progressFill.style.width = '100%';

          resultsSubtitle.textContent =
            `${totalElements} elements enriched with ${productSet.size} DPP product${productSet.size > 1 ? 's' : ''} — ${formatSize(enrichedBlob.size)}`;

          statsGrid.innerHTML = `
            <div class="stat-card"><div class="stat-value">${totalElements}</div><div class="stat-label">Elements</div></div>
            <div class="stat-card"><div class="stat-value">${productSet.size}</div><div class="stat-label">Products</div></div>
            <div class="stat-card"><div class="stat-value">${totalProps}</div><div class="stat-label">Properties</div></div>
            <div class="stat-card"><div class="stat-value">${productSet.size}</div><div class="stat-label">Classifications</div></div>
            <div class="stat-card"><div class="stat-value">${totalDocs}</div><div class="stat-label">Documents</div></div>
            <div class="stat-card"><div class="stat-value">${productSet.size}</div><div class="stat-label">GS1 Links</div></div>
          `;

          resultsMatchTable.innerHTML = renderAssignments(assignments);
          logCopy.textContent = logPre.textContent;

          // Transition to results after a brief moment
          setTimeout(() => setStep(4), 400);
        } catch (err) {
          log(`\nERROR: ${err}`);
          progressFill.classList.remove('indeterminate');
          progressFill.style.width = '100%';
          progressFill.style.background = '#b91c1c';
        }
        resolve();
      }, 50);
    });
  } catch (err) {
    logPre.textContent += `\nERROR: ${err}\n`;
  }
});

// --- Download ---

downloadBtn.addEventListener('click', () => {
  if (!enrichedBlob || !currentFile) return;

  const baseName = currentFile.name.replace(/\.ifc$/i, '');
  const url = URL.createObjectURL(enrichedBlob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${baseName}_enriched.ifc`;
  a.click();
  URL.revokeObjectURL(url);
});

// --- Emissions handoff ---

emissionsBtn.addEventListener('click', () => {
  if (!lastEnrichedText && !currentFile) return;
  try {
    const text = lastEnrichedText || '';
    sessionStorage.setItem('lca-ifc-text', text);
    sessionStorage.setItem('lca-ifc-name', currentFile?.name || 'enriched.ifc');
  } catch {
    // sessionStorage full — user will need to upload manually
  }
  window.location.href = '/emissions/';
});

// --- Restart ---

restartBtn.addEventListener('click', () => {
  currentFile = null;
  enrichedBlob = null;
  lastEnrichedText = null;
  fileInput.value = '';
  logPre.textContent = '';
  progressFill.style.width = '0%';
  progressFill.style.background = '';
  progressFill.classList.remove('indeterminate');
  setStep(1);
});
