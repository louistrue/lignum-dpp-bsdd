/**
 * Hardcoded DPP enrichment configuration derived from mapping/mapping.csv
 * and dpp/products/*.jsonld
 */

export interface PropertyDef {
  name: string;
  value: string;
  unit: string;
  bsddPropertyUri: string;
  dictionaryUri: string;
  standard: string;
  note: string;
}

export interface ComponentConfig {
  label: string;
  psetName: string;
  epdPsetName: string;
  properties: PropertyDef[];
  classificationUri: string;
  classificationLabel: string;
  dictionaryRootUri: string;
  documents: { name: string; url: string; type: string }[];
  gs1: {
    gtin?: string;
    serial?: string;
    batch?: string;
    digitalLink?: string;
  };
}

const BASE = 'https://lignum-dpp-bsdd.vercel.app';

export const COMPONENTS: Record<string, ComponentConfig> = {
  insulation: {
    label: 'Insulation (Knauf Acoustic Batt)',
    psetName: 'CPset_InsulationPerformance',
    epdPsetName: 'CPset_EpdIndicators',
    dictionaryRootUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0',
    classificationUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/class/Mineral Wool Insulation',
    classificationLabel: 'Mineral Wool Insulation',
    properties: [
      { name: 'ThermalConductivity', value: '0.047', unit: 'W/mK', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/ThermalConductivity', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13162', note: 'thermal conductivity range 0.047-0.050 W/mK from datasheet' },
      { name: 'Density', value: '85', unit: 'kg/m³', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/Density', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13162', note: 'from product datasheet' },
      { name: 'WaterVapourResistance', value: '5.00', unit: 'MNs/g.m', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/WaterVapourResistance', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13162', note: 'from DoP' },
      { name: 'CompressiveStrength', value: '10', unit: 'kPa', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/CompressiveStrength', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13162', note: 'CS(10) from DoP' },
      { name: 'DimensionalStability', value: '1', unit: '%-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/DimensionalStability', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13162', note: 'from DoP' },
      { name: 'AirFlowResistivity', value: '10', unit: 'kPa·s/m²', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/AirFlowResistivity', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13162', note: 'from BSI reference' },
      { name: 'LongTermWaterAbsorptionTotal', value: '10', unit: '%', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/LongTermWaterAbsorptionTotal', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13162', note: 'from BSI reference' },
      { name: 'ReactionToFire', value: 'A2-s1d0', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/ReactionToFire', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13501-1', note: 'Euroclass fire rating' },
      { name: 'DOPC_ThermalResistance', value: '2.55', unit: 'm²K/W', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/ThermalResistance', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13162', note: 'DoPC thermal resistance R-value' },
      { name: 'DOPC_SoundAbsorption', value: '0.95', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/SoundAbsorption', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN ISO 354', note: 'DoPC sound absorption coefficient' },
      { name: 'DOPC_TensileStrengthPerpendicular', value: '5', unit: 'kPa', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/TensileStrengthPerpendicular', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 1607', note: 'DoPC tensile strength perpendicular to faces' },
      { name: 'DOPC_ThicknessTolerance', value: 'T5', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/ThicknessTolerance', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0', standard: 'EN 13162', note: 'DoPC thickness tolerance class' },
      // EPD indicators
      { name: 'GWP_total', value: '7.20', unit: 'kgCO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'GWP total A1-A3' },
      { name: 'AE', value: '0.005', unit: 'kgSO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/AE', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Acidification potential A1-A3' },
      { name: 'EP_freshwater', value: '0.002', unit: 'kgPO4e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP_freshwater', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Eutrophication potential A1-A3' },
      { name: 'ODP', value: '0.000001', unit: 'kg CFC-11e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ODP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Ozone depletion potential A1-A3' },
      { name: 'PENRE-with-energycontent-tot', value: '85.0', unit: 'MJ', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/non-renewableprimaryresourceswithenergycontent-tot', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Primary energy total A1-A3' },
    ],
    documents: [
      { name: 'Product Datasheet', url: `${BASE}/files/insul/Acoustic%20Batt%20Datasheet%20.pdf`, type: 'datasheet' },
      { name: 'Product Datasheet', url: `${BASE}/files/insul/Data.pdf`, type: 'datasheet' },
      { name: 'Declaration of Performance (DoP)', url: `${BASE}/files/insul/G4209LSCPR_EN.pdf`, type: 'dop' },
    ],
    gs1: {
      gtin: '04012345678901',
      serial: 'KI-AB-2025-001',
      digitalLink: `${BASE}/id/01/04012345678901/21/KI-AB-2025-001?linkType=dpp`,
    },
  },

  timber: {
    label: 'Timber (Schilliger Glulam GL24h)',
    psetName: 'CPset_TimberPerformance',
    epdPsetName: 'CPset_EpdIndicators',
    dictionaryRootUri: 'https://identifier.buildingsmart.org/uri/demo2025/timber/1.0.0',
    classificationUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/class/glulam-gl24h',
    classificationLabel: 'Glulam GL24h',
    properties: [
      { name: 'strength according to EN 338 (class)', value: 'GL24h', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/timber/1.0.0/prop/strengthClass_EN14080', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/timber/1.0.0', standard: 'EN 14080', note: 'strength class from product name' },
      { name: 'density', value: '410', unit: 'kg/m³', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/10bcd2c4-73f7-4ff1-b220-c2f162a26f8d', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 14080', note: 'typical glulam density from product datasheet' },
      { name: 'DOPC_BendingStrength', value: '24.0', unit: 'MPa', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/bendingStrength', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 14080', note: 'DoPC bending strength fm.g.k' },
      { name: 'DOPC_TensionParallel', value: '19.2', unit: 'MPa', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/tensionStrengthParallel', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 14080', note: 'DoPC tension parallel ft.0.g.k' },
      { name: 'DOPC_TensionPerpendicular', value: '0.5', unit: 'MPa', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/tensionStrengthPerpendicular', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 14080', note: 'DoPC tension perpendicular ft.90.g.k' },
      { name: 'DOPC_ShearStrength', value: '3.5', unit: 'MPa', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/shearStrength', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 14080', note: 'DoPC shear strength fv.g.k' },
      { name: 'DOPC_CompressionParallel', value: '24.0', unit: 'MPa', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/compressionStrengthParallel', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 14080', note: 'DoPC compression parallel fc.0.g.k' },
      { name: 'DOPC_CompressionPerpendicular', value: '2.5', unit: 'MPa', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/compressionStrengthPerpendicular', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 14080', note: 'DoPC compression perpendicular fc.90.g.k' },
      { name: 'DOPC_ModulusOfElasticity', value: '11500', unit: 'MPa', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/modulusOfElasticity', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 14080', note: 'DoPC modulus of elasticity E0.g.mean' },
      { name: 'DOPC_ReactionToFire', value: 'D-s2.d0', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/reactionToFire', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 13501-1', note: 'DoPC Euroclass fire rating' },
      { name: 'DOPC_FormaldehydeEmission', value: 'E1', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/formaldehydeEmission', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 717-1', note: 'DoPC formaldehyde emission class' },
      { name: 'DOPC_DelaminationResistance', value: 'Pass', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0/prop/delaminationResistance', dictionaryUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0', standard: 'EN 14080', note: 'DoPC delamination resistance test result' },
      // EPD indicators
      { name: 'GWP_total', value: '-615.0', unit: 'kgCO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'GWP total A1-A3 (biogenic)' },
      { name: 'AE', value: '0.004', unit: 'kgSO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/AE', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Acidification potential A1-A3' },
      { name: 'EP_freshwater', value: '0.001', unit: 'kgPO4e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP_freshwater', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Eutrophication potential A1-A3' },
      { name: 'ODP', value: '0.0000008', unit: 'kg CFC-11e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ODP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Ozone depletion potential A1-A3' },
      { name: 'PENRE-with-energycontent-tot', value: '95.0', unit: 'MJ', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/non-renewableprimaryresourceswithenergycontent-tot', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Primary energy total A1-A3' },
    ],
    documents: [
      { name: 'Declaration of Performance (DoP)', url: `${BASE}/files/bsh/01-Leistungserklaerung_BSH-SHI-01-01062022.pdf`, type: 'dop' },
      { name: 'Environmental Product Declaration (EPD)', url: `${BASE}/files/bsh/EPD%20Schilliger_glued_laminated_timber_Glulam_as_per_EN_140802013.pdf`, type: 'epd' },
    ],
    gs1: {
      gtin: '07640123456789',
      serial: 'SHI-GL24h-2025-001',
      digitalLink: `${BASE}/id/01/07640123456789/21/SHI-GL24h-2025-001?linkType=dpp`,
    },
  },

  pipe: {
    label: 'Pipe (Wavin PVC DN110)',
    psetName: 'CPset_PipePerformance',
    epdPsetName: 'CPset_EpdIndicators',
    dictionaryRootUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0',
    classificationUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/class/pvc-sewage-pipe',
    classificationLabel: 'PVC sewage pipe',
    properties: [
      { name: 'COLOUR', value: 'Black with blue stripes', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/COLOUR', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: '', note: 'Product marking colour' },
      { name: 'PIPE-TYPE', value: 'co-extruded', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/PIPE-TYPE', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: '', note: 'Pipe construction type' },
      { name: 'VACUUM-STIFF', value: '4', unit: 'kN/m²', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/VACUUM-STIFF', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN 1401-1', note: 'Ring stiffness class SN4' },
      { name: 'DOPC_ImpactResistance', value: 'Pass', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/impactResistance', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN 1401-1', note: 'DoPC TIR impact resistance' },
      { name: 'DOPC_WallThickness', value: '3.2', unit: 'mm', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/wallThickness', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN 1401-1', note: 'DoPC minimum wall thickness' },
      { name: 'DOPC_ChemicalResistance', value: 'Pass', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/chemicalResistance', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN ISO 12099', note: 'DoPC chemical resistance' },
      { name: 'DOPC_PressureRating', value: 'PN4', unit: 'bar', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/pressureRating', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN 1401-1', note: 'DoPC nominal pressure rating' },
      { name: 'DOPC_Watertightness', value: 'Pass', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/watertightness', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN 1401-1', note: 'DoPC watertightness test' },
      { name: 'DOPC_LongitudinalReversion', value: '5', unit: '%', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/longitudinalReversion', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN 1401-1', note: 'DoPC longitudinal reversion max' },
      { name: 'DOPC_ReactionToFire', value: 'E', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/reactionToFire', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN 13501-1', note: 'DoPC Euroclass fire rating' },
      { name: 'DOPC_InternalPressureResistance', value: 'Pass', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/internalPressureResistance', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN 1401-1', note: 'DoPC resistance to internal pressure' },
      { name: 'DOPC_CreepRatio', value: '2.0', unit: '-', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0/prop/creepRatio', dictionaryUri: 'https://identifier.buildingsmart.org/uri/demo2025/ppipes/1.0.0', standard: 'EN 1401-1', note: 'DoPC creep ratio' },
      // EPD indicators
      { name: 'GWP_total', value: '2.85', unit: 'kgCO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'GWP total A1-A3' },
      { name: 'AE', value: '0.012', unit: 'kgSO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/AE', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Acidification potential A1-A3' },
      { name: 'EP_freshwater', value: '0.0015', unit: 'kgPO4e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP_freshwater', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Eutrophication potential A1-A3' },
      { name: 'ODP', value: '0.0000012', unit: 'kg CFC-11e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ODP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Ozone depletion potential A1-A3' },
      { name: 'PENRE-with-energycontent-tot', value: '120.0', unit: 'MJ', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/non-renewableprimaryresourceswithenergycontent-tot', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804', note: 'Primary energy total A1-A3' },
    ],
    documents: [
      { name: 'Environmental Product Declaration (EPD)', url: `${BASE}/files/pipe/NEPD-3589-2252_PVC-Sewage-Pipe.pdf`, type: 'epd' },
    ],
    gs1: {
      gtin: '05790001234561',
      serial: 'WV-DN110-2025-001',
      digitalLink: `${BASE}/id/01/05790001234561/21/WV-DN110-2025-001?linkType=dpp`,
    },
  },
};

/** IFC type → component mapping for demo model (hardcoded, same as patch_ifc.py) */
export const IFC_TYPE_RULES: { types: string[]; component: string }[] = [
  { types: ['IFCWALL', 'IFCWALLSTANDARDCASE'], component: 'insulation' },
  { types: ['IFCPIPESEGMENT'], component: 'pipe' },
  { types: ['IFCCOLUMN', 'IFCBEAM', 'IFCMEMBER'], component: 'timber' },
];

/** Material keyword → component mapping for user models (fallback) */
export const MATERIAL_KEYWORDS: { keywords: string[]; categories: string[]; component: string }[] = [
  { keywords: ['mineral wool', 'insulation', 'glasswool', 'rockwool', 'knauf', 'stone wool', 'eps', 'xps', 'polyurethane'], categories: ['insulation'], component: 'insulation' },
  { keywords: ['wood', 'timber', 'glulam', 'brettschichtholz', 'schilliger', 'bsh', 'gl24', 'clt', 'lvl', 'plywood'], categories: ['wood', 'timber'], component: 'timber' },
  { keywords: ['pvc', 'pipe', 'hdpe', 'pe100', 'wavin', 'sewage', 'drainage', 'polyethylene'], categories: ['plastic', 'pipe'], component: 'pipe' },
];

export const COMPONENT_KEYS = Object.keys(COMPONENTS);
