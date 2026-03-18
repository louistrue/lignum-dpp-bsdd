/**
 * Emissions Calculator UI — wizard: Upload → Configure → Results.
 */

import { analyzeModel, type Assignment } from './enrichment';
import { parseIfcStep, type ParsedModel } from './step-parser';
import { calculateEmissions, formatValue, exportCsv, type LcaResults } from './lca';
import {
  ALL_MODULES, MODULE_LABELS, LCA_COMPONENTS,
  type LifeCycleModule,
} from './config';
import { consumeHandoff } from './ifc-handoff';

const $ = <T extends HTMLElement>(sel: string) => document.querySelector<T>(sel)!;

let currentFileName = '';
let currentFileSize = 0;
let parsedModel: ParsedModel | null = null;
let assignments: Assignment[] | null = null;
let lastResults: LcaResults | null = null;
// EN 15978 / EU Level(s) normative modules for whole-building LCA
const selectedModules = new Set<LifeCycleModule>(['A1-A3', 'C1', 'C2', 'C3', 'C4', 'D']);

// Sections
const stepUpload = $('#step-upload');
const stepConfigure = $('#step-configure');
const stepResults = $('#step-results');

// Elements
const dropzone = $('#dropzone');
const fileInput = $<HTMLInputElement>('#file-input');
const fileNameEl = $('#file-name');
const fileSizeEl = $('#file-size');
const clearBtn = $('#clear-file');
const moduleGrid = $('#module-grid');
const elementSummary = $('#element-summary');
const calculateBtn = $('#calculate-btn');
const statsGrid = $('#stats-grid');
const resultsSubtitle = $('#results-subtitle');
const carbonCallout = $('#carbon-callout');
const noDataWarning = $('#no-data-warning');
const indicatorBars = $('#indicator-bars');
const breakdownTable = $('#breakdown-table');
const moduleTable = $('#module-table');
const exportCsvBtn = $('#export-csv-btn');
const exportJsonBtn = $('#export-json-btn');
const restartBtn = $('#restart-btn');

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// --- Step management ---

function setStep(step: 1 | 2 | 3) {
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
  stepConfigure.hidden = step !== 2;
  stepResults.hidden = step !== 3;
}

// --- Module selection ---

function renderModuleGrid() {
  let html = '';
  for (const mod of ALL_MODULES) {
    const checked = selectedModules.has(mod);
    html += `<label class="module-checkbox${checked ? ' checked' : ''}" data-module="${mod}">
      <input type="checkbox" ${checked ? 'checked' : ''} />
      <div>
        <div class="module-name">${mod}</div>
        <div class="module-desc">${MODULE_LABELS[mod]}</div>
      </div>
    </label>`;
  }
  moduleGrid.innerHTML = html;

  moduleGrid.querySelectorAll('.module-checkbox').forEach(el => {
    el.addEventListener('click', (e) => {
      const target = e.currentTarget as HTMLElement;
      const mod = target.dataset.module as LifeCycleModule;
      const cb = target.querySelector('input') as HTMLInputElement;

      if (mod === 'A1-A3') {
        // A1-A3 always selected
        cb.checked = true;
        return;
      }

      cb.checked = !cb.checked;
      if (cb.checked) {
        selectedModules.add(mod);
        target.classList.add('checked');
      } else {
        selectedModules.delete(mod);
        target.classList.remove('checked');
      }
    });
  });
}

// --- Element summary ---

function renderElementSummary() {
  if (!parsedModel || !assignments) return;

  let totalElements = 0;
  let withData = 0;
  let withoutData = 0;

  for (const a of assignments) {
    for (const elem of a.elements) {
      totalElements++;
      const lcaConfig = LCA_COMPONENTS[a.component];
      if (!lcaConfig) { withoutData++; continue; }

      const eq = parsedModel.elementQuantities.get(elem.id);
      if (!eq) { withoutData++; continue; }

      if (lcaConfig.referenceUnit === 'm') {
        if (eq.length !== null) withData++;
        else withoutData++;
      } else {
        if (eq.grossVolume !== null || eq.netVolume !== null) withData++;
        else withoutData++;
      }
    }
  }

  let html = `<strong>${totalElements}</strong> elements matched to <strong>${assignments.length}</strong> DPP product${assignments.length > 1 ? 's' : ''}`;
  html += `<br><strong>${withData}</strong> elements have quantity data (volume/length)`;
  if (withoutData > 0) {
    html += `<br><span style="color:#92400e;"><strong>${withoutData}</strong> elements missing quantity data — will be excluded</span>`;
  }

  elementSummary.innerHTML = html;
}

// --- File handling ---

async function processFile(text: string, name: string, size: number) {
  currentFileName = name;
  currentFileSize = size;

  try {
    parsedModel = parseIfcStep(text);
    assignments = analyzeModel(parsedModel, () => {});
  } catch (err) {
    elementSummary.innerHTML = `<span style="color:#b91c1c;">Error parsing IFC: ${err}</span>`;
    return;
  }

  fileNameEl.textContent = name;
  fileSizeEl.textContent = formatSize(size);
  renderModuleGrid();
  renderElementSummary();
  setStep(2);
}

async function handleFile(file: File) {
  const text = await file.text();
  await processFile(text, file.name, file.size);
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
  if (file && file.name.toLowerCase().endsWith('.ifc')) handleFile(file);
});
dropzone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', () => {
  const file = fileInput.files?.[0];
  if (file) handleFile(file);
});

clearBtn.addEventListener('click', () => {
  parsedModel = null;
  assignments = null;
  fileInput.value = '';
  setStep(1);
});

// --- Check for data from enrich flow ---

(async function checkHandoff() {
  const payload = await consumeHandoff();
  if (payload) {
    const fromMsg = document.getElementById('from-enrich-msg');
    if (fromMsg) fromMsg.hidden = false;
    processFile(payload.text, payload.name, new Blob([payload.text]).size);
  }
})();

// --- Calculate ---

const COMPONENT_COLORS: Record<string, string> = {
  insulation: '#ea580c',
  timber: '#16a34a',
  pipe: '#2563eb',
};

const COMPONENT_BAR_CLASSES: Record<string, string> = {
  insulation: 'bar-insulation',
  timber: 'bar-timber',
  pipe: 'bar-pipe',
};

function renderResults(results: LcaResults) {
  lastResults = results;
  const { totals, components, indicatorNames, indicatorInfo } = results;

  // Subtitle
  resultsSubtitle.textContent =
    `${totals.elementsWithData} elements analyzed across ${components.length} material${components.length > 1 ? 's' : ''} — modules: ${results.selectedModules.join(', ')}`;

  // Stat cards
  const gwp = totals.indicators['GWP-total'] ?? 0;
  const gwpClass = gwp < 0 ? 'negative' : gwp > 0 ? 'positive' : '';
  statsGrid.innerHTML = `
    <div class="stat-card">
      <div class="stat-value ${gwpClass}">${formatValue(gwp)}</div>
      <div class="stat-label">kg CO2e (GWP)</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${totals.elementsWithData}</div>
      <div class="stat-label">Elements</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${formatValue(totals.totalVolume, 3)}</div>
      <div class="stat-label">Volume (m3)</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${formatValue(totals.totalMass, 0)}</div>
      <div class="stat-label">Mass (kg)</div>
    </div>
  `;

  // Carbon callout (if timber has negative GWP)
  const timberComp = components.find(c => c.component === 'timber');
  const timberGwp = timberComp?.indicators['GWP-total'] ?? 0;
  if (timberGwp < 0) {
    carbonCallout.innerHTML = `
      <div class="carbon-callout">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><path d="M12 22c4-4 8-7.5 8-12a8 8 0 1 0-16 0c0 4.5 4 8 8 12z"/><path d="M12 10v4"/><path d="M10 12h4"/></svg>
        <span>Timber elements store <strong>${formatValue(Math.abs(timberGwp))}</strong> kg CO2e of biogenic carbon (production phase A1-A3)</span>
      </div>`;
  } else {
    carbonCallout.innerHTML = '';
  }

  // Missing data warning
  if (totals.elementsWithoutData > 0) {
    noDataWarning.innerHTML = `
      <div class="no-data-warning">
        ${totals.elementsWithoutData} element${totals.elementsWithoutData > 1 ? 's' : ''} excluded — no volume/length quantity data found in the IFC model.
      </div>`;
  } else {
    noDataWarning.innerHTML = '';
  }

  // Indicator bars
  renderIndicatorBars(results);

  // Material breakdown table
  renderBreakdownTable(results);

  // Module breakdown table
  if (results.selectedModules.length > 1) {
    renderModuleTable(results);
    document.getElementById('module-breakdown')!.hidden = false;
  } else {
    document.getElementById('module-breakdown')!.hidden = true;
  }
}

function renderIndicatorBars(results: LcaResults) {
  const { components, indicatorNames, indicatorInfo, totals } = results;
  let html = '<h3 class="results-section-title">Environmental Indicators</h3>';

  for (const indName of indicatorNames) {
    const info = indicatorInfo[indName];
    const total = totals.indicators[indName] ?? 0;

    // Build segments
    const positiveSum = components.reduce((sum, c) => {
      const v = c.indicators[indName] ?? 0;
      return sum + (v > 0 ? v : 0);
    }, 0);

    html += `<div class="indicator-bar-row">`;
    html += `<div class="indicator-bar-header">`;
    html += `<span class="indicator-bar-name">${info?.displayName ?? indName}</span>`;
    html += `<span class="indicator-bar-value ${total < 0 ? 'neg' : ''}">${formatValue(total)}<span class="indicator-bar-unit">${info?.unit ?? ''}</span></span>`;
    html += `</div>`;
    html += `<div class="indicator-bar-track">`;

    if (positiveSum > 0) {
      for (const comp of components) {
        const val = comp.indicators[indName] ?? 0;
        if (val <= 0) continue;
        const pct = (val / positiveSum) * 100;
        const cls = COMPONENT_BAR_CLASSES[comp.component] || 'bar-insulation';
        const label = pct > 12 ? comp.shortLabel : '';
        html += `<div class="indicator-bar-segment ${cls}" style="width:${pct.toFixed(1)}%;" title="${comp.shortLabel}: ${formatValue(val)} ${info?.unit ?? ''}">${label}</div>`;
      }
    }

    html += `</div>`;

    // Show negative values below the bar
    const negComps = components.filter(c => (c.indicators[indName] ?? 0) < 0);
    if (negComps.length > 0) {
      for (const nc of negComps) {
        const val = nc.indicators[indName]!;
        html += `<div style="font-size:11px;color:#16a34a;margin-top:2px;">&#x2212; ${nc.shortLabel}: ${formatValue(Math.abs(val))} ${info?.unit ?? ''} (carbon storage)</div>`;
      }
    }

    html += `</div>`;
  }

  indicatorBars.innerHTML = html;
}

function renderBreakdownTable(results: LcaResults) {
  const { components, indicatorNames, indicatorInfo, totals } = results;

  let html = '<table class="breakdown-table"><thead><tr>';
  html += '<th>Material</th><th class="num">Elements</th><th class="num">Volume (m3)</th><th class="num">Mass (kg)</th>';
  for (const ind of indicatorNames) {
    const info = indicatorInfo[ind];
    html += `<th class="num">${ind === 'GWP-total' ? 'GWP' : ind}<br><span style="font-weight:400;font-size:9px;">${info?.unit ?? ''}</span></th>`;
  }
  html += '</tr></thead><tbody>';

  for (const comp of components) {
    html += '<tr>';
    html += `<td><span class="badge badge-${comp.component}">${comp.shortLabel}</span></td>`;
    html += `<td class="num">${comp.elementsWithData}</td>`;
    html += `<td class="num">${formatValue(comp.totalVolume, 4)}</td>`;
    html += `<td class="num">${formatValue(comp.totalMass, 1)}</td>`;
    for (const ind of indicatorNames) {
      const val = comp.indicators[ind] ?? 0;
      const cls = val < 0 ? 'neg' : val > 0 ? 'pos' : '';
      html += `<td class="num ${cls}">${formatValue(val)}</td>`;
    }
    html += '</tr>';
  }

  // Total row
  html += '<tr class="total-row">';
  html += '<td>Total</td>';
  html += `<td class="num">${totals.elementsWithData}</td>`;
  html += `<td class="num">${formatValue(totals.totalVolume, 4)}</td>`;
  html += `<td class="num">${formatValue(totals.totalMass, 1)}</td>`;
  for (const ind of indicatorNames) {
    const val = totals.indicators[ind] ?? 0;
    const cls = val < 0 ? 'neg' : val > 0 ? 'pos' : '';
    html += `<td class="num ${cls}">${formatValue(val)}</td>`;
  }
  html += '</tr>';

  html += '</tbody></table>';
  breakdownTable.innerHTML = html;
}

function renderModuleTable(results: LcaResults) {
  const { selectedModules: mods, indicatorNames, indicatorInfo, totals } = results;

  let html = '<table class="breakdown-table"><thead><tr>';
  html += '<th>Module</th><th></th>';
  for (const ind of indicatorNames) {
    const info = indicatorInfo[ind];
    html += `<th class="num">${ind === 'GWP-total' ? 'GWP' : ind}<br><span style="font-weight:400;font-size:9px;">${info?.unit ?? ''}</span></th>`;
  }
  html += '</tr></thead><tbody>';

  for (const mod of mods) {
    html += '<tr>';
    html += `<td><strong>${mod}</strong></td>`;
    html += `<td style="font-size:11px;color:#888;">${MODULE_LABELS[mod]}</td>`;
    for (const ind of indicatorNames) {
      const val = totals.indicatorsByModule[ind]?.[mod] ?? 0;
      const cls = val < 0 ? 'neg' : val > 0 ? 'pos' : '';
      html += `<td class="num ${cls}">${formatValue(val)}</td>`;
    }
    html += '</tr>';
  }

  html += '</tbody></table>';
  moduleTable.innerHTML = html;
}

// --- Calculate button ---

calculateBtn.addEventListener('click', () => {
  if (!parsedModel || !assignments) return;

  const mods = [...selectedModules] as LifeCycleModule[];
  const results = calculateEmissions(parsedModel, assignments, mods);
  renderResults(results);
  setStep(3);
});

// --- Export ---

exportCsvBtn.addEventListener('click', () => {
  if (!lastResults) return;
  const csv = exportCsv(lastResults);
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentFileName.replace(/\.ifc$/i, '')}_emissions.csv`;
  a.click();
  URL.revokeObjectURL(url);
});

exportJsonBtn.addEventListener('click', () => {
  if (!lastResults) return;
  const json = JSON.stringify(lastResults, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentFileName.replace(/\.ifc$/i, '')}_emissions.json`;
  a.click();
  URL.revokeObjectURL(url);
});

// --- Restart ---

restartBtn.addEventListener('click', () => {
  parsedModel = null;
  assignments = null;
  lastResults = null;
  fileInput.value = '';
  selectedModules.clear();
  selectedModules.add('A1-A3');
  setStep(1);
});
