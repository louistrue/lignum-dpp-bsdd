# Lignum DPP PoC – Demo Guide (localhost)

This guide explains how to run and present the complete Digital Product Passport (DPP) PoC end-to-end on localhost.

## Quick start (one command)

```bash
./run_demo.sh
```

The script will:
- Start the API on http://localhost:8000
- List existing DPPs
- Read a DPP (JSON‑LD) and open its HTML view
- Resolve via GS1 Digital Link
- Verify local PDFs under /files
- Generate QR codes (exactly 3) and open the QR gallery
- Create a new DPP, register it (local registry), then update it (RFC 7396)
- Optionally patch an IFC (if `POC.ifc` exists at repo root)
- Show how to validate with the existing `POC.ids` using external IDS tools
- Expose a small admin helper to hot‑reload DPP files from disk

## Presenting live (manual step‑by‑step)

1) Start API
```bash
cd api
pip3 install -r requirements.txt
python3 main.py
```
- Health: http://localhost:8000/health
- Hot‑reload DPPs after editing files (no restart needed):
  ```bash
  curl -X POST http://localhost:8000/admin/reload
  ```

2) List DPPs
```bash
curl -s http://localhost:8000/dpps | python3 -m json.tool | sed -n '1,60p'
```

3) Read DPP (JSON‑LD) and HTML view
```bash
curl -s -H 'Accept: application/ld+json' \
  http://localhost:8000/dpps/did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001 \
  | python3 -m json.tool | sed -n '1,40p'
```
Open HTML view in a browser:
- http://localhost:8000/dpps/did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001

4) GS1 Digital Link resolver (QR target)
```bash
curl -s -H 'Accept: application/ld+json' \
  http://localhost:8000/id/01/04012345678901/21/KI-AB-2025-001 \
  | python3 -m json.tool | sed -n '1,20p'
```

5) Linked documents (served from repo via /files)
```bash
curl -I "http://localhost:8000/files/insul/Acoustic%20Batt%20Datasheet%20.pdf" | sed -n '1,3p'
curl -I "http://localhost:8000/files/bsh/EPD%20Schilliger_glued_laminated_timber_Glulam_as_per_EN_140802013.pdf" | sed -n '1,3p'
# Pipe example (local EPD):
curl -I "http://localhost:8000/files/pipe/NEPD-3589-2252_PVC-Sewage-Pipe.pdf" | sed -n '1,3p'
```

6) QR codes (one per product)
```bash
python3 ./qr_codes/tools/generate_qr_codes.py
open ./qr_codes/index.html
```
Each card shows:
- QR image
- “Open DPP” link (resolver)
- “GS1 Link” (Digital Link URI)

7) Create → Register → Update a DPP
```bash
# Create (server assigns an ID)
NEW_DPP_JSON=./tmp_new_dpp.json
python3 - ./dpp/products/dpp_pvc_sewage_pipe.jsonld > "$NEW_DPP_JSON" <<'PY'
import json,sys
j=json.load(open(sys.argv[1])); j.pop('id', None)
print(json.dumps(j))
PY
CREATE_RESP=$(curl -s -X POST http://localhost:8000/dpps \
  -H 'Content-Type: application/ld+json' --data-binary @"$NEW_DPP_JSON")
NEW_ID=$(echo "$CREATE_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')
echo "New ID: $NEW_ID"

# Register (local registry)
REG_PAYLOAD=$(NEW_ID="$NEW_ID" python3 - <<'PY'
import os,json
print(json.dumps({
  'dppId': os.environ['NEW_ID'],
  'productIdentifiers':[{'scheme':'gtin','value':'05790001234561'}],
  'economicOperatorId':'did:web:wavin.com'
}))
PY
)
curl -s -X POST http://localhost:8000/registerDPP -H 'Content-Type: application/json' -d "$REG_PAYLOAD" | python3 -m json.tool | sed -n '1,20p'

# Update (RFC 7396 merge patch)
PATCH='{"dpp:status":"archived"}'
curl -s -X PATCH "http://localhost:8000/dpps/$NEW_ID" -H 'Content-Type: application/merge-patch+json' -d "$PATCH" \
  | python3 -m json.tool | sed -n '1,20p'
```

8) IFC patch
```bash
python3 ./ifc/tools/patch_ifc.py \
  --ifc ./ifc/samples/POC.ifc \
  --mapping ./mapping/mapping.csv \
  --dpp-dir ./dpp/products \
  --out ./ifc/outputs/POC_patched.ifc
```

9) IDS validation
- IDS: `./ifc/ids/POC.ids`
- IFC: `./ifc/outputs/POC_patched.ifc` (from step 8)
Use the official IDS validator or tools like BlenderBIM / BIMcollab to validate CPset_* properties.

## URLs to showcase in the browser
- Health: http://localhost:8000/health
- DPP JSON‑LD/HTML (Knauf): http://localhost:8000/dpps/did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001
- GS1 resolvers:
  - Knauf:  http://localhost:8000/id/01/04012345678901/21/KI-AB-2025-001
  - Glulam: http://localhost:8000/id/01/07640123456789/10/BSH2022
  - PVC:    http://localhost:8000/id/01/05790001234561/21/WV-DN110-2025-001
- QR gallery: ./qr_codes/index.html
- Local PDFs under `/files`: e.g. http://localhost:8000/files/insul/Acoustic%20Batt%20Datasheet%20.pdf
  - Served from `data/` (preferred) or `vLignum/` (fallback)

## Troubleshooting
- Port 8000 in use: stop other services or kill the previous dev server:
  ```bash
  pkill -f "python3 main.py" || true
  ```
- Python deps: run `pip3 install -r api/requirements.txt`, and for IFC step: `pip3 install ifcopenshell`.
- No QR images: run `python3 ./qr_codes/tools/generate_qr_codes.py`.
- No IFC step: add a sample IFC as `./POC.ifc`.
- DPP edits not visible: call `POST /admin/reload` to refresh in‑memory DPPs without restarting.

## What this demonstrates
- prEN 18223 data model in JSON‑LD (with bSDD references)
- prEN 18222 REST endpoints (Create/Read/Update/Register)
- prEN 18220 data carriers (QR → GS1 Digital Link)
- prEN 18219 identifiers (GTIN, DID:web, GLN/LEI)
- ISO 22057 EPD content inclusion
- IFC patching + IDS check workflow

---

**Note**: This is a proof-of-concept implementation. The prEN standards are drafts under enquiry and may change before final publication.
