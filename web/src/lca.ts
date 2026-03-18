/**
 * LCA Emissions Calculator - pure calculation module, no DOM dependencies.
 * Computes environmental impacts from IFC element quantities and DPP/EPD data.
 */

import type { ParsedModel, IfcElement } from './step-parser';
import type { Assignment } from './enrichment';
import { LCA_COMPONENTS, type LifeCycleModule, type LcaComponentConfig } from './config';

export interface ElementLcaResult {
  element: IfcElement;
  component: string;
  volume: number | null;
  length: number | null;
  mass: number | null;
  gwp: number;
  hasQuantityData: boolean;
}

export interface ComponentLcaResult {
  component: string;
  label: string;
  shortLabel: string;
  elementCount: number;
  elementsWithData: number;
  elementsWithoutData: number;
  totalVolume: number;
  totalLength: number;
  totalMass: number;
  /** indicator name → summed value across selected modules */
  indicators: Record<string, number>;
  /** indicator name → module → value */
  indicatorsByModule: Record<string, Partial<Record<LifeCycleModule, number>>>;
}

export interface LcaResults {
  selectedModules: LifeCycleModule[];
  components: ComponentLcaResult[];
  totals: {
    elementCount: number;
    elementsWithData: number;
    elementsWithoutData: number;
    totalVolume: number;
    totalMass: number;
    indicators: Record<string, number>;
    indicatorsByModule: Record<string, Partial<Record<LifeCycleModule, number>>>;
  };
  /** All unique indicator names found */
  indicatorNames: string[];
  /** Indicator display info */
  indicatorInfo: Record<string, { displayName: string; unit: string }>;
}

function getQuantityForComponent(
  model: ParsedModel,
  elementId: number,
  config: LcaComponentConfig,
): { quantity: number | null; mass: number | null; volume: number | null; length: number | null } {
  const eq = model.elementQuantities.get(elementId);
  if (!eq) return { quantity: null, mass: null, volume: null, length: null };

  if (config.referenceUnit === 'm') {
    // Pipe: use length
    const len = eq.length;
    if (len === null) return { quantity: null, mass: null, volume: null, length: null };
    const mass = config.linearDensity ? len * config.linearDensity : null;
    return { quantity: len, mass, volume: eq.grossVolume, length: len };
  }

  // Volume-based (insulation, timber)
  const vol = eq.grossVolume ?? eq.netVolume;
  if (vol === null) return { quantity: null, mass: null, volume: null, length: eq.length };
  const mass = vol * config.density;
  return { quantity: vol, mass, volume: vol, length: eq.length };
}

export function calculateEmissions(
  model: ParsedModel,
  assignments: Assignment[],
  selectedModules: LifeCycleModule[],
): LcaResults {
  const componentResults: ComponentLcaResult[] = [];
  const allIndicatorNames = new Set<string>();
  const indicatorInfo: Record<string, { displayName: string; unit: string }> = {};

  for (const assignment of assignments) {
    const { component, elements } = assignment;
    const lcaConfig = LCA_COMPONENTS[component];
    if (!lcaConfig) continue;

    // Collect indicator info
    for (const ind of lcaConfig.indicators) {
      allIndicatorNames.add(ind.indicator);
      indicatorInfo[ind.indicator] = { displayName: ind.displayName, unit: ind.unit };
    }

    const compResult: ComponentLcaResult = {
      component,
      label: lcaConfig.label,
      shortLabel: lcaConfig.shortLabel,
      elementCount: elements.length,
      elementsWithData: 0,
      elementsWithoutData: 0,
      totalVolume: 0,
      totalLength: 0,
      totalMass: 0,
      indicators: {},
      indicatorsByModule: {},
    };

    for (const elem of elements) {
      const { quantity, mass, volume, length } = getQuantityForComponent(model, elem.id, lcaConfig);

      if (quantity === null) {
        compResult.elementsWithoutData++;
        continue;
      }

      compResult.elementsWithData++;
      if (volume !== null) compResult.totalVolume += volume;
      if (length !== null) compResult.totalLength += length;
      if (mass !== null) compResult.totalMass += mass;

      // Calculate emissions for each indicator and selected module
      for (const ind of lcaConfig.indicators) {
        if (!compResult.indicatorsByModule[ind.indicator]) {
          compResult.indicatorsByModule[ind.indicator] = {};
        }

        for (const mod of selectedModules) {
          const epdValue = ind.modules[mod];
          if (epdValue === undefined) continue;

          const emission = quantity * epdValue;

          // Per-module
          const byMod = compResult.indicatorsByModule[ind.indicator]!;
          byMod[mod] = (byMod[mod] ?? 0) + emission;

          // Total
          compResult.indicators[ind.indicator] = (compResult.indicators[ind.indicator] ?? 0) + emission;
        }
      }
    }

    componentResults.push(compResult);
  }

  // Compute totals
  const totals = {
    elementCount: 0,
    elementsWithData: 0,
    elementsWithoutData: 0,
    totalVolume: 0,
    totalMass: 0,
    indicators: {} as Record<string, number>,
    indicatorsByModule: {} as Record<string, Partial<Record<LifeCycleModule, number>>>,
  };

  for (const cr of componentResults) {
    totals.elementCount += cr.elementCount;
    totals.elementsWithData += cr.elementsWithData;
    totals.elementsWithoutData += cr.elementsWithoutData;
    totals.totalVolume += cr.totalVolume;
    totals.totalMass += cr.totalMass;

    for (const [ind, val] of Object.entries(cr.indicators)) {
      totals.indicators[ind] = (totals.indicators[ind] ?? 0) + val;
    }
    for (const [ind, byMod] of Object.entries(cr.indicatorsByModule)) {
      if (!totals.indicatorsByModule[ind]) totals.indicatorsByModule[ind] = {};
      for (const [mod, val] of Object.entries(byMod)) {
        const m = mod as LifeCycleModule;
        totals.indicatorsByModule[ind]![m] = (totals.indicatorsByModule[ind]![m] ?? 0) + (val ?? 0);
      }
    }
  }

  return {
    selectedModules,
    components: componentResults,
    totals,
    indicatorNames: [...allIndicatorNames],
    indicatorInfo,
  };
}

/** Format a number for display (handles very small and very large values) */
export function formatValue(val: number, decimals = 2): string {
  if (val === 0) return '0';
  const abs = Math.abs(val);
  if (abs >= 1000) return val.toLocaleString('en-US', { maximumFractionDigits: 0 });
  if (abs >= 1) return val.toFixed(decimals);
  if (abs >= 0.01) return val.toFixed(3);
  return val.toExponential(2);
}

/** Generate CSV export from results */
export function exportCsv(results: LcaResults): string {
  const lines: string[] = [];

  // Header
  const indCols = results.indicatorNames.map(n => {
    const info = results.indicatorInfo[n];
    return `${info?.displayName ?? n} (${info?.unit ?? ''})`;
  });
  lines.push(['Material', 'Elements', 'With Data', 'Volume (m3)', 'Mass (kg)', ...indCols].join(','));

  // Component rows
  for (const cr of results.components) {
    const vals = results.indicatorNames.map(n => formatValue(cr.indicators[n] ?? 0, 4));
    lines.push([
      `"${cr.label}"`,
      cr.elementCount,
      cr.elementsWithData,
      cr.totalVolume.toFixed(4),
      cr.totalMass.toFixed(1),
      ...vals,
    ].join(','));
  }

  // Totals
  const totalVals = results.indicatorNames.map(n => formatValue(results.totals.indicators[n] ?? 0, 4));
  lines.push([
    'TOTAL',
    results.totals.elementCount,
    results.totals.elementsWithData,
    results.totals.totalVolume.toFixed(4),
    results.totals.totalMass.toFixed(1),
    ...totalVals,
  ].join(','));

  // Module breakdown
  lines.push('');
  lines.push('Module Breakdown');
  lines.push(['Module', ...results.indicatorNames.map(n => `${results.indicatorInfo[n]?.displayName ?? n} (${results.indicatorInfo[n]?.unit ?? ''})`)].join(','));
  for (const mod of results.selectedModules) {
    const vals = results.indicatorNames.map(n =>
      formatValue(results.totals.indicatorsByModule[n]?.[mod] ?? 0, 4)
    );
    lines.push([mod, ...vals].join(','));
  }

  return lines.join('\n');
}
