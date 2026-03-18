# Digital Product Passport (DPP) Proof of Concept

## 🎯 Overview

This repository contains a mock implementation of Digital Product Passports (DPP) for construction products, fully conforming to the draft European standards (prEN 18216-18223) and ISO 22057:2022 for machine-readable EPD data.

## 📋 Standards Conformance

This PoC implements:

- **prEN 18223:2025** - System Interoperability and Data Model
- **prEN 18222:2025** - API specification  
- **prEN 18221:2025** - Storage, Archiving & Persistence
- **prEN 18220:2025** - Data Carriers (QR codes)
- **prEN 18219:2025** - Unique Identifiers (DIDs, GS1)
- **prEN 18216:2025** - Data Exchange Protocols (JSON-LD, HTTPS)
- **ISO 22057:2022**  - Data templates for EPD in BIM

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                    DPP System Architecture             │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────┐     ┌──────────────┐                 │
│  │  JSON-LD     │────▶│   REST API   │                 │
│  │   DPP Files  │     │  (FastAPI)   │                 │
│  └──────────────┘     └──────────────┘                 │
│         │                     │                        │
│         ▼                     ▼                        │
│  ┌──────────────┐     ┌──────────────┐                 │
│  │  QR Codes    │     │  HTML View   │                 │
│  │  (Carriers)  │     │  (Human UI)  │                 │
│  └──────────────┘     └──────────────┘                 │
│                                                        │
│  ┌───────────────────────────────────┐                 │
│  │        EU Registry Interface      │                 │
│  └───────────────────────────────────┘                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
openDPP/
├── api/
│   ├── main.py                      # FastAPI server
│   └── requirements.txt             # Python dependencies
├── data/                            # Documents served via /files (EPD/DoP/etc.)
├── docs/
│   ├── README_DEMO.md               # Demo walkthrough (localhost)
│   ├── openapi.yaml                 # OpenAPI 3.0 specification
│   └── comparison-dpp-keystone.md   # Schema comparison with DPP Keystone
├── dpp/
│   └── products/                    # DPP JSON-LD documents (served)
├── ifc/
│   ├── samples/                     # Input IFCs
│   ├── outputs/                     # Patched IFCs
│   ├── ids/                         # IDS definitions
│   └── tools/                       # IFC utilities (patch_ifc.py)
├── mapping/
│   └── mapping.csv                  # Property → IFC mapping with bSDD URIs
├── ontology/
│   ├── dpp-ontology.jsonld          # Formal OWL ontology (JSON-LD)
│   └── dpp-shacl.jsonld             # SHACL validation shapes
├── qr_codes/                        # Generated QR images + index.html
│   └── tools/
│       └── generate_qr_codes.py     # QR code generator
├── run_demo.sh                      # One‑command demo runner
└── README.md                        # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install API dependencies
cd api
pip install -r requirements.txt
cd ..

# Install QR code generator dependencies
pip install qrcode pillow
```

### 2. Start the API Server

```bash
cd api
python main.py
```

The API will be available at:
- API endpoints: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json
 
Hot‑reload DPPs after editing files (no restart):
```bash
curl -X POST http://localhost:8000/admin/reload
```

### 3. Generate QR Codes

```bash
python qr_codes/tools/generate_qr_codes.py
```

View generated QR codes by opening `qr_codes/index.html` in a browser.

## 📊 Sample DPPs

The PoC includes three fully compliant DPPs:

1. **Knauf Acoustic Batt** - Insulation product with thermal properties
2. **Schilliger Glulam** - Engineered timber with EPD data
3. **PVC Sewage Pipe** - Infrastructure product with full lifecycle data

## 🔑 Key Features

### DPP Structure (prEN 18223)

Each DPP includes:
- **Header**: DPP ID, status, schema version, timestamps
- **Economic Operator**: Organization with LEI/GLN identifiers
- **Product Identifiers**: GTIN, MPN, custom IDs
- **Data Collections**:
  - Product properties with bSDD references
  - Full EPD data (ISO 22057 compliant)
  - Linked documents with hash verification (served from `data/` via `/files`)
  - Data carrier information
- **Change Log**: Full audit trail of modifications

### REST API (prEN 18222)

Core endpoints:
- `POST /dpps` - Create new DPP
- `GET /dpps/{dppId}` - Read DPP (JSON-LD or HTML)
- `PATCH /dpps/{dppId}` - Update using JSON Merge Patch
- `DELETE /dpps/{dppId}` - Delete DPP
- `GET /dppsByProductId/{productId}` - Find by product ID
- `POST /registerDPP` - Register with EU registry

### Identifiers (prEN 18219)

Supports multiple identifier schemes:
- **DID:web** - Decentralized identifiers for DPPs
- **GS1 GTIN** - Global Trade Item Numbers
- **LEI** - Legal Entity Identifiers
- **GLN** - Global Location Numbers

### Data Carriers (prEN 18220)

QR codes encode:
- GS1 Digital Links (localhost): `http://localhost:8000/id/01/{GTIN}/21/{SERIAL}` or `.../10/{BATCH}`
- DID resolver URLs (localhost): `http://localhost:8000/dpps/did:web:...`

## 📈 EPD Data (ISO 22057)

Each DPP includes comprehensive EPD data:

### LCIA Indicators (EN 15804+A2)
- GWP (total, fossil, biogenic, luluc)
- ODP, AP, EP (freshwater, marine, terrestrial)
- POCP, ADPE, ADPF

### LCI Indicators
- Energy use (PERE, PERM, PENRE, PENRM)
- Resource use (SM, RSF, NRSF, FW)
- Waste categories (HWD, NHWD, RWD)
- Output flows (CRU, MFR, MER, EEE, EET)

### Scenarios
- A4: Transport to site
- A5: Installation
- B1-B7: Use phase
- C1-C4: End of life
- D: Benefits beyond system boundary

## 🔒 Security & Persistence

- HTTPS with TLS 1.3
- JWT bearer tokens (ready for implementation)
- OAuth 2.0 support
- Document hash verification (SHA-256)
- Complete change log for audit trail

## 🧪 Testing the API

### Create a DPP

```bash
curl -X POST http://localhost:8000/dpps \
  -H "Content-Type: application/json" \
  -d @dpp/products/dpp_knauf_acoustic_batt.jsonld
```

### Read a DPP (JSON-LD)

```bash
curl http://localhost:8000/dpps/did:web:bsdd-dpp.dev:dpp:knauf-acoustic-batt-2025-001 \
  -H "Accept: application/ld+json"
```

### Read a DPP (HTML)

```bash
curl http://localhost:8000/dpps/did:web:bsdd-dpp.dev:dpp:knauf-acoustic-batt-2025-001 \
  -H "Accept: text/html"
```

### Register with EU Registry

```bash
curl -X POST http://localhost:8000/registerDPP \
  -H "Content-Type: application/json" \
  -d '{
    "dppId": "did:web:bsdd-dpp.dev:dpp:example-001",
    "productIdentifiers": [{"scheme": "gtin", "value": "04012345678901"}],
    "economicOperatorId": "did:web:example.com"
  }'
```

## 🎨 Human-Readable View

The API automatically generates HTML views for DPPs when accessed with `Accept: text/html`. Features:
- Clean, responsive design
- Organized data sections
- Indicator tables
- Document links
- QR code information

## 🔄 Version Management

Each DPP maintains:
- Creation timestamp
- Last modification timestamp
- Complete change log with:
  - Change ID (UUID)
  - Timestamp
  - Actor information
  - Changed properties
  - Change type (create/update/delete)

## 📝 Semantic Interoperability

All properties link to:
- **bSDD** (buildingSMART Data Dictionary)
- **ISO 23386/23387** property definitions
- **EN standards** for specific domains
 - IfcExternalReference + IfcExternalReferenceRelationship links for bSDD URIs
 - IfcDocumentInformation + IfcDocumentReference for EPD/DoP/DPP documents

## 🧬 OWL Ontology & SHACL Validation

### Formal Ontology (`ontology/dpp-ontology.jsonld`)

A complete OWL 2 ontology under the `dpp:` namespace (`https://w3id.org/dpp#`) defining:

- **21 classes**: DigitalProductPassport, Product (→ ConstructionProduct → InsulationProduct / TimberProduct / PipeProduct), Organization (→ EconomicOperator / NotifiedBody / TechnicalAssessmentBody), DataElementCollection, DataElement, ValueElement, DeclarationOfPerformance, Document, ChangeEvent, Agent, ProductIdentifier, Facility
- **16 object properties**: hasDataElementCollection, hasElement, hasValueElement, hasProductIdentifier, hasEconomicOperator, hasChangeLog, hasDoPC, etc.
- **30 datatype properties**: declarationCode, harmonisedStandard, avcpSystem, numericValue, textValue, unit, thermalConductivity, bendingStrength, ringStiffness, etc.
- **Equivalence mappings**: `dpp:Organization ≡ schema:Organization`, `dpp:Product ≡ schema:Product`

Served at `GET /ontology` as `application/ld+json`.

### SHACL Shapes (`ontology/dpp-shacl.jsonld`)

9 validation shapes conforming to prEN 18216-18223:
- DigitalProductPassportShape, OrganizationShape, ProductIdentifierShape
- DataElementCollectionShape, DataElementShape, ValueElementShape
- ChangeEventShape, **DeclarationOfPerformanceShape**, DocumentShape

Served at `GET /ontology/shacl` as `application/ld+json`.

## 🏛️ Declaration of Performance and Conformity (DoPC)

Each product DPP includes a `#dopc` DataElementCollection with `dpp:dopcMetadata` containing:
- Declaration code, date of issue, harmonised standard reference
- AVCP system (1, 1+, 2, 2+, 3, 4), notified body, intended use

### Product-Specific DoPC Properties

| Product | Standard | Properties |
|---------|----------|------------|
| **Knauf Acoustic Batt** | EN 13162:2012+A1:2015 | Thermal conductivity, thermal resistance, reaction to fire, water vapour resistance, compressive strength, dimensional stability, water absorption, sound absorption, tensile strength perpendicular, thickness tolerance |
| **Schilliger Glulam** | EN 14080:2013 | Strength class (GL24h), bending strength, tension parallel/perpendicular, shear strength, compression parallel/perpendicular, modulus of elasticity, density, reaction to fire, formaldehyde emission, moisture content, delamination resistance |
| **PVC Sewage Pipe** | EN 1401-1:2019 | Ring stiffness, impact resistance, wall thickness, chemical resistance, pressure rating, watertightness, longitudinal reversion, reaction to fire, internal pressure resistance, creep ratio |

All DoPC properties are linked to bSDD URIs and include provenance metadata referencing the source DoP document.

## 📚 References

- [ESPR Framework](https://ec.europa.eu/environment/eussd/smgp/PEFCR_OEFSR_en.htm)
- [prEN 18216-18223 Draft Standards](https://www.cencenelec.eu/)
- [ISO 22057:2022](https://www.iso.org/standard/72463.html)
- [buildingSMART Data Dictionary](https://www.buildingsmart.org/users/services/buildingsmart-data-dictionary/)
- [GS1 Digital Link](https://www.gs1.org/standards/gs1-digital-link)

---

**Note**: This is a proof-of-concept implementation. The prEN standards are drafts under enquiry and may change before final publication.
