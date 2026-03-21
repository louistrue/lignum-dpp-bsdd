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

const BASE = 'https://bsdd-dpp.dev';

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
      // EPD indicators – EN 15804+A2:2019, per 1 m³ declared unit
      // A1-A3 (production)
      { name: 'GWP_total_A1-A3', value: '1.23', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total A1-A3' },
      { name: 'AP_A1-A3', value: '0.0045', unit: 'mol H+e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/AP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Acidification potential A1-A3' },
      { name: 'EP_freshwater_A1-A3', value: '0.00012', unit: 'kg PO4e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP_freshwater', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Eutrophication freshwater A1-A3' },
      { name: 'EP_marine_A1-A3', value: '0.0013', unit: 'kg Ne', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP_marine', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Eutrophication marine A1-A3' },
      { name: 'EP_terrestrial_A1-A3', value: '0.014', unit: 'mol Ne', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP_terrestrial', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Eutrophication terrestrial A1-A3' },
      { name: 'ODP_A1-A3', value: '1.2e-8', unit: 'kg CFC-11e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ODP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Ozone depletion potential A1-A3' },
      { name: 'POCP_A1-A3', value: '0.0038', unit: 'kg NMVOCe', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/POCP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Photochemical ozone creation A1-A3' },
      { name: 'PENRT_A1-A3', value: '18.7', unit: 'MJ', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/PENRT', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Primary energy non-renewable total A1-A3' },
      // A4 (transport to site, 150 km truck)
      { name: 'GWP_total_A4', value: '0.152', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total A4' },
      // A5 (installation)
      { name: 'GWP_total_A5', value: '0.048', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total A5' },
      // C2 (transport to disposal)
      { name: 'GWP_total_C2', value: '0.030', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total C2' },
      // C3 (waste processing)
      { name: 'GWP_total_C3', value: '0.019', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total C3' },
      // C4 (disposal/landfill)
      { name: 'GWP_total_C4', value: '0.010', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total C4' },
      // D (reuse/recovery potential)
      { name: 'GWP_total_D', value: '-0.178', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total D' },
    ],
    documents: [
      { name: 'Declaration of Performance (DoP)', url: `${BASE}/files/insul/G4209LSCPR_EN.pdf`, type: 'dop' },
      { name: 'Product Sheet', url: `${BASE}/files/insul/Acoustic%20Batt%20Datasheet%20.pdf`, type: 'datasheet' },
      { name: 'Product Sheet (EPD Data)', url: `${BASE}/files/insul/Data.pdf`, type: 'datasheet' },
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
    dictionaryRootUri: 'https://identifier.buildingsmart.org/uri/cei-bois.org/wood/1.0.0',
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
      // EPD indicators – EN 15804:2012+A1:2013 (IBU EPD-SCH-20130123-IBC1-DE), per 1 m³ declared unit
      // A1-A3 (production)
      { name: 'GWP_total_A1-A3', value: '-671', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'GWP total A1-A3 (incl. biogenic carbon -825 kg CO2e)' },
      { name: 'AP_A1-A3', value: '0.581', unit: 'kg SO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/AP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'Acidification potential A1-A3' },
      { name: 'EP_A1-A3', value: '0.135', unit: 'kg PO4e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'Eutrophication potential A1-A3' },
      { name: 'ODP_A1-A3', value: '2.14e-6', unit: 'kg CFC-11e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ODP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'Ozone depletion potential A1-A3' },
      { name: 'POCP_A1-A3', value: '0.0684', unit: 'kg C2H4e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/POCP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'Photochemical ozone creation A1-A3' },
      { name: 'ADPE_A1-A3', value: '0.00321', unit: 'kg Sbe', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ADPE', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'Abiotic depletion elements A1-A3' },
      { name: 'ADPF_A1-A3', value: '2170', unit: 'MJ', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ADPF', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'Abiotic depletion fossil A1-A3' },
      { name: 'PENRT_A1-A3', value: '2170', unit: 'MJ', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/PENRT', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'Primary energy non-renewable total A1-A3' },
      // A4 (transport to site)
      { name: 'GWP_total_A4', value: '4.12', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'GWP total A4' },
      // A5 (installation)
      { name: 'GWP_total_A5', value: '5.75', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'GWP total A5' },
      // C2 (transport to disposal)
      { name: 'GWP_total_C2', value: '1.37', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'GWP total C2' },
      // C3 (waste processing / incineration releases stored biogenic carbon)
      { name: 'GWP_total_C3', value: '686', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'GWP total C3' },
      // C4 (disposal)
      { name: 'GWP_total_C4', value: '0', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A1', note: 'GWP total C4' },
    ],
    documents: [
      { name: 'Declaration of Performance (DoP)', url: `${BASE}/files/bsh/01-Leistungserklaerung_BSH-SHI-01-01062022.pdf`, type: 'dop' },
      { name: 'Environmental Product Declaration (EPD)', url: `${BASE}/files/bsh/EPD%20Schilliger_glued_laminated_timber_Glulam_as_per_EN_140802013.pdf`, type: 'epd' },
      { name: 'Product Sheet', url: `${BASE}/files/bsh/BSH-Brettschichtholz.pdf`, type: 'datasheet' },
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
      // EPD indicators – EN 15804+A2:2019 (EPD Norge NEPD-3589-2252-EN), per 1 m declared unit
      // A1-A3 (production)
      { name: 'GWP_total_A1-A3', value: '2.35', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total A1-A3' },
      { name: 'AP_A1-A3', value: '0.00593', unit: 'mol H+e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/AP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Acidification potential A1-A3' },
      { name: 'EP_freshwater_A1-A3', value: '0.000129', unit: 'kg Pe', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP_freshwater', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Eutrophication freshwater A1-A3' },
      { name: 'EP_marine_A1-A3', value: '0.00167', unit: 'kg Ne', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP_marine', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Eutrophication marine A1-A3' },
      { name: 'EP_terrestrial_A1-A3', value: '0.0184', unit: 'mol Ne', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/EP_terrestrial', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Eutrophication terrestrial A1-A3' },
      { name: 'ODP_A1-A3', value: '4.89e-8', unit: 'kg CFC-11e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ODP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Ozone depletion potential A1-A3' },
      { name: 'POCP_A1-A3', value: '0.00481', unit: 'kg NMVOCe', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/POCP', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Photochemical ozone creation A1-A3' },
      { name: 'ADPE_A1-A3', value: '1.31e-5', unit: 'kg Sbe', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ADPE', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Abiotic depletion elements A1-A3' },
      { name: 'ADPF_A1-A3', value: '42.8', unit: 'MJ', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/ADPF', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Abiotic depletion fossil A1-A3' },
      { name: 'PENRT_A1-A3', value: '63.7', unit: 'MJ', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/PENRT', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'Primary energy non-renewable total A1-A3' },
      // A4 (transport to site, 500 km truck)
      { name: 'GWP_total_A4', value: '0.060', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total A4' },
      // A5 (installation)
      { name: 'GWP_total_A5', value: '0.047', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total A5' },
      // C1 (demolition)
      { name: 'GWP_total_C1', value: '0.010', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total C1' },
      // C2 (transport to disposal)
      { name: 'GWP_total_C2', value: '0.020', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total C2' },
      // C3 (waste processing / recycling)
      { name: 'GWP_total_C3', value: '0.142', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total C3' },
      // C4 (disposal/landfill)
      { name: 'GWP_total_C4', value: '0.045', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total C4' },
      // D (reuse/recovery potential)
      { name: 'GWP_total_D', value: '-0.824', unit: 'kg CO2e', bsddPropertyUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0/prop/GWP_total', dictionaryUri: 'https://identifier.buildingsmart.org/uri/LCA/LCA/3.0', standard: 'EN 15804+A2', note: 'GWP total D' },
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

// --- LCA / Emissions calculation data ---

export type LifeCycleModule = 'A1-A3' | 'A4' | 'A5' | 'C1' | 'C2' | 'C3' | 'C4' | 'D';

export const ALL_MODULES: LifeCycleModule[] = ['A1-A3', 'A4', 'A5', 'C1', 'C2', 'C3', 'C4', 'D'];

export const MODULE_LABELS: Record<LifeCycleModule, string> = {
  'A1-A3': 'Production',
  'A4': 'Transport to site',
  'A5': 'Installation',
  'C1': 'Deconstruction',
  'C2': 'Waste transport',
  'C3': 'Waste processing',
  'C4': 'Disposal',
  'D': 'Reuse/recovery potential',
};

export interface EpdIndicatorValue {
  indicator: string;
  displayName: string;
  unit: string;
  modules: Partial<Record<LifeCycleModule, number>>;
}

export interface LcaComponentConfig {
  label: string;
  shortLabel: string;
  density: number;
  referenceUnit: 'm3' | 'm';
  referenceQuantity: number;
  linearDensity?: number;
  indicators: EpdIndicatorValue[];
}

/**
 * LCA indicator data per component, sourced from DPP JSON-LD files and EPDs.
 * Values are per declared/reference unit (1 m3 for insulation/timber, 1 m for pipe).
 */
export const LCA_COMPONENTS: Record<string, LcaComponentConfig> = {
  insulation: {
    label: 'Insulation (Knauf Acoustic Batt)',
    shortLabel: 'Insulation',
    density: 85,
    referenceUnit: 'm3',
    referenceQuantity: 1,
    // EN 15804+A2:2019 — EPD S-P-05678 (EPD International)
    indicators: [
      {
        indicator: 'GWP-total', displayName: 'Global Warming Potential', unit: 'kg CO2e',
        modules: { 'A1-A3': 1.23, 'A4': 0.152, 'A5': 0.048, 'C2': 0.030, 'C3': 0.019, 'C4': 0.010, 'D': -0.178 },
      },
      {
        indicator: 'AP', displayName: 'Acidification', unit: 'mol H+e',
        modules: { 'A1-A3': 0.0045 },
      },
      {
        indicator: 'EP-freshwater', displayName: 'Eutrophication (freshwater)', unit: 'kg PO4e',
        modules: { 'A1-A3': 0.00012 },
      },
      {
        indicator: 'EP-marine', displayName: 'Eutrophication (marine)', unit: 'kg Ne',
        modules: { 'A1-A3': 0.0013 },
      },
      {
        indicator: 'EP-terrestrial', displayName: 'Eutrophication (terrestrial)', unit: 'mol Ne',
        modules: { 'A1-A3': 0.014 },
      },
      {
        indicator: 'ODP', displayName: 'Ozone Depletion', unit: 'kg CFC-11e',
        modules: { 'A1-A3': 1.2e-08 },
      },
      {
        indicator: 'POCP', displayName: 'Photochemical Ozone Creation', unit: 'kg NMVOCe',
        modules: { 'A1-A3': 0.0038 },
      },
      {
        indicator: 'PENRT', displayName: 'Primary Energy (non-renewable)', unit: 'MJ',
        modules: { 'A1-A3': 18.7 },
      },
    ],
  },
  timber: {
    label: 'Timber (Schilliger Glulam GL24h)',
    shortLabel: 'Timber',
    density: 410,
    referenceUnit: 'm3',
    referenceQuantity: 1,
    // EN 15804:2012+A1:2013 — EPD-SCH-20130123-IBC1-DE (IBU)
    indicators: [
      {
        indicator: 'GWP-total', displayName: 'Global Warming Potential', unit: 'kg CO2e',
        modules: { 'A1-A3': -671, 'A4': 4.12, 'A5': 5.75, 'C2': 1.37, 'C3': 686, 'C4': 0 },
      },
      {
        indicator: 'AP', displayName: 'Acidification', unit: 'kg SO2e',
        modules: { 'A1-A3': 0.581 },
      },
      {
        indicator: 'EP', displayName: 'Eutrophication', unit: 'kg PO4e',
        modules: { 'A1-A3': 0.135 },
      },
      {
        indicator: 'POCP', displayName: 'Photochemical Ozone Creation', unit: 'kg C2H4e',
        modules: { 'A1-A3': 0.0684 },
      },
      {
        indicator: 'ODP', displayName: 'Ozone Depletion', unit: 'kg CFC-11e',
        modules: { 'A1-A3': 2.14e-06 },
      },
      {
        indicator: 'ADPE', displayName: 'Abiotic Depletion (elements)', unit: 'kg Sbe',
        modules: { 'A1-A3': 0.00321 },
      },
      {
        indicator: 'ADPF', displayName: 'Abiotic Depletion (fossil)', unit: 'MJ',
        modules: { 'A1-A3': 2170 },
      },
      {
        indicator: 'PENRT', displayName: 'Primary Energy (non-renewable)', unit: 'MJ',
        modules: { 'A1-A3': 2170 },
      },
    ],
  },
  pipe: {
    label: 'Pipe (Wavin PVC DN110)',
    shortLabel: 'Pipe',
    density: 1410,
    referenceUnit: 'm',
    referenceQuantity: 1,
    linearDensity: 1.58,
    // EN 15804+A2:2019 — EPD NEPD-3589-2252-EN (EPD Norge)
    indicators: [
      {
        indicator: 'GWP-total', displayName: 'Global Warming Potential', unit: 'kg CO2e',
        modules: { 'A1-A3': 2.35, 'A4': 0.060, 'A5': 0.047, 'C1': 0.010, 'C2': 0.020, 'C3': 0.142, 'C4': 0.045, 'D': -0.824 },
      },
      {
        indicator: 'AP', displayName: 'Acidification', unit: 'mol H+e',
        modules: { 'A1-A3': 0.00593 },
      },
      {
        indicator: 'EP-freshwater', displayName: 'Eutrophication (freshwater)', unit: 'kg Pe',
        modules: { 'A1-A3': 0.000129 },
      },
      {
        indicator: 'EP-marine', displayName: 'Eutrophication (marine)', unit: 'kg Ne',
        modules: { 'A1-A3': 0.00167 },
      },
      {
        indicator: 'EP-terrestrial', displayName: 'Eutrophication (terrestrial)', unit: 'mol Ne',
        modules: { 'A1-A3': 0.0184 },
      },
      {
        indicator: 'ODP', displayName: 'Ozone Depletion', unit: 'kg CFC-11e',
        modules: { 'A1-A3': 4.89e-08 },
      },
      {
        indicator: 'POCP', displayName: 'Photochemical Ozone Creation', unit: 'kg NMVOCe',
        modules: { 'A1-A3': 0.00481 },
      },
      {
        indicator: 'ADPE', displayName: 'Abiotic Depletion (elements)', unit: 'kg Sbe',
        modules: { 'A1-A3': 1.31e-05 },
      },
      {
        indicator: 'ADPF', displayName: 'Abiotic Depletion (fossil)', unit: 'MJ',
        modules: { 'A1-A3': 42.8 },
      },
      {
        indicator: 'PENRT', displayName: 'Primary Energy (non-renewable)', unit: 'MJ',
        modules: { 'A1-A3': 63.7 },
      },
    ],
  },
};
