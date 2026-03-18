/**
 * Minimal IFC STEP parser - extracts entities we need for enrichment.
 * Works on the raw text of an IFC file without external dependencies.
 */

export interface StepEntity {
  id: number;
  type: string;
  args: string; // raw argument string between outer parentheses
}

export interface IfcElement {
  id: number;
  type: string;
  globalId: string;
  name: string;
}

export interface IfcMaterial {
  id: number;
  name: string;
  category: string;
}

export interface MaterialAssociation {
  elementIds: number[];
  materialRef: number; // direct material or layer set / profile set usage
}

export interface ElementQuantity {
  grossVolume: number | null;
  netVolume: number | null;
  length: number | null;
  grossArea: number | null;
}

export interface ParsedModel {
  entities: Map<number, StepEntity>;
  elements: IfcElement[];
  materials: IfcMaterial[];
  /** element ID → material IDs (resolved through layer/profile sets) */
  elementMaterials: Map<number, number[]>;
  /** material ID → element IDs */
  materialElements: Map<number, number[]>;
  /** element ID → quantity data (volumes, lengths, areas) */
  elementQuantities: Map<number, ElementQuantity>;
  maxId: number;
  ownerHistoryId: number | null;
}

// IFC product types we care about
const PRODUCT_TYPES = new Set([
  'IFCWALL', 'IFCWALLSTANDARDCASE', 'IFCWALLTYPE',
  'IFCCOLUMN', 'IFCCOLUMNTYPE',
  'IFCBEAM', 'IFCBEAMTYPE',
  'IFCMEMBER', 'IFCMEMBERTYPE',
  'IFCPIPESEGMENT', 'IFCPIPESEGMENTTYPE',
  'IFCSLAB', 'IFCSLABTYPE',
  'IFCWINDOW', 'IFCWINDOWTYPE',
  'IFCDOOR', 'IFCDOORTYPE',
  'IFCPLATE', 'IFCPLATETYPE',
  'IFCROOF', 'IFCROOFTYPE',
  'IFCSTAIR', 'IFCSTAIRTYPE',
  'IFCRAILING', 'IFCRAILINGTYPE',
  'IFCCOVERING', 'IFCCOVERINGTYPE',
  'IFCFOOTING', 'IFCFOOTINGTYPE',
  'IFCBUILDINGELEMENTPROXY',
  'IFCFLOWSEGMENT',
  'IFCFLOWTERMINAL',
  'IFCFLOWFITTING',
]);

/** Extract a single-quoted string from a STEP arg at position */
function extractString(args: string, position: number): string {
  const parts = splitStepArgs(args);
  if (position >= parts.length) return '';
  const val = parts[position].trim();
  if (val === '$' || val === '*') return '';
  // Remove surrounding quotes and unescape
  if (val.startsWith("'") && val.endsWith("'")) {
    return val.slice(1, -1).replace(/''/g, "'");
  }
  return val;
}

/** Split STEP arguments respecting nested parentheses and strings */
function splitStepArgs(args: string): string[] {
  const result: string[] = [];
  let depth = 0;
  let inString = false;
  let current = '';

  for (let i = 0; i < args.length; i++) {
    const ch = args[i];
    if (inString) {
      current += ch;
      if (ch === "'" && i + 1 < args.length && args[i + 1] === "'") {
        current += "'";
        i++;
      } else if (ch === "'") {
        inString = false;
      }
    } else if (ch === "'") {
      inString = true;
      current += ch;
    } else if (ch === '(') {
      depth++;
      current += ch;
    } else if (ch === ')') {
      depth--;
      current += ch;
    } else if (ch === ',' && depth === 0) {
      result.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  if (current) result.push(current);
  return result;
}

/** Extract entity references (#N) from a STEP arg string */
function extractRefs(s: string): number[] {
  const refs: number[] = [];
  const re = /#(\d+)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(s)) !== null) {
    refs.push(parseInt(m[1], 10));
  }
  return refs;
}

/** Parse all entities from STEP DATA section */
function parseEntities(text: string): Map<number, StepEntity> {
  const entities = new Map<number, StepEntity>();
  // Match lines like: #123=IFCTYPE(args);
  const re = /^#(\d+)\s*=\s*([A-Z][A-Z0-9_]*)\s*\((.+)\)\s*;/gm;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    entities.set(parseInt(m[1], 10), {
      id: parseInt(m[1], 10),
      type: m[2],
      args: m[3],
    });
  }
  return entities;
}

/** Resolve a material reference through layer sets, profile sets, usages */
function resolveMaterialIds(entities: Map<number, StepEntity>, ref: number): number[] {
  const entity = entities.get(ref);
  if (!entity) return [];

  switch (entity.type) {
    case 'IFCMATERIAL':
      return [ref];

    case 'IFCMATERIALLAYER': {
      // arg 0 is material ref
      const matRefs = extractRefs(splitStepArgs(entity.args)[0] || '');
      return matRefs;
    }

    case 'IFCMATERIALLAYERSET': {
      // arg 0 is list of layers
      const layerRefs = extractRefs(splitStepArgs(entity.args)[0] || '');
      const mats: number[] = [];
      for (const lr of layerRefs) {
        mats.push(...resolveMaterialIds(entities, lr));
      }
      return mats;
    }

    case 'IFCMATERIALLAYERSETUSAGE': {
      // arg 0 is layer set ref
      const lsRef = extractRefs(splitStepArgs(entity.args)[0] || '');
      if (lsRef.length > 0) return resolveMaterialIds(entities, lsRef[0]);
      return [];
    }

    case 'IFCMATERIALPROFILE': {
      // arg 2 is material ref
      const parts = splitStepArgs(entity.args);
      const matRef = extractRefs(parts[2] || '');
      return matRef;
    }

    case 'IFCMATERIALPROFILESET': {
      // arg 2 is list of profiles
      const profRefs = extractRefs(splitStepArgs(entity.args)[2] || '');
      const mats: number[] = [];
      for (const pr of profRefs) {
        mats.push(...resolveMaterialIds(entities, pr));
      }
      return mats;
    }

    case 'IFCMATERIALPROFILESETUSAGE': {
      // arg 0 is profile set ref
      const psRef = extractRefs(splitStepArgs(entity.args)[0] || '');
      if (psRef.length > 0) return resolveMaterialIds(entities, psRef[0]);
      return [];
    }

    case 'IFCMATERIALLIST': {
      // arg 0 is list of materials
      return extractRefs(splitStepArgs(entity.args)[0] || '');
    }

    default:
      return [];
  }
}

export function parseIfcStep(text: string): ParsedModel {
  const entities = parseEntities(text);

  // Find max entity ID
  let maxId = 0;
  for (const id of entities.keys()) {
    if (id > maxId) maxId = id;
  }

  // Extract elements
  const elements: IfcElement[] = [];
  for (const [id, ent] of entities) {
    if (PRODUCT_TYPES.has(ent.type)) {
      const globalId = extractString(ent.args, 0);
      const name = extractString(ent.args, 2);
      elements.push({ id, type: ent.type, globalId, name });
    }
  }

  // Extract materials
  const materials: IfcMaterial[] = [];
  for (const [id, ent] of entities) {
    if (ent.type === 'IFCMATERIAL') {
      const name = extractString(ent.args, 0);
      const category = extractString(ent.args, 2);
      materials.push({ id, name, category });
    }
  }

  // Build element → material mapping via IfcRelAssociatesMaterial
  const elementMaterials = new Map<number, number[]>();
  const materialElements = new Map<number, number[]>();

  for (const [, ent] of entities) {
    if (ent.type === 'IFCRELASSOCIATESMATERIAL') {
      const parts = splitStepArgs(ent.args);
      // arg 4 = RelatedObjects (list of element refs)
      // arg 5 = RelatingMaterial (material/set ref)
      const elemRefs = extractRefs(parts[4] || '');
      const matRef = extractRefs(parts[5] || '');
      if (matRef.length === 0) continue;

      const resolvedMats = resolveMaterialIds(entities, matRef[0]);
      for (const elemId of elemRefs) {
        const existing = elementMaterials.get(elemId) || [];
        for (const mId of resolvedMats) {
          if (!existing.includes(mId)) existing.push(mId);
        }
        elementMaterials.set(elemId, existing);

        for (const mId of resolvedMats) {
          const mel = materialElements.get(mId) || [];
          if (!mel.includes(elemId)) mel.push(elemId);
          materialElements.set(mId, mel);
        }
      }
    }
  }

  // Find OwnerHistory
  let ownerHistoryId: number | null = null;
  for (const [id, ent] of entities) {
    if (ent.type === 'IFCOWNERHISTORY') {
      ownerHistoryId = id;
      break;
    }
  }

  // Extract element quantities (volumes, lengths, areas) via IfcRelDefinesByProperties → IfcElementQuantity
  const elementQuantities = new Map<number, ElementQuantity>();

  for (const [, ent] of entities) {
    if (ent.type !== 'IFCRELDEFINESBYPROPERTIES') continue;
    const parts = splitStepArgs(ent.args);
    const elemRefs = extractRefs(parts[4] || '');
    const defRef = extractRefs(parts[5] || '');
    if (defRef.length === 0) continue;

    const defEntity = entities.get(defRef[0]);
    if (!defEntity || defEntity.type !== 'IFCELEMENTQUANTITY') continue;

    // Extract quantity member refs from arg[5] of IfcElementQuantity
    const eqParts = splitStepArgs(defEntity.args);
    const qtyRefs = extractRefs(eqParts[5] || '');

    // Parse each quantity value
    let grossVolume: number | null = null;
    let netVolume: number | null = null;
    let length: number | null = null;
    let grossArea: number | null = null;

    for (const qRef of qtyRefs) {
      const qEnt = entities.get(qRef);
      if (!qEnt) continue;
      const qParts = splitStepArgs(qEnt.args);
      const qName = extractString(qEnt.args, 0);
      const qVal = parseFloat(qParts[3]?.trim() || '');
      if (isNaN(qVal)) continue;

      if (qEnt.type === 'IFCQUANTITYVOLUME') {
        if (qName === 'GrossVolume') grossVolume = qVal;
        else if (qName === 'NetVolume') netVolume = qVal;
        else if (grossVolume === null) grossVolume = qVal; // fallback: any volume
      } else if (qEnt.type === 'IFCQUANTITYLENGTH') {
        if (qName === 'Length' || qName === 'length') length = qVal;
        else if (length === null) length = qVal;
      } else if (qEnt.type === 'IFCQUANTITYAREA') {
        if (qName === 'GrossSurfaceArea') grossArea = qVal;
        else if (grossArea === null) grossArea = qVal;
      }
    }

    // Assign to each related element
    for (const elemId of elemRefs) {
      const existing = elementQuantities.get(elemId) || {
        grossVolume: null, netVolume: null, length: null, grossArea: null,
      };
      if (grossVolume !== null) existing.grossVolume = grossVolume;
      if (netVolume !== null) existing.netVolume = netVolume;
      if (length !== null) existing.length = length;
      if (grossArea !== null) existing.grossArea = grossArea;
      elementQuantities.set(elemId, existing);
    }
  }

  return {
    entities,
    elements,
    materials,
    elementMaterials,
    materialElements,
    elementQuantities,
    maxId,
    ownerHistoryId,
  };
}
