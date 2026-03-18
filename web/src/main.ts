/**
 * UI entry point — handles file upload, enrichment trigger, and download.
 */

import { processIfc, analyzeModel, type Assignment } from './enrichment';
import { parseIfcStep } from './step-parser';

const $ = <T extends HTMLElement>(sel: string) => document.querySelector<T>(sel)!;

let currentFile: File | null = null;
let enrichedBlob: Blob | null = null;

// --- File upload ---

const dropzone = $('#dropzone');
const fileInput = $<HTMLInputElement>('#file-input');
const fileInfo = $('#file-info');
const fileName = $('#file-name');
const fileSize = $('#file-size');
const clearBtn = $('#clear-file');
const matchSection = $('#match-section');
const matchTable = $('#match-table');
const enrichBtn = $('#enrich-btn');
const logSection = $('#log-section');
const logPre = $('#log');
const downloadSection = $('#download-section');
const downloadBtn = $('#download-btn');

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderAssignments(assignments: Assignment[]): string {
  if (assignments.length === 0) return '<p>No elements found in this IFC file.</p>';

  let html = '<table class="match-table"><thead><tr>';
  html += '<th>DPP</th><th>Elements</th><th>Match</th>';
  html += '</tr></thead><tbody>';

  for (const a of assignments) {
    const badge = a.matchReason.includes('random') ? 'badge-random' :
      `badge-${a.component}`;
    const elemNames = a.elements.slice(0, 5).map(e => e.name || e.type).join(', ');
    const more = a.elements.length > 5 ? ` +${a.elements.length - 5} more` : '';

    html += '<tr>';
    html += `<td><span class="badge badge-${a.component}">${a.config.label}</span></td>`;
    html += `<td>${elemNames}${more} <em>(${a.elements.length})</em></td>`;
    html += `<td><span class="badge ${badge}">${a.matchReason}</span></td>`;
    html += '</tr>';
  }

  html += '</tbody></table>';
  return html;
}

async function handleFile(file: File) {
  currentFile = file;
  enrichedBlob = null;

  fileName.textContent = file.name;
  fileSize.textContent = formatSize(file.size);
  fileInfo.hidden = false;
  downloadSection.hidden = true;
  logSection.hidden = true;
  logPre.textContent = '';

  // Parse and show assignments preview
  matchSection.hidden = false;
  matchTable.innerHTML = '<p>Analyzing...</p>';

  try {
    const text = await file.text();
    const model = parseIfcStep(text);
    const assignments = analyzeModel(model, () => {}); // silent analysis
    matchTable.innerHTML = renderAssignments(assignments);
    enrichBtn.hidden = false;
  } catch (err) {
    matchTable.innerHTML = `<p style="color:red">Error parsing IFC: ${err}</p>`;
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

clearBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  currentFile = null;
  enrichedBlob = null;
  fileInfo.hidden = true;
  matchSection.hidden = true;
  downloadSection.hidden = true;
  logSection.hidden = true;
  fileInput.value = '';
});

// --- Enrichment ---

enrichBtn.addEventListener('click', async () => {
  if (!currentFile) return;

  enrichBtn.setAttribute('disabled', '');
  enrichBtn.textContent = 'Enriching...';
  logSection.hidden = false;
  logPre.textContent = '';
  downloadSection.hidden = true;

  const log = (msg: string) => {
    logPre.textContent += msg + '\n';
    logPre.scrollTop = logPre.scrollHeight;
  };

  try {
    const text = await currentFile.text();
    // Run in a setTimeout to allow UI to update
    await new Promise<void>((resolve) => {
      setTimeout(() => {
        try {
          const { enrichedText, assignments } = processIfc(text, log);
          enrichedBlob = new Blob([enrichedText], { type: 'application/octet-stream' });

          // Update assignment table with final data
          matchTable.innerHTML = renderAssignments(assignments);

          downloadSection.hidden = false;
          log(`\nOutput size: ${formatSize(enrichedBlob.size)}`);
        } catch (err) {
          log(`\nERROR: ${err}`);
        }
        resolve();
      }, 50);
    });
  } catch (err) {
    logPre.textContent += `\nERROR: ${err}\n`;
  }

  enrichBtn.removeAttribute('disabled');
  enrichBtn.textContent = 'Enrich IFC';
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
