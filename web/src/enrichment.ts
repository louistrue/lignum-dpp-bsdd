/**
 * IFC Enrichment orchestrator — matches elements to DPP configs and generates
 * new STEP entities for property sets, classifications, documents, and GS1 IDs.
 */

import { parseIfcStep, type ParsedModel, type IfcElement } from './step-parser';
import { StepWriter, insertStepLines } from './step-writer';
import {
  COMPONENTS, IFC_TYPE_RULES, MATERIAL_KEYWORDS, COMPONENT_KEYS,
  type ComponentConfig,
} from './config';

export type LogFn = (msg: string) => void;

export interface Assignment {
  component: string;
  config: ComponentConfig;
  elements: IfcElement[];
  matchReason: string; // 'ifc-type' | 'material-keyword' | 'random'
}

/** Hash a string to a stable index for deterministic "random" assignment */
function hashToIndex(s: string, mod: number): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  }
  return ((h % mod) + mod) % mod;
}

/**
 * Phase 1: Analyze the model and create element → DPP assignments.
 *
 * Strategy:
 * 1. Try IFC type-based matching (demo model: Wall→insulation, Pipe→pipe, Column/Beam→timber)
 * 2. If an element has no type match, try material keyword matching
 * 3. If still no match, assign a DPP per unique material name (round-robin)
 * 4. Elements with no material get grouped by type for random assignment
 */
export function analyzeModel(model: ParsedModel, log: LogFn): Assignment[] {
  const assignments = new Map<string, { elements: IfcElement[]; reason: string }>();

  // Filter to only instance elements (not types)
  const instanceElements = model.elements.filter(e => !e.type.endsWith('TYPE'));

  log(`Found ${instanceElements.length} elements, ${model.materials.length} materials`);

  // Track which elements are assigned
  const assigned = new Set<number>();

  // Step 1: IFC type-based matching (primary for demo model)
  for (const rule of IFC_TYPE_RULES) {
    const matching = instanceElements.filter(e =>
      rule.types.includes(e.type) && !assigned.has(e.id)
    );
    if (matching.length > 0) {
      const key = rule.component;
      const existing = assignments.get(key);
      if (existing) {
        existing.elements.push(...matching);
      } else {
        assignments.set(key, { elements: [...matching], reason: 'ifc-type' });
      }
      matching.forEach(e => assigned.add(e.id));
      log(`  IFC type match: ${matching.length} ${rule.types.join('/')} → ${COMPONENTS[key].label}`);
    }
  }

  // Step 2: For unassigned elements, try material keyword matching
  const unassigned = instanceElements.filter(e => !assigned.has(e.id));
  if (unassigned.length > 0) {
    // Group unassigned elements by their material
    const byMaterial = new Map<string, IfcElement[]>(); // material key → elements
    const noMaterial: IfcElement[] = [];

    for (const elem of unassigned) {
      const matIds = model.elementMaterials.get(elem.id);
      if (matIds && matIds.length > 0) {
        // Use first material as key
        const mat = model.materials.find(m => m.id === matIds[0]);
        const matKey = mat ? `${mat.name}|${mat.category}` : `id:${matIds[0]}`;
        const group = byMaterial.get(matKey) || [];
        group.push(elem);
        byMaterial.set(matKey, group);
      } else {
        noMaterial.push(elem);
      }
    }

    // Try keyword matching for each material group
    for (const [matKey, elems] of byMaterial) {
      const [name, category] = matKey.split('|');
      const nameLower = (name || '').toLowerCase();
      const catLower = (category || '').toLowerCase();

      let matched = false;
      for (const rule of MATERIAL_KEYWORDS) {
        const nameMatch = rule.keywords.some(kw => nameLower.includes(kw));
        const catMatch = rule.categories.some(cat => catLower.includes(cat));
        if (nameMatch || catMatch) {
          const key = rule.component;
          const existing = assignments.get(key);
          if (existing) {
            existing.elements.push(...elems);
          } else {
            assignments.set(key, { elements: [...elems], reason: 'material-keyword' });
          }
          elems.forEach(e => assigned.add(e.id));
          log(`  Material keyword: "${name}" (${category}) → ${COMPONENTS[key].label} [${elems.length} elements]`);
          matched = true;
          break;
        }
      }

      // Step 3: No keyword match → deterministic random assignment per material
      if (!matched) {
        const idx = hashToIndex(matKey, COMPONENT_KEYS.length);
        const key = COMPONENT_KEYS[idx];
        const existing = assignments.get(key);
        if (existing) {
          existing.elements.push(...elems);
          if (existing.reason === 'ifc-type') existing.reason = 'ifc-type + random';
        } else {
          assignments.set(key, { elements: [...elems], reason: 'random' });
        }
        elems.forEach(e => assigned.add(e.id));
        log(`  Random assign: material "${name}" → ${COMPONENTS[key].label} [${elems.length} elements]`);
      }
    }

    // Elements with no material → group by IFC type for random assignment
    if (noMaterial.length > 0) {
      const byType = new Map<string, IfcElement[]>();
      for (const elem of noMaterial) {
        const group = byType.get(elem.type) || [];
        group.push(elem);
        byType.set(elem.type, group);
      }
      for (const [type, elems] of byType) {
        const idx = hashToIndex(type, COMPONENT_KEYS.length);
        const key = COMPONENT_KEYS[idx];
        const existing = assignments.get(key);
        if (existing) {
          existing.elements.push(...elems);
        } else {
          assignments.set(key, { elements: [...elems], reason: 'random' });
        }
        elems.forEach(e => assigned.add(e.id));
        log(`  Random assign: type ${type} (no material) → ${COMPONENTS[key].label} [${elems.length} elements]`);
      }
    }
  }

  // Convert to Assignment array
  const result: Assignment[] = [];
  for (const [component, data] of assignments) {
    result.push({
      component,
      config: COMPONENTS[component],
      elements: data.elements,
      matchReason: data.reason,
    });
  }

  return result;
}

/**
 * Phase 2: Enrich the IFC file by generating new STEP entities.
 */
export function enrichIfc(
  originalText: string,
  model: ParsedModel,
  assignments: Assignment[],
  log: LogFn,
): string {
  const writer = new StepWriter(model.maxId + 1);

  // Ensure OwnerHistory exists
  const ohId = writer.createOwnerHistory(model.ownerHistoryId);
  if (!model.ownerHistoryId) {
    log('Created OwnerHistory');
  }

  for (const assignment of assignments) {
    const { component, config, elements } = assignment;
    const elementIds = elements.map(e => e.id);

    if (elementIds.length === 0) continue;

    log(`\nEnriching ${elements.length} elements with ${config.label}:`);

    // Separate performance properties from EPD properties
    const perfProps = config.properties.filter(p =>
      !p.standard.includes('15804') &&
      !p.note.toLowerCase().includes('gwp total') &&
      !p.note.toLowerCase().includes('acidification') &&
      !p.note.toLowerCase().includes('eutrophication') &&
      !p.note.toLowerCase().includes('ozone depletion') &&
      !p.note.toLowerCase().includes('primary energy')
    );
    const epdProps = config.properties.filter(p =>
      p.standard.includes('15804') ||
      p.note.toLowerCase().includes('gwp total') ||
      p.note.toLowerCase().includes('acidification') ||
      p.note.toLowerCase().includes('eutrophication') ||
      p.note.toLowerCase().includes('ozone depletion') ||
      p.note.toLowerCase().includes('primary energy')
    );

    // 1. Performance property set
    if (perfProps.length > 0) {
      writer.createPropertySet(ohId, config.psetName, perfProps, elementIds);
      log(`  + ${config.psetName} (${perfProps.length} properties)`);
    }

    // 2. EPD indicators property set
    if (epdProps.length > 0) {
      writer.createPropertySet(ohId, config.epdPsetName, epdProps, elementIds);
      log(`  + ${config.epdPsetName} (${epdProps.length} indicators)`);
    }

    // 3. Aggregated LCA indicators (bSDD-aligned)
    writer.createLcaPset(ohId, config.properties, elementIds);
    log(`  + CPset_LCAIndicators_bSDD (aggregated)`);

    // 4. GS1 identifiers
    writer.createGS1Pset(ohId, config.gs1, elementIds);
    log(`  + CPset_GS1_Identifiers`);

    // 5. bSDD classification
    writer.createClassification(ohId, config, elementIds);
    log(`  + Classification: ${config.classificationLabel}`);

    // 6. Document references
    writer.createDocuments(ohId, config.documents, elementIds);
    log(`  + ${config.documents.length} document references`);

    // 7. DPP resolver link
    if (config.gs1.digitalLink) {
      writer.createDppLink(ohId, config.gs1.digitalLink, elementIds);
      log(`  + DPP resolver link`);
    }
  }

  const newLines = writer.getLines();
  log(`\nGenerated ${newLines.length} new STEP entities`);

  return insertStepLines(originalText, newLines);
}

/**
 * Full pipeline: parse → analyze → enrich → return modified text.
 */
export function processIfc(fileText: string, log: LogFn): { enrichedText: string; assignments: Assignment[] } {
  log('Parsing IFC file...');
  const model = parseIfcStep(fileText);
  log(`Parsed ${model.entities.size} entities (max ID: #${model.maxId})`);

  log('\nAnalyzing element → DPP assignments...');
  const assignments = analyzeModel(model, log);

  if (assignments.length === 0) {
    log('\nNo elements found to enrich.');
    return { enrichedText: fileText, assignments };
  }

  log('\nEnriching IFC...');
  const enrichedText = enrichIfc(fileText, model, assignments, log);

  log('\nDone!');
  return { enrichedText, assignments };
}
