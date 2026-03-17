# Schema Comparison: lignum-dpp-bsdd vs DPP Keystone

> Comprehensive diff of the lignum-dpp-bsdd schema (prEN 18216–18223) against the
> [DPP Keystone Ontology v1](https://github.com/dpp-keystone-org/DPPKeystoneOrg).

---

## 1. Foundational Architecture

| Aspect | lignum-dpp-bsdd | DPP Keystone |
|--------|----------------|--------------|
| **Format** | JSON-LD documents + OpenAPI 3.0 YAML + OWL ontology + SHACL shapes | OWL/RDFS ontology in JSON-LD + JSON Schema + SHACL shapes |
| **Namespace** | `dpp: https://w3id.org/dpp#` | `dppk: https://dpp-keystone.org/spec/v1/terms#` |
| **Vocabulary approach** | Reuses dcterms, schema.org, prov, bSDD URIs directly | Defines own `dppk:` terms with `owl:equivalentProperty`/`owl:equivalentClass` mappings to schema.org, GS1, UNECE |
| **Validation** | OpenAPI 3.0 + SHACL shapes + Pydantic (Python) + IDS (XML) | JSON Schema + SHACL shapes (dual validation) |
| **Modularity** | Flat: single OpenAPI spec + product JSON-LD files | Modular ontology: core modules (Header, Product, Organization, Compliance, EPD, Identifier, RelatedResource, DoPC) + sector modules (Battery, Textile, Construction, Electronics) |
| **Sector scope** | Construction-only (insulation, pipe, timber) | Multi-sector (Construction, Battery, Textile, Electronics, General Product, Packaging) |
| **Standards cited** | prEN 18216–18223, ISO 22057, EN 15804 | ESPR (Ecodesign for Sustainable Products Regulation), EN 15804, CPR |
| **Linked Data** | JSON-LD with `@context` in each document | JSON-LD contexts per sector (`dpp-core.context.jsonld`, `dpp-construction.context.jsonld`, `dpp-epd.context.jsonld`, etc.) |
| **Tooling** | FastAPI server, IFC patcher, QR code generator | Validator, Explorer, Wizard, CSV adapter, HTML generator, Schema adapter |
| **IFC integration** | Yes (patch_ifc.py, IDS specs, bSDD→IFC property mapping) | No IFC integration |
| **bSDD integration** | Deep (every property has bSDD URI, classification references) | None (defines own property URIs under `dppk:` namespace) |

---

## 2. DPP Header / Envelope

### 2.1 Identification

| Field | lignum-dpp-bsdd | DPP Keystone | Difference |
|-------|----------------|--------------|------------|
| DPP ID | `"id"` / `"@id"` using `did:web:` URIs | `digitalProductPassportId` (string, URI format) | **Different ID scheme**: lignum uses DID:web; Keystone uses plain URIs |
| Type declaration | `"type": "dpp:DigitalProductPassport"` | `"@type": "DigitalProductPassport"` (via context) | Keystone omits explicit namespace prefix in instances |
| Product ID | `dpp:productIdentifiers` array of `{scheme, value, namespace}` | `uniqueProductIdentifier` — single URI string | **Structural**: lignum supports multiple typed identifiers; Keystone has one primary URI |
| Economic Operator | `dpp:economicOperator` → embedded Organization object | `economicOperatorId` → URI reference (string) | **Depth**: lignum embeds full org; Keystone references by ID |
| Backup Operator | `dpp:backupOperator` (optional embedded Organization) | Not present | **Missing in Keystone** |
| Facility | Not in header (appears in product body) | `facilityId` → URI reference | **Different placement** |
| Granularity | `dpp:granularity` enum: `model`, `batch`, `item` (lowercase) | `granularity` enum: `Model`, `Batch`, `Item` (capitalized) | **Case difference** in enum values |
| Status | `dpp:status` enum: `active`, `inactive`, `archived` | `dppStatus` (string, no enum constraint) | **lignum constrains** to 3 values; Keystone is open string |
| Schema version | `dpp:dppSchemaVersion` | `dppSchemaVersion` | Equivalent |
| Language | `dcterms:language` (e.g., `"de-CH"`) | Not in header schema | **Missing in Keystone header** |
| Created date | `dcterms:created` (ISO 8601) | Not present | **Missing in Keystone** |
| Modified date | `dcterms:modified` (ISO 8601) | `lastUpdate` (date-time) | **Different property name** |
| HS Code | Not present | `hsCode` (string) | **Missing in lignum** |
| Content Spec IDs | Not present | `contentSpecificationIds` (array of strings) | **Missing in lignum** |
| Version Number | Not present (uses changeLog) | `versionNumber` (string) | **Missing in lignum** |
| Version Date | Not present | `versionDate` (date) | **Missing in lignum** |
| Labels/Tags | `dpp:labels` (array of strings) | Not present | **Missing in Keystone** |
| Registry info | `dpp:registry` (object with registryUrl, registryId) | Not present | **Missing in Keystone** |
| Conforms To | `dcterms:conformsTo` (array of standard URIs) | Not present | **Missing in Keystone** |

### 2.2 Required Fields

| Schema | Required Fields |
|--------|----------------|
| **lignum** | Not formally enforced (OpenAPI marks some as required in POST) |
| **Keystone** | `digitalProductPassportId`, `uniqueProductIdentifier`, `granularity`, `dppSchemaVersion`, `dppStatus`, `lastUpdate`, `economicOperatorId`, `contentSpecificationIds` |

---

## 3. Organization Model

| Field | lignum-dpp-bsdd | DPP Keystone | Difference |
|-------|----------------|--------------|------------|
| Type | `schema:Organization` | `dppk:Organization` (≡ schema:Organization) | Namespace differs |
| Name | `schema:name` | `organizationName` | **Different property** |
| Trading name | Not present | `tradingName` | **Missing in lignum** |
| LEI | `dpp:lei` | `leiCode` | **Different property name** |
| GLN | `dpp:gln` | `gln` | Similar |
| Additional ID | Not present | `additionalOrganizationId` + `additionalOrganizationIdType` | **Missing in lignum** (no EORI/VAT support) |
| Address | Not present (org is minimal) | Full `PostalAddress` object (street, postal code, locality, country) | **Missing in lignum** |
| Contact | Not present | `email`, `telephone`, `website` | **Missing in lignum** |
| Roles | Not modeled | `EconomicOperatorRole`, `ManufacturerRole`, `FacilityRole`, `ConformityAssessmentBodyRole` | **Keystone has role-based organization modeling** |
| Required | — | Only `organizationName` required | — |

---

## 4. Product Model

| Field | lignum-dpp-bsdd | DPP Keystone | Difference |
|-------|----------------|--------------|------------|
| Class | No explicit Product class (product data in DPP body) | `dppk:Product` (≡ schema:Product, gs1:Product) | **Keystone has formal Product class** |
| Product name | Implicit in DPP metadata | `productName` (multilingual, `@language` container) | **Missing formal property in lignum** |
| Description | Not present as formal field | `description` (multilingual) | **Missing in lignum** |
| GTIN | In `productIdentifiers[scheme="gtin"]` | `gtin` (dedicated property ≡ schema:gtin) | **Different structure** |
| Brand | Not present | `brand` | **Missing in lignum** |
| Model | Not present | `model` | **Missing in lignum** |
| Image | Not present | `image` (URI) | **Missing in lignum** |
| Color | Not present (only in pipe properties) | `color` | **Missing as formal product property in lignum** |
| Country of origin | Not present | `countryOfOrigin` | **Missing in lignum** |
| Physical dimensions | Not present (in property collections) | `length`, `width`, `height`, `depth`, `netWeight`, `grossWeight` | **Keystone has formal dimension properties** |
| Components | Not modeled | `dppk:Component` class with `components`, `percentage` | **Missing in lignum** |
| Recycled content | Not present | `recycledContentPercentage` | **Missing in lignum** |
| Product characteristics | Via `dpp:DataElementCollection` / `dpp:DataElement` | `dppk:ProductCharacteristic` with `characteristicName`, `characteristicValue`, `testMethod` | **Fundamentally different**: lignum uses generic data elements; Keystone uses typed characteristics |
| QuantitativeValue | `dpp:ValueElement` with `numericValue`, `textValue`, `unit` | `dppk:QuantitativeValue` with `value`, `unitCode`, `unitText` | **Different property names**, same concept |

---

## 5. Data Element Architecture (Fundamental Difference)

This is the **most significant structural difference** between the two schemas.

### lignum-dpp-bsdd: Generic Data Element Model

```text
DigitalProductPassport
  └── dpp:dataElementCollections[]
        ├── id (fragment ID)
        ├── dcterms:title
        ├── dpp:labelSet[]
        └── dpp:elements[]
              ├── dpp:path (hierarchical path)
              ├── dpp:name
              ├── dpp:dictionaryReference (bSDD URI)
              ├── dpp:value (flexible: object/array/string)
              └── dpp:valueElement
                    ├── dpp:numericValue
                    ├── dpp:textValue
                    └── dpp:unit
```

### DPP Keystone: Typed Property Model

```text
DigitalProductPassport
  ├── Product (formal class)
  │     ├── productName, description, gtin, brand, model...
  │     ├── productCharacteristics[]
  │     │     ├── characteristicName
  │     │     ├── characteristicValue (QuantitativeValue)
  │     │     └── testMethod
  │     └── components[]
  ├── epd (EPDBlock)
  │     ├── gwp → ImpactValues {a1..d, total}
  │     ├── odp → ImpactValues {a1..d, total}
  │     └── ... (14 indicators)
  ├── dopc (DoPCBlock)
  │     ├── declarationCode, dateOfIssue
  │     └── performance properties...
  └── Organization roles
```

**Key implications:**
- **lignum** is schema-agnostic: any property can go in any collection, linked via bSDD URIs
- **Keystone** is schema-prescriptive: each property has a defined place in the ontology hierarchy
- **lignum** relies on external dictionaries (bSDD) for semantics; **Keystone** embeds semantics in the ontology itself

---

## 6. EPD / Environmental Data

| Aspect | lignum-dpp-bsdd | DPP Keystone | Difference |
|--------|----------------|--------------|------------|
| **Structure** | Flat collection: `epd` DataElementCollection with nested elements for header, methodology, LCIA, LCI | Typed ontology: `EPDBlock` → indicator properties → `ImpactValues` per lifecycle stage | **Fundamentally different structure** |
| **EPD metadata** | `epdHeader` with ID, validity dates, program operator | Not in EPD block (separate compliance module) | **lignum has richer EPD metadata** |
| **Methodology** | `methodology` element with standard, modules, scenarios | Not formally modeled | **Missing in Keystone** |
| **Declared/Functional unit** | In EPD header element | In DoPC block (`declaredUnit`, `functionalUnit`) | **Different location** |

### 6.1 LCIA Indicators

| Indicator | lignum-dpp-bsdd | DPP Keystone |
|-----------|----------------|--------------|
| GWP-total | `GWP-total` (in elements) | `gwp` → `{a1..d, total}` |
| GWP-fossil | `GWP-fossil` | `gwpF` |
| GWP-biogenic | `GWP-biogenic` | `gwpB` |
| GWP-LULUC | Not present | `gwpLuluc` |
| GWP-GHG | Not present | `gwpGhg` |
| ODP | `ODP` | `odp` |
| AP | `AP` | `ap` |
| EP-freshwater | `EP-freshwater` | `epF` |
| EP-marine | `EP-marine` | `epM` |
| EP-terrestrial | `EP-terrestrial` | `epT` |
| POCP | `POCP` | `pocp` |
| ADPE | `ADPE` | `adpe` |
| ADPF | `ADPF` | `adpf` |
| WDP | Not present | `wdp` (Water Depletion Potential) |

**Differences:**
- **Keystone has 2 more indicators**: `gwpLuluc` (GWP Land Use), `gwpGhg` (GWP Greenhouse Gas), `wdp` (Water Depletion)
- **lignum has LCI indicators** (resource use): PERE, PERM, PERT, PENRE, PENRM, PENRT, SM, RSF, NRSF, FW, HWD, NHWD, RWD, CRU, MFR, MER, EEE, EET — **none of these exist in Keystone**
- **Lifecycle stage modeling**: Keystone models each indicator with per-stage values (a1–d, total); lignum stores aggregated values (typically A1-A3 totals) or per-module values as separate data elements

---

## 7. Construction-Specific Features

| Feature | lignum-dpp-bsdd | DPP Keystone | Difference |
|---------|----------------|--------------|------------|
| **Construction class** | No formal class (uses bSDD classification) | `dppk:ConstructionProduct` (formal OWL class) | **Keystone has dedicated class** |
| **DoP** | `dpp:DeclarationOfPerformance` OWL class + `#dopc` DataElementCollection with `dpp:dopcMetadata` | `dppk:DeclarationOfPerformance` class + `dppk:DoPCBlock` with extensive properties | **Both have DoPC support; different structure** |
| **DoP identifier** | `dpp:declarationCode` in dopcMetadata | `dopIdentifier` | **Both present, different property name** |
| **Harmonised standard** | `dpp:harmonisedStandard` in dopcMetadata | `harmonisedStandardReference` (URI) | **Both present, different property name** |
| **AVCP system** | `dpp:avcpSystem` enum ["1","1+","2","2+","3","4"] in dopcMetadata | `avsSystem` | **Both present** |
| **Notified body** | `dpp:notifiedBody` in dopcMetadata (string) | `notifiedBody` → Organization | **Both present; Keystone links to Organization object** |
| **Technical assessment body** | Not present | `technicalAssessmentBody` → Organization | **Missing in lignum** |
| **Validation reports** | Not present | `validationReports` → array of RelatedResource | **Missing in lignum** |
| **European Assessment Document** | Not present | `europeanAssessmentDocument` → RelatedResource | **Missing in lignum** |
| **Reaction to fire** | DoPC data element with bSDD URI + AVCP system in metadata | `reactionToFire` (linked to QuantitativeValue) + detailed AVCP system 1-4 | **Both have it, different structure** |
| **Thermal conductivity** | DoPC + product properties data elements with bSDD URI | `thermalConductivity` → QuantitativeValue | **Both have it, different structure** |
| **Compressive strength** | DoPC data element with bSDD URI | `compressiveStrength` → QuantitativeValue | **Both have it, different structure** |
| **DoPC material testing** | 33 DoPC properties across 3 product types (insulation: 10, timber: 13, pipe: 10) with bSDD URIs | Extensive: chloride content, bond strength, thermal compatibility, elastic recovery, carbonation resistance, flow resistance, slip/skid resistance, shrinkage/expansion, modulus of elasticity | **Both have extensive DoPC properties; different coverage areas** |
| **Steel/rail properties** | Not present | `steelGrade`, `railProfile` | **Missing in lignum** (different product scope) |
| **Timber properties** | `strengthClass`, `density`, `moistureContent`, `adhesiveType` | Not present | **Missing in Keystone** |
| **Pipe properties** | `nominalDiameter`, `materialType`, `ringStiffness`, `vacuumStiffness`, `pipeType`, `applicationArea` | Not present | **Missing in Keystone** |
| **Insulation properties** | `thermalConductivity`, `density`, `waterVapourResistivity`, `airFlowResistivity`, `dimensionalStability`, `longTermWaterAbsorption` | Only `thermalConductivity`, `compressiveStrength` | **lignum has more insulation-specific properties** |

---

## 8. Compliance & Certification

| Feature | lignum-dpp-bsdd | DPP Keystone |
|---------|----------------|--------------|
| Certification class | Not present (documents linked as RelatedResource) | `dppk:Certification` (≡ schema:Certification) with `certificationBodyName`, `certificationBodyId`, `certificationStartDate` |
| Substances of Concern | Not present | `dppk:SubstanceOfConcern` with `substanceName`, `casNumber`, `concentration`, `minValue`, `maxValue` |
| Packaging | Not present | `dppk:Packaging` with `packagingMaterialType`, `packagingRecycledContent`, `packagingRecyclingProcessType` |
| Production steps | Not present | `dppk:ProductionStep` with `productionStepType`, `productionLocationCountry` |
| Dangerous substances | Not present | Via SubstanceOfConcern class |

**Keystone has an entire compliance module missing from lignum.**

---

## 9. Document / Resource Linking

| Feature | lignum-dpp-bsdd | DPP Keystone |
|---------|----------------|--------------|
| Model | `dpp:Document` type within DataElementCollections | `dppk:RelatedResource` class |
| Properties | `dpp:name`, `dpp:value` (URL), type inference from URL patterns | `resourceTitle`, `url`, `contentType` (MIME), `language` |
| Specialized links | Generic document references | `instructionsForUse`, `safetyDataSheet` (dedicated properties) |
| Content type | Not explicitly modeled | `contentType` (MIME type) |
| Language | Not per-document | `language` per resource |

---

## 10. Audit Trail / Change Management

| Feature | lignum-dpp-bsdd | DPP Keystone |
|---------|----------------|--------------|
| Change log | `dpp:changeLog` array of `dpp:ChangeEvent` | Not present |
| Change ID | `dpp:changeId` (UUID) | — |
| Timestamp | `dpp:timestamp` (ISO 8601) | — |
| Actor | `dpp:actor` (Agent object) | — |
| Change type | `dpp:changeType` enum: create, update, delete | — |
| Changed properties | `dpp:changedProperties` array | — |

**lignum has a full audit trail model; Keystone has none.**

---

## 11. API & Access Layer

| Feature | lignum-dpp-bsdd | DPP Keystone |
|---------|----------------|--------------|
| REST API | Full CRUD (prEN 18222:2025 conformant) | No API defined |
| GS1 Digital Link resolver | Yes (`/id/01/{gtin}`, `/id/01/{gtin}/21/{serial}`) | No |
| Registry integration | `POST /registerDPP` | No |
| Content negotiation | JSON-LD / JSON / HTML | N/A (static files) |
| Pagination | Cursor-based on list endpoint | N/A |
| PATCH support | JSON Merge Patch (RFC 7396) | N/A |

**lignum has a complete API; Keystone is ontology/vocabulary only.**

---

## 12. IFC / BIM Integration

| Feature | lignum-dpp-bsdd | DPP Keystone |
|---------|----------------|--------------|
| IFC patching | Yes (Python tool, 1179 lines) | No |
| IDS validation | Yes (3 specifications for insulation, pipe, timber) | No |
| Custom Property Sets | `CPset_InsulationPerformance`, `CPset_PipePerformance`, `CPset_TimberPerformance`, `CPset_EpdIndicators` | No |
| bSDD property linking | Yes (via IfcExternalReference) | No |
| IFC classification | Yes (IfcClassification → bSDD dictionary) | No |

**lignum has deep BIM/IFC integration; Keystone has none.**

---

## 13. Identifier Systems

| Scheme | lignum-dpp-bsdd | DPP Keystone |
|--------|----------------|--------------|
| DID:web | Primary ID format | Not used |
| Plain URI | Supported | Primary ID format |
| GTIN | In productIdentifiers array | `gtin` property or `uniqueProductIdentifier` URI |
| MPN | In productIdentifiers array | `model` property |
| LEI | `dpp:lei` on Organization | `leiCode` on Organization |
| GLN | `dpp:gln` on Organization | `gln` on Organization |
| EPD ID | In productIdentifiers array | Not a product identifier |
| EORI / VAT | Not supported | `additionalOrganizationId` + type |
| Custom IDs | `productIdentifiers[scheme="custom"]` with namespace | Not present |
| GS1 Digital Link | Full resolver support | Not present |

---

## 14. Multilingual Support

| Feature | lignum-dpp-bsdd | DPP Keystone |
|---------|----------------|--------------|
| DPP-level language | `dcterms:language` (single language tag) | Not in header |
| Property labels | Not multilingual (English only) | 24 EU languages on ontology labels/comments |
| Product name | Single language | `@language` container (multilingual) |
| Instance data | Monolingual per DPP | Multilingual per field |

**Keystone has much richer multilingual support at the ontology and instance level.**

---

## 15. External Vocabulary Alignment

| Vocabulary | lignum-dpp-bsdd | DPP Keystone |
|------------|----------------|--------------|
| schema.org | Used directly (`schema:Organization`, `schema:name`) | Mapped via `owl:equivalentClass`/`owl:equivalentProperty` |
| Dublin Core | Used directly (`dcterms:created`, `dcterms:title`) | Referenced in ontology namespace |
| W3C PROV | Used (`prov:`) | Not used |
| GS1 | Not referenced in ontology | Extensive equivalence mappings (`gs1:Product`, `gs1:CertificationDetails`) |
| UNECE | Not referenced | Equivalence mappings (`unece:certificationEvidenceDocument`) |
| bSDD | **Core integration** — every property linked to bSDD URI | **Not used at all** |
| QUDT | Not used | Referenced for units |
| EUDPP | Not referenced | Equivalence mappings to EU DPP regulation terms |

---

## 16. Sector-Specific Modules (Keystone-only)

DPP Keystone defines four sector modules with no equivalent in lignum-dpp-bsdd:

### 16.1 Battery Sector (~90+ properties)

| Class | Description |
|-------|-------------|
| `dppk:BatteryProduct` | Battery product (EU Battery Regulation 2023/1542) |
| `dppk:BatteryPerformance` | Performance data container |
| `dppk:CapacityInfo` | ratedCapacity, remainingCapacity, capacityFade, capacityThroughput |
| `dppk:EfficiencyInfo` | roundTripEfficiencyInitial, at50Cycles, fade, remaining |
| `dppk:InternalResistanceInfo` | initial, increase |
| `dppk:PowerInfo` | original, remaining, fade, maximumPermitted, energyRatio |
| `dppk:LifetimeInfo` | expectedLifetimeCycles, expectedLifetimeYears, cycleCountFull, energyThroughput |
| `dppk:TemperatureInfo` | idle/charging/extreme temperature lower/upper bounds |
| `dppk:NegativeEventsInfo` | accidents, deepDischarge, overcharge event counts |

**Key battery properties**: batteryCategory, batteryChemistry, batteryMass, batteryStatus, manufacturingDate/Place, voltageNominal/Min/Max, stateOfCharge, carbonFootprintAbsolute/Class/Label, materialComposition, criticalRawMaterials, hazardousSubstances, recycled content (pre/post consumer), dismantlingInformation, safetyMeasures, extinguishingAgent, warrantyPeriod, dueDiligenceReport, supplyChainAssurances.

### 16.2 Textile Sector (~13 properties)

| Class | Description |
|-------|-------------|
| `dppk:TextileProduct` | subClassOf Product (EU Reg 1007/2011) |
| `dppk:FibreComposition` | fibreType + fibrePercentage |

**Properties**: fibreComposition, animalOriginNonTextile, tearStrength (ISO 13937-2), abrasionResistance (ISO 12947), dimensionalStability (ISO 5077), colorfastnessToWashing (ISO 105-C06), microplasticRelease (ISO 4484-1), careInstructions (ISO 3758), repairabilityInformation, apparelSize, apparelSizeSystem.

### 16.3 Electronics Sector (~11 properties)

| Class | Description |
|-------|-------------|
| `dppk:ElectronicDevice` | subClassOf Product (WEEE 2012/19/EU) |
| `dppk:PowerTool` | subClassOf ElectronicDevice |

**Properties**: voltage, ratedPower, energyEfficiencyClass, ipRating, sparePartsAvailable, serviceManualAvailable, softwareUpdatePolicy, weeeCategory, disassemblyInstructions, torque (PowerTool), maximumRatedSpeed (PowerTool).

### 16.4 Packaging Sector

Integrated into core compliance module (see Section 8). Properties: packagingMaterialType, packagingMaterialCompositionQuantity, packagingRecyclingProcessType, packagingRecycledContent, packagingSubstanceOfConcern.

**None of these sector modules exist in lignum-dpp-bsdd, which focuses exclusively on construction products.**

---

## 17. Annotation & Metadata Properties

| Feature | lignum-dpp-bsdd | DPP Keystone |
|---------|----------------|--------------|
| `governedBy` annotation | Not present | `dppk:governedBy` — links properties to governing standards |
| `unit` annotation | Inline in ValueElement | `dppk:unit` — annotation property on ontology terms |
| `unitInherited` flag | Not present | `dppk:unitInherited` — boolean: unit inherited from parent indicator |
| Custom datatypes | Not present | `dppk:KgWeightLiteral`, `dppk:MetersLengthLiteral` (subClassOf xsd:double) |
| SKOS annotations | Not used | SKOS referenced in namespace |

---

## 18. Summary of Key Differences

### What lignum-dpp-bsdd has that Keystone lacks:
1. **bSDD integration** — deep linking to buildingSMART Data Dictionary
2. **IFC/BIM integration** — property patching, IDS validation, classification
3. **REST API** — full CRUD with prEN 18222 conformance
4. **GS1 Digital Link resolver** — carrier/QR code infrastructure
5. **Audit trail** — complete change log with actor, timestamp, change type
6. **Registry integration** — EU DPP registry registration endpoint
7. **Backup operator** concept
8. **LCI resource indicators** — PERE, PERM, PERT, PENRE, etc. (18 indicators)
9. **DID:web identifiers**
10. **Multi-scheme product identifiers** — GTIN, MPN, EPD, custom with namespaces
11. **Construction sub-domains** — timber (GL24h, moisture, adhesive), pipe (DN, ring stiffness, vacuum), insulation (air flow resistivity, water vapor)
12. **EPD metadata** — program operator, validity dates, methodology, scenarios
13. **Content negotiation** — JSON-LD / JSON / HTML responses
14. **DPP labels/tags** system

### What DPP Keystone has that lignum lacks:
1. ~~**Formal OWL ontology**~~ — ✅ **Now implemented**: `ontology/dpp-ontology.jsonld` with 21 classes, 16 object properties, 30 datatype properties
2. **Multi-sector coverage** — Battery (~90+ properties), Textile (~13 properties), Electronics (~11 properties), Packaging
3. ~~**SHACL validation shapes**~~ — ✅ **Now implemented**: `ontology/dpp-shacl.jsonld` with 9 node shapes including DeclarationOfPerformance validation
4. ~~**DoPC (Declaration of Performance and Conformity)**~~ — ✅ **Now implemented**: 33 DoPC test properties across 3 product types (insulation: 10 EN 13162, timber: 13 EN 14080, pipe: 10 EN 1401-1) with bSDD URIs and provenance
5. **Substances of Concern** — SVHC/dangerous substance tracking with CAS numbers, concentration, min/max values
6. **Packaging model** — material type, recycled content, recycling process, packaging substance of concern
7. **Production steps** — type and location tracking (ISO 3166-1 alpha-3)
8. **Certification model** — formal class with body name, ID, start date
9. **Component/BOM model** — components with percentages, recycled content
10. **Rich Organization model** — postal address (street, postal code, locality, country), contact details (email, telephone, website), trading name, EORI/VAT
11. **Role-based organization** — EconomicOperator, Manufacturer, Facility, ConformityAssessmentBody roles
12. **Multilingual support** — 24 EU languages on ontology labels, `@language` containers on instance data
13. **HS Code** — customs tariff classification
14. **Content Specification IDs** — delegated act references
15. **Version management** — versionNumber + versionDate fields
16. **Formal Product class** — dedicated properties for brand, model, image, color, dimensions (length/width/height/depth), netWeight, grossWeight, countryOfOrigin
17. **GS1/UNECE/EUDPP alignment** — equivalence mappings to multiple international vocabularies
18. **Water Depletion Potential** (WDP) indicator
19. **GWP-LULUC and GWP-GHG** sub-indicators
20. **Wizard/validator/explorer tools** for DPP creation and validation
21. **Instructions for Use** and **Safety Data Sheet** as dedicated link types
22. **QUDT unit references** for measurement units
23. ~~**Notified Body**~~ ✅ **Now implemented** and **Technical Assessment Body** references
24. **European Assessment Document** references
25. ~~**Harmonised Standard Reference**~~ ✅ **Now implemented** as `dpp:harmonisedStandard` in dopcMetadata
26. **Battery sector** — full EU Battery Regulation coverage: capacity, efficiency, internal resistance, power, lifetime, temperature ranges, negative events, voltage specs, state of charge, carbon footprint, material composition, critical raw materials, dismantling info, safety measures
27. **Textile sector** — fibre composition, tear strength, abrasion resistance, dimensional stability, colorfastness, microplastic release, care instructions, repairability, apparel sizing
28. **Electronics sector** — voltage, rated power, energy efficiency class, IP rating, spare parts availability, WEEE category, disassembly instructions, software update policy, power tool properties (torque, max speed)
29. **Custom datatypes** — `KgWeightLiteral`, `MetersLengthLiteral` for type-safe measurements
30. **`governedBy` annotation** — links properties to their governing standards directly in the ontology
31. **9 JSON-LD context files** — sector-specific contexts for clean instance data
32. **13 JSON Schema files** — per-module validation schemas with conditional application (e.g., construction schema triggers when `contentSpecificationIds` contains `draft_construction_specification_id`)
