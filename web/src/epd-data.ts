/**
 * Single source of truth for EPD indicator data.
 * Imports DPP JSON-LD files and derives both IFC enrichment properties
 * and LCA calculation indicators from them — no duplicate values.
 */

import type { PropertyDef } from './config';
import type { EpdIndicatorValue } from './config';
import type { LifeCycleModule } from './config';

// Import JSON-LD source files (Vite jsonld-loader plugin handles .jsonld)
import insulationDpp from '../../api/data/dpp/dpp_knauf_acoustic_batt.jsonld';
import timberDpp from '../../api/data/dpp/dpp_schilliger_glulam.jsonld';
import pipeDpp from '../../api/data/dpp/dpp_pvc_sewage_pipe.jsonld';

// --- Static metadata per component (not in JSON-LD) ---

const COMPONENT_META: Record<string, { standard: string }> = {
  insulation: { standard: 'EN 15804+A2' },
  timber: { standard: 'EN 15804+A1' },
  pipe: { standard: 'EN 15804+A2' },
};

const DPP_FILES: Record<string, Record<string, unknown>> = {
  insulation: insulationDpp,
  timber: timberDpp,
  pipe: pipeDpp,
};

// --- Indicator display names ---

const DISPLAY_NAMES: Record<string, string> = {
  'GWP-total': 'Global Warming Potential',
  'AP': 'Acidification',
  'EP': 'Eutrophication',
  'EP-freshwater': 'Eutrophication (freshwater)',
  'EP-marine': 'Eutrophication (marine)',
  'EP-terrestrial': 'Eutrophication (terrestrial)',
  'ODP': 'Ozone Depletion',
  'POCP': 'Photochemical Ozone Creation',
  'ADPE': 'Abiotic Depletion (elements)',
  'ADPF': 'Abiotic Depletion (fossil)',
  'PENRT': 'Primary Energy (non-renewable)',
};

// --- bSDD property URI mapping ---

const BSDD_BASE = 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0';
const BSDD_URIS: Record<string, string> = {
  'GWP-total': `${BSDD_BASE}/prop/GWP_total`,
  'AP': `${BSDD_BASE}/prop/AP`,
  'EP': `${BSDD_BASE}/prop/EP`,
  'EP-freshwater': `${BSDD_BASE}/prop/EP_freshwater`,
  'EP-marine': `${BSDD_BASE}/prop/EP_marine`,
  'EP-terrestrial': `${BSDD_BASE}/prop/EP_terrestrial`,
  'ODP': `${BSDD_BASE}/prop/ODP`,
  'POCP': `${BSDD_BASE}/prop/POCP`,
  'ADPE': `${BSDD_BASE}/prop/ADPE`,
  'ADPF': `${BSDD_BASE}/prop/ADPF`,
  'PENRT': `${BSDD_BASE}/prop/PENRT`,
};

// Indicators used in LCA calculations (skip GWP sub-indicators like GWP-fossil)
const LCA_INDICATORS = new Set([
  'GWP-total', 'AP', 'EP', 'EP-freshwater', 'EP-marine', 'EP-terrestrial',
  'ODP', 'POCP', 'ADPE', 'ADPF', 'PENRT',
]);

// --- JSON-LD extraction helpers ---

interface JsonLdIndicator {
  indicator: string;
  module: string;
  value: number;
  unit: string;
}

function extractIndicators(dpp: Record<string, unknown>): JsonLdIndicator[] {
  const results: JsonLdIndicator[] = [];

  // Collections are at the root level (flat JSON-LD, not @graph)
  const collections = dpp['dpp:dataElementCollections'] as unknown[] | undefined;
  if (!Array.isArray(collections)) return [];

  for (const coll of collections) {
    const c = coll as Record<string, unknown>;
    const elements = c['dpp:elements'] as unknown[] | undefined;
    if (!Array.isArray(elements)) continue;

    for (const elem of elements) {
      const e = elem as Record<string, unknown>;
      const val = e['dpp:value'];
      if (!Array.isArray(val)) continue;
      // Check if this is an indicator array
      const first = val[0] as Record<string, unknown> | undefined;
      if (!first || !('indicator' in first)) continue;

      for (const item of val) {
        const i = item as JsonLdIndicator;
        if (i.indicator && i.module !== undefined && i.value !== undefined) {
          results.push(i);
        }
      }
    }
  }

  return results;
}

// --- Cache extracted data ---

const _cache = new Map<string, JsonLdIndicator[]>();

function getIndicatorsForComponent(key: string): JsonLdIndicator[] {
  if (_cache.has(key)) return _cache.get(key)!;
  const dpp = DPP_FILES[key];
  if (!dpp) return [];
  const indicators = extractIndicators(dpp);
  _cache.set(key, indicators);
  return indicators;
}

// --- Public API ---

/**
 * Get EPD properties for IFC enrichment (PropertyDef format).
 * Derives values directly from JSON-LD source files.
 */
export function getEpdProperties(componentKey: string): PropertyDef[] {
  const indicators = getIndicatorsForComponent(componentKey);
  const meta = COMPONENT_META[componentKey];
  if (!meta) return [];

  return indicators
    .filter(i => LCA_INDICATORS.has(i.indicator))
    .map(i => {
      const propName = i.indicator === 'GWP-total'
        ? `GWP_total_${i.module}`
        : `${i.indicator.replace(/-/g, '_')}_${i.module}`;

      return {
        name: propName,
        value: String(i.value),
        unit: i.unit,
        bsddPropertyUri: BSDD_URIS[i.indicator] ?? '',
        dictionaryUri: BSDD_BASE,
        standard: meta.standard,
        note: `${DISPLAY_NAMES[i.indicator] ?? i.indicator} ${i.module}`,
      };
    });
}

/**
 * Get EPD indicators for LCA calculations (EpdIndicatorValue format).
 * Groups flat JSON-LD entries by indicator, building module maps.
 */
export function getEpdIndicators(componentKey: string): EpdIndicatorValue[] {
  const indicators = getIndicatorsForComponent(componentKey);

  // Group by indicator name
  const grouped = new Map<string, { unit: string; modules: Partial<Record<LifeCycleModule, number>> }>();

  for (const i of indicators) {
    if (!LCA_INDICATORS.has(i.indicator)) continue;

    if (!grouped.has(i.indicator)) {
      grouped.set(i.indicator, { unit: i.unit, modules: {} });
    }
    const g = grouped.get(i.indicator)!;
    g.modules[i.module as LifeCycleModule] = i.value;
  }

  return Array.from(grouped.entries()).map(([indicator, data]) => ({
    indicator,
    displayName: DISPLAY_NAMES[indicator] ?? indicator,
    unit: data.unit,
    modules: data.modules,
  }));
}
