# Lignum DPP PoC -- Demo Guide

This guide explains how to run the complete Digital Product Passport (DPP) PoC end-to-end.

The demo runs against the **deployed Vercel API** by default. Set `DPP_API_URL=http://localhost:8000` to use a local server instead.

**Deployed API:** https://lignum-dpp-bsdd.vercel.app

## Quick start (one command)

```bash
./run_demo.sh
```

The script will:
- Check the deployed API health (or start a local server if `DPP_API_URL=http://localhost:8000`)
- List existing DPPs
- Read a DPP (JSON-LD) and open its HTML view
- Resolve via GS1 Digital Link
- Verify linked PDFs under /files
- Generate QR codes (3 products) and open the QR gallery
- Create a new DPP, register it, then update it (RFC 7396)
- Optionally patch an IFC (if `POC.ifc` exists)
- Show how to validate with the existing `POC.ids` using external IDS tools

## Presenting live (manual step-by-step)

### 1) Browse the landing page
Open https://lignum-dpp-bsdd.vercel.app in a browser. Shows all sample products with links.

### 2) List DPPs
```bash
curl -s https://lignum-dpp-bsdd.vercel.app/dpps | python3 -m json.tool | sed -n '1,60p'
```

### 3) Read DPP (JSON-LD) and HTML view
```bash
curl -s -H 'Accept: application/ld+json' \
  https://lignum-dpp-bsdd.vercel.app/dpps/did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001 \
  | python3 -m json.tool | sed -n '1,40p'
```
Open HTML view in a browser:
- https://lignum-dpp-bsdd.vercel.app/dpps/did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001

### 4) GS1 Digital Link resolver (QR target)
```bash
curl -s -H 'Accept: application/ld+json' \
  https://lignum-dpp-bsdd.vercel.app/id/01/04012345678901/21/KI-AB-2025-001 \
  | python3 -m json.tool | sed -n '1,20p'
```

### 5) Linked documents (served via /files)
```bash
curl -I "https://lignum-dpp-bsdd.vercel.app/files/insul/Acoustic%20Batt%20Datasheet%20.pdf" | sed -n '1,3p'
curl -I "https://lignum-dpp-bsdd.vercel.app/files/bsh/EPD%20Schilliger_glued_laminated_timber_Glulam_as_per_EN_140802013.pdf" | sed -n '1,3p'
curl -I "https://lignum-dpp-bsdd.vercel.app/files/pipe/NEPD-3589-2252_PVC-Sewage-Pipe.pdf" | sed -n '1,3p'
```

### 6) QR codes (one per product)
```bash
python3 ./qr_codes/tools/generate_qr_codes.py
open ./qr_codes/index.html
```
QR codes point to the deployed API. Override with `DPP_API_URL=http://localhost:8000`.

### 7) Create, Register, Update a DPP
```bash
# Create (server assigns an ID)
NEW_DPP_JSON=./tmp_new_dpp.json
python3 - ./dpp/products/dpp_pvc_sewage_pipe.jsonld > "$NEW_DPP_JSON" <<'PY'
import json,sys
j=json.load(open(sys.argv[1])); j.pop('id', None)
print(json.dumps(j))
PY
CREATE_RESP=$(curl -s -X POST https://lignum-dpp-bsdd.vercel.app/dpps \
  -H 'Content-Type: application/ld+json' --data-binary @"$NEW_DPP_JSON")
NEW_ID=$(echo "$CREATE_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')
echo "New ID: $NEW_ID"

# Register
REG_PAYLOAD=$(NEW_ID="$NEW_ID" python3 - <<'PY'
import os,json
print(json.dumps({
  'dppId': os.environ['NEW_ID'],
  'productIdentifiers':[{'scheme':'gtin','value':'05790001234561'}],
  'economicOperatorId':'did:web:wavin.com'
}))
PY
)
curl -s -X POST https://lignum-dpp-bsdd.vercel.app/registerDPP \
  -H 'Content-Type: application/json' -d "$REG_PAYLOAD" | python3 -m json.tool | sed -n '1,20p'

# Update (RFC 7396 merge patch)
PATCH='{"dpp:status":"archived"}'
curl -s -X PATCH "https://lignum-dpp-bsdd.vercel.app/dpps/$NEW_ID" \
  -H 'Content-Type: application/merge-patch+json' -d "$PATCH" | python3 -m json.tool | sed -n '1,20p'
```

### 8) IFC patch
```bash
python3 ./ifc/tools/patch_ifc.py \
  --ifc ./ifc/samples/POC.ifc \
  --mapping ./mapping/mapping.csv \
  --dpp-dir ./dpp/products \
  --out ./ifc/outputs/POC_patched.ifc
```
Evidence URLs in the patched IFC point to the deployed API. Override with `DPP_API_URL=http://localhost:8000`.

### 9) IDS validation
- IDS: `./ifc/ids/POC.ids`
- IFC: `./ifc/outputs/POC_patched.ifc` (from step 8)
Use the official IDS validator or tools like BlenderBIM / BIMcollab to validate CPset_* properties.

## URLs to showcase in the browser
- Landing page: https://lignum-dpp-bsdd.vercel.app
- Swagger UI: https://lignum-dpp-bsdd.vercel.app/docs
- DPP HTML (Knauf): https://lignum-dpp-bsdd.vercel.app/dpps/did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001
- GS1 resolvers:
  - Knauf:  https://lignum-dpp-bsdd.vercel.app/id/01/04012345678901
  - Glulam: https://lignum-dpp-bsdd.vercel.app/id/01/07640123456789
  - PVC:    https://lignum-dpp-bsdd.vercel.app/id/01/05790001234561
- Ontology: https://lignum-dpp-bsdd.vercel.app/ontology
- SHACL Shapes: https://lignum-dpp-bsdd.vercel.app/ontology/shacl
- QR gallery: ./qr_codes/index.html (generated locally)

## Local development
To run everything against a local server:
```bash
DPP_API_URL=http://localhost:8000 ./run_demo.sh
```

## What this demonstrates
- prEN 18223 data model in JSON-LD (with bSDD references)
- prEN 18222 REST endpoints (Create/Read/Update/Register)
- prEN 18220 data carriers (QR -> GS1 Digital Link)
- prEN 18219 identifiers (GTIN, DID:web, GLN/LEI)
- ISO 22057 EPD content inclusion
- IFC patching + IDS check workflow
- Content negotiation (HTML in browser, JSON-LD via curl)
- SHACL validation endpoint
- OWL ontology serving

---

**Note**: This is a proof-of-concept implementation. The prEN standards are drafts under enquiry and may change before final publication.
