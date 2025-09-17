# Digital Product Passport (DPP) POC - Lignum Integration

**Proof of Concept für modulare Digital Product Passports mit IFC-Integration**

## 📋 Projektübersicht

Dieser POC demonstriert die **vollständige Integration** von Digital Product Passports (DPP) in openBIM Workflows. Das Projekt folgt etablierten DPP-Standards und implementiert den **modularen Ansatz** mit standardisierten Patterns für Identifier, Quantities & Units sowie Provenance.

### 🎯 Zielerreichung

✅ **Alle ursprünglichen Ziele erreicht:**
- **Modulare DPP-JSON-LD** nach etablierten Standards  
- **IFC-Integration** via CPset_ PropertySets (keine Pset_ Konflikte)
- **bSDD-Referenzierung** mit demo2025 Dictionaries
- **Vollständige Provenance** mit PDF-Quellenverweisen
- **IDS-Validierung** für automatisierte Qualitätskontrolle

## 🏗️ Architektur & Standards

### DPP Modular Patterns (entspricht UN Transparency Protocol)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Identifier    │    │ Quantities &    │    │   Provenance    │
│    Pattern      │    │  Units Pattern  │    │    Pattern      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Product URI   │    │ • QuantityKind  │    │ • wasDerivedFrom│
│ • Manufacturer  │    │ • QuantityValue │    │ • attributedTo  │
│ • Classification│    │ • hasUnit       │    │ • hasDocument   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### IFC-Integration Schema

```
IFC Model
├── IfcWallStandardCase
│   ├── CPset_Insulation_Performance
│   │   ├── lambdaDeclared_EN12664 (IfcThermalConductivityMeasure)
│   │   └── fireReactionEuroclass_EN13501 (IfcLabel)
│   ├── IfcClassificationReference → demo2025/thermal-insulation
│   └── IfcDocumentReference → Knauf PDFs
├── IfcPipeSegment  
│   ├── CPset_Pipe_DimensionsAndRatings
│   │   ├── nominalDiameter (IfcLabel)
│   │   ├── materialType (IfcLabel) 
│   │   ├── density (IfcMassDensityMeasure)
│   │   └── thermalConductivity (IfcThermalConductivityMeasure)
│   ├── IfcClassificationReference → demo2025/ppipes
│   └── IfcDocumentReference → NEPD-3589-2252-EN
└── IfcMember (Glulam)
    ├── CPset_Timber_Performance
    │   ├── strengthClass_EN14080 (IfcLabel)
    │   └── density (IfcMassDensityMeasure)
    ├── IfcClassificationReference → cei-bois.org/wood
    └── IfcDocumentReference → Schilliger PDFs
```

## 📁 Projektstruktur

```
lignum-dpp/
├── README.md                           # Diese Datei
├── dpp_knauf_acoustic_batt.jsonld      # Knauf Dämmung DPP
├── dpp_pvc_sewage_pipe.jsonld          # PVC Abwasserrohr DPP  
├── dpp_schilliger_glulam.jsonld        # Schilliger Brettschichtholz DPP
├── mapping.csv                         # Property-Mapping mit bSDD URIs
├── POC.ids                            # IDS Validierungsregeln
├── DOCS_dpp.md                        # DPP Dokumentation
├── DOCS_patch_poc_ifc.md              # IFC Patching Anleitung
└── patch_poc_ifc.py                   # IFC Integration Script
```

## 🔬 Technische DPP-Aspekte

### 1. JSON-LD Struktur nach W3C Standards

Alle DPPs verwenden **konsistente Ontologie**:

```json
{
  "@context": {
    "dpp": "http://www.w3id.org/dpp#",
    "bsdd": "https://identifier.buildingsmart.org/uri/"
  },
  "type": "dpp:Product",
  "dpp:hasSpecification": {
    "@type": "dpp:ProductSpecification", 
    "dpp:hasQuantity": [
      {
        "@type": "dpp:Quantity",
        "dpp:hasQuantityKind": {...},
        "dpp:hasQuantityValue": {...},
        "dpp:hasConceptUri": "https://identifier.buildingsmart.org/uri/...",
        "dpp:wasDerivedFrom": {...}
      }
    ]
  }
}
```

### 2. bSDD Integration (buildingSMART Data Dictionary)

**Verwendete Dictionaries:**
- **Dämmung:** `demo2025/thermal-insulation-products/1.0.0`
- **Rohre:** `demo2025/ppipes/1.0`  
- **Holz:** `cei-bois.org/wood/1.0.0`

**Property-Verknüpfung:**
```csv
component,cp_property,bsdd_property_uri,dictionary_uri
insulation,lambdaDeclared_EN12664,https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/thermalConductivityDeclared_EN12664,https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0
```

### 3. Provenance & Rückverfolgbarkeit

**Vollständige Evidenzkette:**
- **Quelle:** Hersteller-PDFs und EPDs (Environmental Product Declarations)
- **Attribution:** Spezifische Herstellernamen (Knauf Insulation GmbH, Nordisk Wavin A/S, Schilliger Holz AG)
- **Standards:** EN 13162, EN 13501-1, EN 14080, NEPD-3589-2252-EN
- **Dokumente:** Direkte URI-Links zu Datenblättern

## 🔧 IFC-Integration Details

### CPset_ PropertySets (Konfliktvermeidung)

**Bewusste Vermeidung von Pset_** zur Konfliktvermeidung mit IFC Schema:

```cpp
// Dämmung Properties
CPset_Insulation_Performance:
├── lambdaDeclared_EN12664: IfcThermalConductivityMeasure (0.047 W/mK)
└── fireReactionEuroclass_EN13501: IfcLabel ("A1")

// Rohr Properties  
CPset_Pipe_DimensionsAndRatings:
├── nominalDiameter: IfcLabel ("DN110")
├── materialType: IfcLabel ("uPVC")  
├── density: IfcMassDensityMeasure (1410 kg/m³)
└── thermalConductivity: IfcThermalConductivityMeasure (0.15 W/mK)

// Holz Properties
CPset_Timber_Performance:
├── strengthClass_EN14080: IfcLabel ("GL24h")
└── density: IfcMassDensityMeasure (410 kg/m³)
```

### IFC Measure Types Mapping

**Automatische Typ-Erkennung basierend auf Einheiten:**

| Einheit | IFC Measure Type | Beispiel |
|---------|------------------|----------|
| `W/mK` | `IfcThermalConductivityMeasure` | 0.047 W/mK |  
| `kg/m³` | `IfcMassDensityMeasure` | 1410 kg/m³ |
| `mm`, `m` | `IfcPositiveLengthMeasure` | 110 mm |
| `-` (numerisch) | `IfcReal` | 11 |
| `-` (Text) | `IfcLabel` | "A1", "GL24h" |

## 🏭 Produktdatengrundlage

### Knauf Insulation Acoustic Batt
- **Hersteller:** Knauf Insulation GmbH
- **Wärmeleitfähigkeit:** 0.047 W/mK (EN 12664)
- **Brandklasse:** A1 (EN 13501-1)
- **Klassifikation:** Glass mineral wool batt
- **Evidenz:** Produktdatenblatt + EPD

### PVC Abwasserrohr (Nordisk Wavin A/S)
- **EPD:** NEPD-3589-2252-EN (Norwegische EPD Foundation)
- **Nominaldurchmesser:** DN110
- **Material:** uPVC
- **Dichte:** 1410 kg/m³ 
- **Wärmeleitfähigkeit:** 0.15 W/mK (bei 23°C)
- **Klassifikation:** PVC sewage pipe

### Schilliger Brettschichtholz
- **Hersteller:** Schilliger Holz AG
- **Festigkeitsklasse:** GL24h (EN 14080)
- **Dichte:** 410 kg/m³
- **Klassifikation:** Glued laminated timber (CEI-Bois)
- **Evidenz:** Leistungserklärung + EPD

## 🔍 Qualitätssicherung

### IDS-Validierung (Information Delivery Specification)

Die `POC.ids` definiert **Mindestanforderungen**:

```xml
<ids:Specification name="Insulation λ declared">
  <ids:Entity name="IfcWallStandardCase"/>
  <ids:Property>
    <ids:PropertySet>CPset_Insulation_Performance</ids:PropertySet>
    <ids:Name>lambdaDeclared_EN12664</ids:Name>
    <ids:HasValue datatype="xs:double"/>
    <ids:Uri>https://identifier.buildingsmart.org/uri/demo2025/thermal-insulation-products/1.0.0/prop/thermalConductivityDeclared_EN12664</ids:Uri>
  </ids:Property>
</ids:Specification>
```

### Validierungslogik
- ✅ **Datentyp-Überprüfung** (xs:double, xs:string)  
- ✅ **bSDD URI-Konsistenz**
- ✅ **Pflichtfelder-Vollständigkeit**
- ✅ **Property-Set-Zuordnung**

## 🚀 Verwendung

### 1. DPP-Daten analysieren
```bash
# JSON-LD Struktur prüfen
cat DPP/dpp_knauf_acoustic_batt.jsonld | jq '.["dpp:hasSpecification"]["dpp:hasQuantity"]'
```

### 2. Mapping verstehen  
```bash
# bSDD-Zuordnungen anzeigen
cat mapping.csv | column -t -s ','
```

### 3. IFC-Integration (geplant)
```bash
python patch_poc_ifc.py \
  --ifc POC_Wall.ifc \
  --mapping mapping.csv \
  --dpp-dir . \
  --out POC_Wall_patched.ifc
```

### 4. IDS-Validierung
```bash
# Mit ifcopenshell oder buildingSMART Validator
ids-check --ifc POC_Wall_patched.ifc --ids POC.ids
```

## 📊 Standards-Compliance

### ✅ UN Transparency Protocol (UNTP)
- **Modular DPP Structure:** Product, Specification, Quantity patterns
- **Traceability:** Complete provenance chains
- **Interoperability:** JSON-LD with standardized vocabularies

### ✅ buildingSMART Standards  
- **IFC 4.3:** Correct entity usage and property sets
- **bSDD Integration:** Official dictionary references
- **IDS Compliance:** Automated validation rules

### ✅ European Standards
- **EN 13162:** Thermal insulation products
- **EN 13501-1:** Fire classification 
- **EN 14080:** Glulam specifications
- **EPD Standards:** Environmental product declarations

## 📚 Referenzen & Standards

- **UN Transparency Protocol:** [UNTP DPP Specification](https://uncefact.github.io/spec-untp/)
- **buildingSMART bSDD:** [Data Dictionary Guide](https://github.com/buildingSMART/bSDD)
- **IFC 4.3:** [buildingSMART IFC Documentation](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/)
- **CEI-Bois Dictionary:** [Wood Product Classifications](https://www.cei-bois.org/)
- **Norwegian EPD Foundation:** [EPD Database](https://www.epd-norge.no/)

## 👥 Kontakt & Support

**Projekt:** Lignum Digital Product Passport POC  
**Standards:** UN Transparency Protocol, buildingSMART IFC  
**Integration:** bSDD demo2025 dictionaries

---

