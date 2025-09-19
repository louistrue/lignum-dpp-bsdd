#!/bin/bash
set -euo pipefail

# Lignum DPP PoC – End-to-End Demo Runner (localhost)
# Shows: API, JSON-LD DPPs, GS1 resolvers, documents, create/register/update,
# QR codes, IFC patch (optional), and IDS check (instruction using existing tools).

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$ROOT_DIR/api"

echo "\n=== 0) Environment check ==="
command -v python3 >/dev/null || { echo "Python3 is required"; exit 1; }
echo "Python: $(python3 --version)"

echo "\n=== 1) Install runtime deps (PoC) ==="
(cd "$API_DIR" && pip3 install -r requirements.txt >/dev/null)
pip3 show ifcopenshell >/dev/null 2>&1 || pip3 install ifcopenshell >/dev/null || true

echo "\n=== 2) Start API on localhost:8000 (background) ==="
pkill -f "python3 main.py" >/dev/null 2>&1 || true
(cd "$API_DIR" && nohup python3 main.py >/dev/null 2>&1 & echo $! > "$ROOT_DIR/.api_pid")
sleep 2

echo "Waiting for API..."
for i in {1..10}; do
  if curl -sf http://localhost:8000/health >/dev/null; then echo "API is up"; break; fi
  sleep 1
done

echo "\n=== 3) List DPPs ==="
curl -s http://localhost:8000/dpps | python3 -m json.tool | sed -n '1,30p'

echo "\n=== 4) Read DPP (JSON-LD + HTML) ==="
curl -s -H 'Accept: application/ld+json' \
  "http://localhost:8000/dpps/did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001" \
  | python3 -m json.tool | sed -n '1,20p'

echo "Open human view in browser (optional)"
open "http://localhost:8000/dpps/did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001" >/dev/null 2>&1 || true

echo "\n=== 5) Resolve via GS1 Digital Link (QR target) ==="
curl -s -H 'Accept: application/ld+json' \
  "http://localhost:8000/id/01/04012345678901/21/KI-AB-2025-001" \
  | python3 -m json.tool | sed -n '1,12p'

echo "\n=== 6) Verify linked documents (served from repo via /files) ==="
curl -I "http://localhost:8000/files/insul/Acoustic%20Batt%20Datasheet%20.pdf" | sed -n '1,3p'
curl -I "http://localhost:8000/files/bsh/EPD%20Schilliger_glued_laminated_timber_Glulam_as_per_EN_140802013.pdf" | sed -n '1,3p'

echo "\n=== 7) Generate QR codes & open viewer ==="
python3 "$ROOT_DIR/qr_codes/tools/generate_qr_codes.py" >/dev/null
open "$ROOT_DIR/qr_codes/index.html" >/dev/null 2>&1 || true

echo "\n=== 8) Create a new DPP (server generates ID) ==="
NEW_DPP_JSON="$ROOT_DIR/tmp_new_dpp.json"
python3 - "$ROOT_DIR/dpp/products/dpp_pvc_sewage_pipe.jsonld" > "$NEW_DPP_JSON" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
d.pop('id', None)
print(json.dumps(d))
PY
CREATE_RESP=$(curl -s -X POST http://localhost:8000/dpps \
  -H 'Content-Type: application/ld+json' \
  --data-binary @"$NEW_DPP_JSON")
echo "$CREATE_RESP" | python3 -m json.tool | sed -n '1,12p'
NEW_ID=$(echo "$CREATE_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')
echo "New DPP ID: $NEW_ID"

echo "\n=== 9) Register the new DPP (local registry) ==="
REG_PAYLOAD=$(NEW_ID="$NEW_ID" python3 - <<'PY'
import os, json
print(json.dumps({
  'dppId': os.environ.get('NEW_ID',''),
  'productIdentifiers':[{'scheme':'gtin','value':'05790001234561'}],
  'economicOperatorId':'did:web:wavin.com'
}))
PY
)
curl -s -X POST http://localhost:8000/registerDPP \
  -H 'Content-Type: application/json' -d "$REG_PAYLOAD" | python3 -m json.tool | sed -n '1,20p'

echo "\n=== 10) Update DPP (RFC 7396 merge patch) ==="
PATCH='{"dpp:status":"archived"}'
curl -s -X PATCH "http://localhost:8000/dpps/$NEW_ID" \
  -H 'Content-Type: application/merge-patch+json' -d "$PATCH" | python3 -m json.tool | sed -n '1,14p'

echo "\n=== 11) IFC patch (optional if IFC present) ==="
IFC_IN="$ROOT_DIR/ifc/samples/POC.ifc"
IFC_OUT="$ROOT_DIR/ifc/outputs/POC_patched.ifc"
if [ -f "$IFC_IN" ]; then
  echo "Patching IFC using mapping.csv and DPP JSON-LD..."
  python3 "$ROOT_DIR/ifc/tools/patch_ifc.py" \
    --ifc "$IFC_IN" \
    --mapping "$ROOT_DIR/mapping/mapping.csv" \
    --dpp-dir "$ROOT_DIR/dpp/products" \
    --out "$IFC_OUT"
  echo "Patched IFC: $IFC_OUT"
else
  echo "(Skip) No IFC found at $IFC_IN. Add a demo IFC to run this step."
fi

echo "\n=== 12) IDS validation (use existing tools) ==="
echo "Open the official IDS validator and validate your patched IFC against POC.ids:"
echo "  - IDS file: $ROOT_DIR/ifc/ids/POC.ids"
echo "  - IFC file: $IFC_OUT (if generated)"
echo "Or use BlenderBIM / BIMcollab IDS check with the same files."

echo "\n=== Done. Press Ctrl+C to stop API if running in foreground. ==="
exit 0


