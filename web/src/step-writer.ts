/**
 * STEP entity writer — generates new IFC STEP lines to append to the DATA section.
 */

import type { ComponentConfig, PropertyDef } from './config';

// IFC GUID: 22-char base64 with custom alphabet
const IFC_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$';

function generateIfcGuid(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  let result = '';
  // Encode 128 bits as 22 base-64 characters (6 bits each, 22*6=132, last 4 bits unused)
  let bits = 0n;
  for (const b of bytes) bits = (bits << 8n) | BigInt(b);
  for (let i = 0; i < 22; i++) {
    const idx = Number((bits >> BigInt((21 - i) * 6)) & 0x3fn);
    result += IFC_CHARS[idx];
  }
  return result;
}

/** Escape a string for IFC STEP format */
function stepStr(s: string): string {
  return "'" + s.replace(/'/g, "''") + "'";
}

/** Determine IFC measure type from unit string */
function ifcMeasure(value: string, unit: string): string {
  const v = value.trim();
  const u = unit.trim().toLowerCase().replace(/²/g, '2').replace(/³/g, '3').replace(/·/g, '/');
  const isNum = !isNaN(parseFloat(v));

  if ((u === 'w/mk' || u === 'w/m/k') && isNum) return `IFCTHERMALCONDUCTIVITYMEASURE(${parseFloat(v)})`;
  if ((u === 'kg/m3' || u === 'kg/m^3') && isNum) return `IFCMASSDENSITYMEASURE(${parseFloat(v)})`;
  if ((u === 'mm' || u === 'm') && isNum) return `IFCPOSITIVELENGTHMEASURE(${parseFloat(v)})`;
  if (u === 'mpa' && isNum) return `IFCPRESSUREMEASURE(${parseFloat(v)})`;

  // EPD units → IfcReal
  const epdUnits = ['kgco2e', 'kgso2e', 'kgcfc-11e', 'kgpo4e', 'mj', 'kj', 'kpa', 'kn/m2',
    'kpa/s/m2', 'kpas/m2', '%', '%-', 'm2k/w', 'bar'];
  if (epdUnits.includes(u.replace(/ /g, '')) && isNum) return `IFCREAL(${parseFloat(v)})`;

  if ((u === '-' || u === '') && isNum) return `IFCREAL(${parseFloat(v)})`;

  // Text value
  return `IFCLABEL(${stepStr(v)})`;
}

export class StepWriter {
  private nextId: number;
  private lines: string[] = [];

  constructor(startId: number) {
    this.nextId = startId;
  }

  private newId(): number {
    return this.nextId++;
  }

  getNextId(): number {
    return this.nextId;
  }

  getLines(): string[] {
    return this.lines;
  }

  private emit(id: number, type: string, args: string): number {
    this.lines.push(`#${id}=${type}(${args});`);
    return id;
  }

  /** Create OwnerHistory if not present */
  createOwnerHistory(existingId: number | null): number {
    if (existingId !== null) return existingId;
    const personId = this.newId();
    this.emit(personId, 'IFCPERSON', "$,$,'DPPEnrich',$,$,$,$,$");
    const orgId = this.newId();
    this.emit(orgId, 'IFCORGANIZATION', "$,'buildingSMART DPP',$,$,$");
    const poId = this.newId();
    this.emit(poId, 'IFCPERSONANDORGANIZATION', `#${personId},#${orgId},$`);
    const appId = this.newId();
    this.emit(appId, 'IFCAPPLICATION', `#${orgId},'1.0','IFC DPP Enrichment','DPPEnrich'`);
    const ohId = this.newId();
    this.emit(ohId, 'IFCOWNERHISTORY', `#${poId},#${appId},$,.ADDED.,${Math.floor(Date.now() / 1000)},$,$,0`);
    return ohId;
  }

  /** Create a property set with properties and link to elements */
  createPropertySet(
    ownerHistoryId: number,
    psetName: string,
    properties: PropertyDef[],
    elementIds: number[],
  ): { psetId: number; propIds: number[] } {
    const propIds: number[] = [];
    for (const p of properties) {
      const propId = this.newId();
      const measure = ifcMeasure(p.value, p.unit);
      const desc = p.bsddPropertyUri ? stepStr(p.bsddPropertyUri) : '$';
      this.emit(propId, 'IFCPROPERTYSINGLEVALUE', `${stepStr(p.name)},${desc},${measure},$`);
      propIds.push(propId);
    }

    const psetId = this.newId();
    const propList = propIds.map(id => `#${id}`).join(',');
    this.emit(psetId, 'IFCPROPERTYSET',
      `'${generateIfcGuid()}',#${ownerHistoryId},${stepStr(psetName)},$,(${propList})`);

    // Link to elements
    const elemList = elementIds.map(id => `#${id}`).join(',');
    const relId = this.newId();
    this.emit(relId, 'IFCRELDEFINESBYPROPERTIES',
      `'${generateIfcGuid()}',#${ownerHistoryId},$,$,(${elemList}),#${psetId}`);

    return { psetId, propIds };
  }

  /** Create LCA aggregated indicator property set */
  createLcaPset(
    ownerHistoryId: number,
    properties: PropertyDef[],
    elementIds: number[],
  ): void {
    // Aggregate EPD properties by bSDD URI
    const agg = new Map<string, { sum: number; unit: string; name: string }>();
    for (const p of properties) {
      if (!p.standard.includes('15804') && !p.note.toLowerCase().includes('epd') &&
          !p.note.toLowerCase().includes('a1') && !p.note.toLowerCase().includes('gwp')) continue;
      const key = p.bsddPropertyUri;
      if (!key) continue;
      const val = parseFloat(p.value);
      if (isNaN(val)) continue;
      const existing = agg.get(key);
      if (existing) {
        existing.sum += val;
      } else {
        // Extract prop name from URI
        const segs = key.split('/');
        const propName = segs[segs.length - 1];
        agg.set(key, { sum: val, unit: p.unit, name: propName });
      }
    }

    if (agg.size === 0) return;

    const propIds: number[] = [];
    for (const [uri, info] of agg) {
      const propId = this.newId();
      const measure = ifcMeasure(String(info.sum), info.unit);
      this.emit(propId, 'IFCPROPERTYSINGLEVALUE', `${stepStr(info.name)},${stepStr(uri)},${measure},$`);
      propIds.push(propId);
    }

    const psetId = this.newId();
    const propList = propIds.map(id => `#${id}`).join(',');
    this.emit(psetId, 'IFCPROPERTYSET',
      `'${generateIfcGuid()}',#${ownerHistoryId},'CPset_LCAIndicators_bSDD',$,(${propList})`);

    const elemList = elementIds.map(id => `#${id}`).join(',');
    const relId = this.newId();
    this.emit(relId, 'IFCRELDEFINESBYPROPERTIES',
      `'${generateIfcGuid()}',#${ownerHistoryId},$,$,(${elemList}),#${psetId}`);
  }

  /** Create GS1 identifier property set */
  createGS1Pset(
    ownerHistoryId: number,
    gs1: ComponentConfig['gs1'],
    elementIds: number[],
  ): void {
    const props: { name: string; value: string }[] = [];
    if (gs1.gtin) props.push({ name: 'GS1_AI_01_GTIN', value: gs1.gtin });
    if (gs1.serial) props.push({ name: 'GS1_AI_21_SERIAL', value: gs1.serial });
    if (gs1.batch) props.push({ name: 'GS1_AI_10_BATCH', value: gs1.batch });
    if (gs1.digitalLink) props.push({ name: 'GS1_DigitalLink', value: gs1.digitalLink });
    if (props.length === 0) return;

    const propIds: number[] = [];
    for (const p of props) {
      const propId = this.newId();
      this.emit(propId, 'IFCPROPERTYSINGLEVALUE', `${stepStr(p.name)},$,IFCLABEL(${stepStr(p.value)}),$`);
      propIds.push(propId);
    }

    const psetId = this.newId();
    const propList = propIds.map(id => `#${id}`).join(',');
    this.emit(psetId, 'IFCPROPERTYSET',
      `'${generateIfcGuid()}',#${ownerHistoryId},'CPset_GS1_Identifiers',$,(${propList})`);

    const elemList = elementIds.map(id => `#${id}`).join(',');
    const relId = this.newId();
    this.emit(relId, 'IFCRELDEFINESBYPROPERTIES',
      `'${generateIfcGuid()}',#${ownerHistoryId},$,$,(${elemList}),#${psetId}`);
  }

  /** Create IfcClassification + IfcClassificationReference + IfcRelAssociatesClassification */
  createClassification(
    ownerHistoryId: number,
    config: ComponentConfig,
    elementIds: number[],
  ): void {
    // Derive dictionary root from classificationUri when it points to a different
    // dictionary than dictionaryRootUri (e.g. class in cei-bois.org/wood but config
    // says demo2025/timber). The parent IfcClassification must match the class URI.
    let rootUri = config.dictionaryRootUri;
    if (config.classificationUri.includes('/class/')) {
      const derivedRoot = config.classificationUri.split('/class/')[0];
      if (derivedRoot && derivedRoot !== rootUri) {
        rootUri = derivedRoot;
      }
    }

    // Parse dictionary metadata from URI
    const parts = rootUri.split('/');
    const uriIdx = parts.indexOf('uri');
    const scheme = uriIdx >= 0 && parts.length > uriIdx + 1 ? parts[uriIdx + 1] : '';
    const dictName = uriIdx >= 0 && parts.length > uriIdx + 2 ? parts[uriIdx + 2] : 'bSDD';
    const edition = uriIdx >= 0 && parts.length > uriIdx + 3 ? parts[uriIdx + 3] : '';

    const clsId = this.newId();
    // IFC4 IfcClassification: Source, Edition, EditionDate, Name, Description, Specification(Location), ReferenceTokens
    this.emit(clsId, 'IFCCLASSIFICATION',
      `${stepStr(scheme)},${stepStr(edition)},$,${stepStr(dictName)},$,${stepStr(rootUri)},$`);

    // Extract identification from class URI
    let ident = '$';
    if (config.classificationUri.includes('/class/')) {
      const classSegs = config.classificationUri.split('/class/');
      if (classSegs.length > 1) ident = stepStr(classSegs[1]);
    }

    const refId = this.newId();
    // IFC4 IfcClassificationReference: Location, Identification, Name, ReferencedSource, Description, Sort
    this.emit(refId, 'IFCCLASSIFICATIONREFERENCE',
      `${stepStr(config.classificationUri)},${ident},${stepStr(config.classificationLabel)},#${clsId},${stepStr('Classification concept: ' + config.classificationLabel)},$`);

    const elemList = elementIds.map(id => `#${id}`).join(',');
    const relId = this.newId();
    this.emit(relId, 'IFCRELASSOCIATESCLASSIFICATION',
      `'${generateIfcGuid()}',#${ownerHistoryId},$,${stepStr('bSDD: ' + config.classificationLabel)},(${elemList}),#${refId}`);
  }

  /** Create document references and associate with elements */
  createDocuments(
    ownerHistoryId: number,
    documents: ComponentConfig['documents'],
    elementIds: number[],
  ): void {
    for (const doc of documents) {
      const infoId = this.newId();
      // IFC4 IfcDocumentInformation: Identification, Name, Description, Location, Purpose,
      // IntendedUse, Scope, Revision, DocumentOwner, Editors, CreationTime, LastRevisionTime,
      // ElectronicFormat, ValidFrom, ValidUntil, Confidentiality, Status
      this.emit(infoId, 'IFCDOCUMENTINFORMATION',
        `${stepStr(doc.name)},${stepStr(doc.name)},$,${stepStr(doc.url)},$,$,$,$,$,$,$,$,$,$,$,$,$`);

      const refId = this.newId();
      // IFC4 IfcDocumentReference: Location, Identification, Name, Description, ReferencedDocument
      this.emit(refId, 'IFCDOCUMENTREFERENCE',
        `${stepStr(doc.url)},${stepStr(doc.name)},$,$,#${infoId}`);

      const elemList = elementIds.map(id => `#${id}`).join(',');
      const relId = this.newId();
      this.emit(relId, 'IFCRELASSOCIATESDOCUMENT',
        `'${generateIfcGuid()}',#${ownerHistoryId},$,$,(${elemList}),#${refId}`);
    }
  }

  /** Create DPP resolver link as document reference */
  createDppLink(
    ownerHistoryId: number,
    digitalLink: string,
    elementIds: number[],
  ): void {
    const infoId = this.newId();
    // IFC4 IfcDocumentInformation: Identification, Name, Description, Location, ...13 more optional attrs
    this.emit(infoId, 'IFCDOCUMENTINFORMATION',
      `'Digital Product Passport (resolver)','Digital Product Passport (resolver)',$,${stepStr(digitalLink)},$,$,$,$,$,$,$,$,$,$,$,$,$`);

    const refId = this.newId();
    this.emit(refId, 'IFCDOCUMENTREFERENCE',
      // IFC4 IfcDocumentReference: Location, Identification, Name, Description, ReferencedDocument
      `${stepStr(digitalLink)},'Digital Product Passport (resolver)',$,$,#${infoId}`);

    const elemList = elementIds.map(id => `#${id}`).join(',');
    const relId = this.newId();
    this.emit(relId, 'IFCRELASSOCIATESDOCUMENT',
      `'${generateIfcGuid()}',#${ownerHistoryId},$,$,(${elemList}),#${refId}`);
  }
}

/** Insert new STEP lines into an IFC file text before the final ENDSEC; */
export function insertStepLines(originalText: string, newLines: string[]): string {
  if (newLines.length === 0) return originalText;

  // Find the last ENDSEC; in the DATA section
  const endSecIdx = originalText.lastIndexOf('ENDSEC;');
  if (endSecIdx === -1) {
    throw new Error('Invalid IFC file: no ENDSEC; found');
  }

  const before = originalText.slice(0, endSecIdx);
  const after = originalText.slice(endSecIdx);
  const insertion = newLines.join('\n') + '\n';

  return before + insertion + after;
}
