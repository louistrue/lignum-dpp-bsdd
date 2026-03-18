"""
Lignum DPP API Server [DEMO]
Proof-of-concept conforming to prEN 18222:2025 - API specification
NOT an official Digital Product Passport server.
"""

import json
import hashlib
import html as html_module
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import unquote
import os

from fastapi import FastAPI, HTTPException, Header, Request, Response, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Base URL: use explicit env var, fall back to Vercel's auto-set URL, then localhost
BASE_URL = os.getenv("BASE_URL") or (
    f"https://{os.getenv('VERCEL_URL')}" if os.getenv("VERCEL_URL") else "http://localhost:8000"
)
BASE_URL = BASE_URL.rstrip("/")

DEMO_DISCLAIMER = (
    "DEMO / PROOF OF CONCEPT — This is NOT an official Digital Product Passport server. "
    "Sample data only. Not operated by or affiliated with any manufacturer. "
    "Presented at bS-Summit Porto."
)

# Demo protection: when True, seed DPPs cannot be deleted or destructively modified.
# Set DEMO_PROTECTED=false to disable (e.g. for local development).
DEMO_PROTECTED = os.getenv("DEMO_PROTECTED", "true").lower() != "false"

# IDs of seed DPPs loaded from disk — populated by load_sample_dpps()
_seed_dpp_ids: set = set()

# SVG favicon — stylised tree-ring cross-section (wood = "lignum")
FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#fff"/>
  <circle cx="16" cy="16" r="11" fill="none" stroke="#8b6f47" stroke-width="1.5" opacity=".35"/>
  <circle cx="16" cy="16" r="8" fill="none" stroke="#8b6f47" stroke-width="1.5" opacity=".5"/>
  <circle cx="16" cy="16" r="5" fill="none" stroke="#8b6f47" stroke-width="1.5" opacity=".7"/>
  <circle cx="16" cy="16" r="2" fill="#8b6f47"/>
</svg>"""

FAVICON_DATA_URI = "data:image/svg+xml," + FAVICON_SVG.replace("#", "%23").replace("\n", "").replace("  ", "")

META_DESCRIPTION = (
    "Proof-of-concept Digital Product Passport (DPP) API for construction products, "
    "conforming to prEN 18222:2025 with GS1 Digital Link, bSDD references, and SHACL validation."
)

# Tag metadata controls ordering in Swagger UI
tags_metadata = [
    {"name": "Demo Landing", "description": "Interactive landing page with product cards and QR codes"},
    {"name": "Linked Data & Ontology", "description": "OWL ontology, SHACL shapes, and JSON-LD validation"},
    {"name": "GS1 Digital Link", "description": "Resolve product identifiers via GS1 Digital Link URIs"},
    {"name": "DPP CRUD", "description": "Create, read, update, delete Digital Product Passports (prEN 18222)"},
    {"name": "Data Elements", "description": "Access individual data element collections and elements"},
    {"name": "Registry", "description": "EU DPP registry simulation (PoC)"},
    {"name": "System", "description": "Health checks and admin endpoints"},
]

# Initialize FastAPI app
app = FastAPI(
    title="Lignum DPP API [DEMO] — bS-Summit Porto",
    description=(
        "## DEMO / PROOF OF CONCEPT\n\n"
        "**This is NOT an official Digital Product Passport server.**\n"
        "Sample data for demonstration purposes only. Not affiliated with any manufacturer.\n\n"
        "---\n\n"
        "### What is this?\n"
        "A working proof-of-concept of the **prEN 18222:2025** DPP API specification for construction products, "
        "featuring:\n\n"
        "- **GS1 Digital Link** resolution (scan a QR code → get the DPP)\n"
        "- **bSDD** (buildingSMART Data Dictionary) property references with clickable links\n"
        "- **OWL ontology** & **SHACL shapes** for linked-data validation\n"
        "- **Content negotiation**: same URL returns HTML (browser) or JSON-LD (`Accept: application/ld+json`)\n"
        "- **Declaration of Performance** (DoPC) data per EU CPR\n\n"
        "### Try it\n"
        "1. Browse the [DPP list](/dpps) or the [interactive landing page](/)\n"
        "2. Click a DPP link in your browser → HTML view with bSDD links & QR codes\n"
        "3. `curl` the same URL with `-H 'Accept: application/ld+json'` → JSON-LD\n"
        "4. POST a DPP to [`/validate`](#/Linked%20Data%20%26%20Ontology/validate_dpp_validate_post) to check SHACL conformance\n\n"
        "### Sample products\n"
        "| Product | GTIN | GS1 Link |\n"
        "|---------|------|----------|\n"
        "| Knauf Acoustic Batt | `04012345678901` | [`/id/01/04012345678901`](/id/01/04012345678901) |\n"
        "| Schilliger Glulam GL24h | `07640123456789` | [`/id/01/07640123456789`](/id/01/07640123456789) |\n"
        "| PVC Sewage Pipe DN110 | `05790001234561` | [`/id/01/05790001234561`](/id/01/05790001234561) |\n\n"
        "*Presented at bS-Summit Porto — buildingSMART International*"
    ),
    version="0.1.0-demo",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=tags_metadata,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo disclaimer middleware — adds headers to every response
@app.middleware("http")
async def add_demo_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-DPP-Demo"] = "true"
    response.headers["X-DPP-Disclaimer"] = (
        "DEMO ONLY - Not an official DPP server - bS-Summit Porto PoC"
    )
    return response

# In-memory storage (replace with database in production)
dpp_storage: Dict[str, Dict] = {}
registry_storage: Dict[str, Dict] = {}

# Load sample DPPs from JSON-LD files
def load_sample_dpps():
    """Load sample DPP files from dpp/products directory.

    Replaces hardcoded localhost:8000 URLs with BASE_URL and injects
    demo disclaimer metadata into each DPP.
    """
    api_path = Path(__file__).parent
    base_path = api_path.parent
    # Vercel bundles files inside api/; local dev uses project root
    dpp_dir = api_path / "data" / "dpp"
    if not dpp_dir.exists():
        dpp_dir = base_path / "dpp" / "products"
    if not dpp_dir.exists():
        candidates = [
            base_path / "dpp_knauf_acoustic_batt.jsonld",
            base_path / "dpp_schilliger_glulam.jsonld",
            base_path / "dpp_pvc_sewage_pipe.jsonld",
        ]
    else:
        candidates = sorted(dpp_dir.glob("*.jsonld"))

    for filepath in candidates:
        try:
            raw = filepath.read_text(encoding="utf-8")
            # Replace localhost URLs with deployment BASE_URL
            if BASE_URL != "http://localhost:8000":
                raw = raw.replace("http://localhost:8000", BASE_URL)
            dpp_data = json.loads(raw)
            dpp_id = dpp_data.get("id")
            if dpp_id:
                # Inject demo disclaimer into every DPP
                dpp_data["dpp:disclaimer"] = DEMO_DISCLAIMER
                dpp_data["dpp:demoNotice"] = {
                    "type": "schema:SpecialAnnouncement",
                    "schema:name": "Demo Disclaimer",
                    "schema:text": (
                        "This DPP instance is a proof-of-concept demonstration. "
                        "All data is illustrative and not authoritative. "
                        "Not operated by or affiliated with any manufacturer."
                    ),
                    "schema:category": "demo",
                    "schema:event": "bS-Summit Porto"
                }
                dpp_storage[dpp_id] = dpp_data
                _seed_dpp_ids.add(dpp_id)
                print(f"Loaded sample DPP: {dpp_id}")
        except Exception as e:
            print(f"Warning: failed to load DPP {filepath}: {e}")

# Pydantic models for request/response
class ProductIdentifier(BaseModel):
    scheme: str = Field(alias="dpp:scheme")
    value: str = Field(alias="dpp:value")
    namespace: Optional[str] = Field(None, alias="dpp:namespace")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

class RegistryRequest(BaseModel):
    dppId: str
    productIdentifiers: List[Dict[str, str]]
    economicOperatorId: str
    backupOperatorId: Optional[str] = None

class RegistryResponse(BaseModel):
    registryId: str
    registryUrl: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict] = None

# Helper functions
def generate_registry_id() -> str:
    """Generate a unique registry ID"""
    return f"urn:eu-dpp-reg:{uuid.uuid4()}"

def verify_bearer_token(authorization: Optional[str] = Header(None)) -> bool:
    """Simple bearer token verification (implement properly for production)"""
    if not authorization:
        return False
    # In production, verify JWT token here
    return authorization.startswith("Bearer ")

def render_dpp_as_html(dpp: Dict) -> str:
    """Render DPP as a polished HTML page for human viewing."""
    dpp_id = dpp.get("id", "N/A")
    op = dpp.get("dpp:economicOperator", {})
    op_name = html_module.escape(str(op.get("schema:name", "Unknown")))

    # Derive product name
    collections = dpp.get("dpp:dataElementCollections", [])
    dopc_coll = next((c for c in collections if c.get("id") == "#dopc"), None)
    product_name = "Construction Product"
    if dopc_coll and "dpp:dopcMetadata" in dopc_coll:
        product_name = dopc_coll["dpp:dopcMetadata"].get("dpp:productName", product_name)
    if product_name == "Construction Product":
        product_name = dpp_id.split(":")[-1].replace("-", " ").title()

    # Find GS1 link and QR URI
    pids = dpp.get("dpp:productIdentifiers", [])
    gtin = next((p["dpp:value"] for p in pids if p.get("dpp:scheme") == "gtin"), "")
    qr_uri = ""
    for c in collections:
        if c.get("id") == "#carrier":
            for e in c.get("dpp:elements", []):
                if e.get("id") == "#qrLink":
                    qr_uri = e.get("dpp:value", {}).get("uri", "")

    # Generate QR code as inline SVG-style using simple table approach
    qr_data_uri = ""
    if qr_uri:
        try:
            import qrcode
            import io
            import base64
            qr = qrcode.QRCode(version=1, box_size=6, border=2)
            qr.add_data(qr_uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            qr_data_uri = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
        except Exception:
            pass

    # --- Build HTML ---
    esc = html_module.escape

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{esc(product_name)} — Digital Product Passport (prEN 18222 demo)">
    <meta name="theme-color" content="#111">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <title>{esc(product_name)} &mdash; DPP [DEMO]</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #fff; color: #1a1a1a; min-height: 100vh; line-height: 1.5; }}
        .demo-banner {{ position: fixed; top: 0; left: 0; right: 0; z-index: 9999; background: #b91c1c; color: white; text-align: center; padding: 8px 20px; font-size: 12px; font-weight: 600; letter-spacing: 0.3px; }}
        .container {{ max-width: 860px; margin: 0 auto; padding: 60px 24px 48px; }}
        .header {{ margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #e5e5e5; }}
        .header h1 {{ font-size: 1.75em; font-weight: 700; color: #111; margin-bottom: 4px; letter-spacing: -0.01em; }}
        .header .operator {{ font-size: 0.95em; color: #666; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 1px; margin: 24px 0; background: #e5e5e5; border: 1px solid #e5e5e5; border-radius: 4px; overflow: hidden; }}
        .meta-item {{ background: #fafafa; padding: 14px 16px; }}
        .meta-item .lbl {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; color: #888; margin-bottom: 4px; font-weight: 600; }}
        .meta-item .val {{ font-size: 13px; color: #1a1a1a; word-break: break-all; }}
        .meta-item .val code {{ background: #f0f0f0; padding: 2px 5px; border-radius: 3px; font-size: 12px; color: #333; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; }}
        .status {{ display: inline-block; padding: 2px 10px; border-radius: 3px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
        .status-active {{ background: #dcfce7; color: #166534; }}
        .section {{ margin: 32px 0; }}
        .section-title {{ font-size: 0.85em; font-weight: 700; color: #444; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #111; text-transform: uppercase; letter-spacing: 0.8px; }}
        .card {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 16px; margin-bottom: 12px; }}
        .prop-row {{ display: flex; justify-content: space-between; align-items: baseline; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }}
        .prop-row:last-child {{ border-bottom: none; }}
        .prop-name {{ font-size: 13px; color: #555; flex: 1; }}
        .prop-value {{ font-size: 13px; font-weight: 600; color: #111; text-align: right; }}
        .prop-unit {{ font-size: 12px; color: #888; margin-left: 4px; font-weight: 400; }}
        .bsdd-link {{ display: inline-block; margin-left: 6px; padding: 1px 6px; background: #f0f7ff; border: 1px solid #c5d9ed; border-radius: 3px; font-size: 10px; color: #2563eb; text-decoration: none; font-weight: 600; letter-spacing: 0.3px; }}
        .bsdd-link:hover {{ background: #dbeafe; }}
        .dopc-header {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 16px; margin-bottom: 14px; }}
        .dopc-header strong {{ color: #1e40af; font-size: 14px; }}
        .dopc-meta {{ font-size: 13px; color: #555; line-height: 1.8; }}
        .doc-item {{ display: flex; align-items: center; gap: 10px; padding: 12px 14px; background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; margin-bottom: 6px; text-decoration: none; color: #1a1a1a; transition: border-color 0.15s; }}
        .doc-item:hover {{ border-color: #999; }}
        .doc-icon {{ font-size: 16px; color: #888; }}
        .doc-name {{ font-size: 13px; font-weight: 500; }}
        .indicator-table {{ width: 100%; border-collapse: collapse; }}
        .indicator-table th {{ background: #f5f5f5; color: #555; padding: 10px 14px; text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 700; border-bottom: 2px solid #ddd; }}
        .indicator-table td {{ padding: 9px 14px; border-bottom: 1px solid #eee; font-size: 13px; color: #333; }}
        .indicator-table tr:hover td {{ background: #fafafa; }}
        .carrier-card {{ background: #fafafa; border: 1px solid #e5e5e5; border-radius: 4px; padding: 24px; text-align: center; }}
        .carrier-card h3 {{ color: #111; margin-bottom: 12px; font-size: 14px; font-weight: 600; }}
        .carrier-card img {{ margin: 12px auto; display: block; }}
        .carrier-card code {{ display: block; background: #f0f0f0; padding: 10px; border-radius: 3px; font-size: 11px; color: #333; margin-top: 12px; word-break: break-all; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; }}
        .carrier-card .gs1-label {{ font-size: 11px; color: #888; margin-top: 8px; }}
        .class-card {{ display: flex; align-items: center; gap: 16px; padding: 16px; background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; margin-bottom: 8px; }}
        .class-info {{ flex: 1; }}
        .class-info .scheme {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }}
        .class-info .name {{ font-size: 15px; font-weight: 600; color: #111; margin: 4px 0; }}
        .class-info a {{ color: #2563eb; font-size: 12px; text-decoration: none; }}
        .class-info a:hover {{ text-decoration: underline; }}
        .json-toggle {{ display: inline-block; margin-top: 20px; padding: 7px 16px; background: #fff; border: 1px solid #ccc; border-radius: 3px; color: #333; font-size: 13px; text-decoration: none; font-weight: 500; }}
        .json-toggle:hover {{ background: #f5f5f5; border-color: #999; }}
        .footer {{ text-align: center; padding: 32px 0; color: #999; font-size: 12px; margin-top: 24px; border-top: 1px solid #e5e5e5; }}
        .footer a {{ color: #666; text-decoration: none; }}
        .footer a:hover {{ color: #111; }}
        a.back-link {{ color: #666; text-decoration: none; font-size: 13px; }}
        a.back-link:hover {{ color: #111; }}
    </style>
</head>
<body>
    <div class="demo-banner">
        DEMO / PROOF OF CONCEPT — NOT an official DPP server — Sample data only — Not affiliated with any manufacturer — bS-Summit Porto
    </div>
    <div class="container">
        <a href="/" class="back-link">&larr; Back to all products</a>
        <div class="header" style="margin-top:16px;">
            <h1>{esc(product_name)}</h1>
            <div class="operator">{op_name}</div>
        </div>

        <div class="meta-grid">
            <div class="meta-item">
                <div class="lbl">Status</div>
                <div class="val"><span class="status status-active">{esc(str(dpp.get('dpp:status', 'N/A')))}</span></div>
            </div>
            <div class="meta-item">
                <div class="lbl">Schema Version</div>
                <div class="val">{esc(str(dpp.get('dpp:dppSchemaVersion', 'N/A')))}</div>
            </div>
            <div class="meta-item">
                <div class="lbl">Last Modified</div>
                <div class="val">{esc(str(dpp.get('dcterms:modified', 'N/A')))}</div>
            </div>
            <div class="meta-item">
                <div class="lbl">DPP ID</div>
                <div class="val"><code>{esc(str(dpp_id))}</code></div>
            </div>
        </div>
"""

    # Product Identifiers
    if pids:
        html += '<div class="section"><h2 class="section-title">Product Identifiers</h2><div class="meta-grid">'
        for pid in pids:
            scheme = esc(str(pid.get("dpp:scheme", "unknown")))
            val = esc(str(pid.get("dpp:value", "")))
            html += f'<div class="meta-item"><div class="lbl">{scheme}</div><div class="val"><code>{val}</code></div></div>'
        html += "</div></div>"

    # Economic Operator detail
    if op:
        html += '<div class="section"><h2 class="section-title">Economic Operator</h2><div class="card">'
        for k, label in [("schema:name", "Name"), ("dpp:lei", "LEI"), ("dpp:gln", "GLN"), ("id", "DID")]:
            if k in op:
                html += f'<div class="prop-row"><span class="prop-name">{esc(label)}</span><span class="prop-value">{esc(str(op[k]))}</span></div>'
        html += "</div></div>"

    # Data Element Collections — render order: DoPC, EPD, Documents, Carrier, Classification
    # Skip #productProperties entirely (duplicates DoPC declared values)
    for collection in collections:
        coll_id = collection.get("id", "")
        title = esc(str(collection.get("dcterms:title", "Untitled")))
        elements = collection.get("dpp:elements", [])

        # --- Skip product properties (redundant with DoPC) ---
        if coll_id == "#productProperties":
            continue

        # --- Classification ---
        if coll_id == "#classification":
            html += f'<div class="section"><h2 class="section-title">{title}</h2>'
            for element in elements:
                val = element.get("dpp:value", {})
                if isinstance(val, dict):
                    scheme = esc(str(val.get("scheme", "")))
                    name = esc(str(val.get("name", "")))
                    uri = val.get("uri", "")
                    html += f"""<div class="class-card">
                        <div class="class-info">
                            <div class="scheme">{scheme}</div>
                            <div class="name">{name}</div>
                            {f'<a href="{esc(uri)}" target="_blank">{esc(uri)}</a>' if uri else ''}
                        </div>
                    </div>"""
            html += "</div>"
            continue

        # --- Data Carrier / QR ---
        if coll_id == "#carrier":
            html += f'<div class="section"><h2 class="section-title">{title}</h2><div class="carrier-card">'
            if qr_data_uri:
                html += f'<img src="{qr_data_uri}" alt="QR Code" width="180" height="180">'
            if qr_uri:
                html += f'<code>{esc(qr_uri)}</code>'
                html += '<div class="gs1-label">GS1 Digital Link — scan to access this DPP</div>'
            if gtin:
                gs1_link = f"{BASE_URL}/id/01/{gtin}"
                html += f'<div style="margin-top:12px;"><a href="{esc(gs1_link)}" class="bsdd-link" style="font-size:13px;">Open GS1 Link</a></div>'
            html += "</div></div>"
            continue

        # --- Documents ---
        if coll_id == "#documents":
            html += f'<div class="section"><h2 class="section-title">{title}</h2>'
            for element in elements:
                if element.get("type") == "dpp:Document":
                    fname = esc(str(element.get("dpp:fileName", "Document")))
                    url = esc(str(element.get("schema:url", "#")))
                    html += f'<a href="{url}" class="doc-item" target="_blank"><span class="doc-name">{fname}</span></a>'
            html += "</div>"
            continue

        # --- DoPC or EPD collections ---
        html += f'<div class="section"><h2 class="section-title">{title}</h2>'

        # DoPC metadata header
        if "dpp:dopcMetadata" in collection:
            meta = collection["dpp:dopcMetadata"]
            html += '<div class="dopc-header"><strong>Declaration of Performance (DoPC)</strong><div class="dopc-meta">'
            for mk, ml in [("dpp:declarationCode", "Code"), ("dpp:dateOfIssue", "Issued"),
                           ("dpp:harmonisedStandard", "Standard"), ("dpp:avcpSystem", "AVCP System"),
                           ("dpp:notifiedBody", "Notified Body"), ("dpp:intendedUse", "Intended Use"),
                           ("dpp:declaredUnit", "Declared Unit"), ("dpp:productName", "Product Name")]:
                if mk in meta:
                    html += f"<div><strong>{esc(ml)}:</strong> {esc(str(meta[mk]))}</div>"
            html += "</div></div>"

        # Render elements
        has_props = False
        for element in elements:
            # Indicator table (EPD LCIA)
            if "dpp:value" in element and isinstance(element["dpp:value"], list):
                items = element["dpp:value"]
                if items and isinstance(items[0], dict) and "indicator" in items[0]:
                    html += '<div class="card"><table class="indicator-table"><thead><tr><th>Indicator</th><th>Module</th><th>Value</th><th>Unit</th></tr></thead><tbody>'
                    for ind in items:
                        html += f'<tr><td>{esc(str(ind.get("indicator","")))}</td><td>{esc(str(ind.get("module","")))}</td><td>{esc(str(ind.get("value","")))}</td><td>{esc(str(ind.get("unit","")))}</td></tr>'
                    html += "</tbody></table></div>"
                continue

            # Single value property with optional bSDD link
            if "dpp:valueElement" in element:
                if not has_props:
                    html += '<div class="card">'
                    has_props = True
                ve = element["dpp:valueElement"]
                raw_name = str(element.get("dpp:name", "Property"))
                # Clean up property names: strip DOPC_ prefix, replace underscores
                display_name = raw_name
                if display_name.startswith("DOPC_"):
                    display_name = display_name[5:]
                display_name = display_name.replace("_", " ").title()
                value = esc(str(ve.get("dpp:numericValue") or ve.get("dpp:textValue", "N/A")))
                unit = esc(str(ve.get("dpp:unit", "")))
                dict_ref = element.get("dpp:dictionaryReference", "")
                bsdd_html = ""
                if dict_ref and "buildingsmart.org" in dict_ref:
                    bsdd_html = f'<a href="{esc(dict_ref)}" class="bsdd-link" target="_blank" title="View in bSDD">bSDD</a>'
                html += f'<div class="prop-row"><span class="prop-name">{esc(display_name)}{bsdd_html}</span><span class="prop-value">{value}<span class="prop-unit">{unit}</span></span></div>'
                continue

            # Object values (EPD metadata etc.) — format dicts and lists nicely
            if "dpp:value" in element and isinstance(element["dpp:value"], dict):
                obj = element["dpp:value"]
                if not has_props:
                    html += '<div class="card">'
                    has_props = True
                for k, v in obj.items():
                    display_key = esc(str(k).replace("_", " ").title())
                    if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")):
                        html += f'<div class="prop-row"><span class="prop-name">{display_key}</span><span class="prop-value"><a href="{esc(v)}" target="_blank" style="color:#2563eb;text-decoration:none;">{esc(v)}</a></span></div>'
                    elif isinstance(v, dict):
                        # Format nested dicts like {value: 1, unit: m³} nicely
                        if "value" in v and "unit" in v:
                            html += f'<div class="prop-row"><span class="prop-name">{display_key}</span><span class="prop-value">{esc(str(v["value"]))}<span class="prop-unit">{esc(str(v["unit"]))}</span></span></div>'
                        else:
                            parts = ", ".join(f"{esc(str(dk))}: {esc(str(dv))}" for dk, dv in v.items())
                            html += f'<div class="prop-row"><span class="prop-name">{display_key}</span><span class="prop-value">{parts}</span></div>'
                    elif isinstance(v, list):
                        # Format lists nicely
                        html += f'<div class="prop-row"><span class="prop-name">{display_key}</span><span class="prop-value">{esc(", ".join(str(i) for i in v))}</span></div>'
                    elif isinstance(v, bool):
                        html += f'<div class="prop-row"><span class="prop-name">{display_key}</span><span class="prop-value">{"Yes" if v else "No"}</span></div>'
                    else:
                        html += f'<div class="prop-row"><span class="prop-name">{display_key}</span><span class="prop-value">{esc(str(v))}</span></div>'
                continue

        if has_props:
            html += "</div>"
        html += "</div>"

    # JSON-LD toggle link
    encoded_id = dpp_id.replace("/", "%2F").replace(":", "%3A")
    html += f"""
        <div style="text-align:center;margin-top:30px;">
            <a href="/dpps/{encoded_id}" class="json-toggle" onclick="fetch('/dpps/{encoded_id}',{{headers:{{'Accept':'application/ld+json'}}}}).then(r=>r.json()).then(d=>{{document.getElementById('json-view').textContent=JSON.stringify(d,null,2);document.getElementById('json-panel').style.display='block';}});return false;">
                View JSON-LD
            </a>
        </div>
        <pre id="json-panel" style="display:none;background:#f5f5f5;border:1px solid #e5e5e5;border-radius:4px;padding:20px;margin-top:16px;overflow-x:auto;font-size:12px;color:#333;max-height:600px;overflow-y:auto;font-family:'SF Mono',Monaco,'Cascadia Code',monospace;"><code id="json-view"></code></pre>
        <div class="footer">
            <a href="/">Home</a> &middot;
            <a href="/docs">API Docs</a> &middot;
            <a href="/ontology">Ontology</a><br>
            bS-Summit Porto — buildingSMART International
        </div>
    </div>
</body>
</html>"""
    return html

# API Endpoints

@app.get("/", tags=["Demo Landing"])
async def root(request: Request):
    """Interactive demo landing page.

    Returns HTML in a browser, JSON-LD otherwise.
    Browse sample DPPs, scan QR codes, explore bSDD links and the OWL ontology.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        # Build product cards from loaded DPPs
        product_cards = ""
        for dpp in dpp_storage.values():
            dpp_id = dpp.get("id", "")
            op = dpp.get("dpp:economicOperator", {})
            op_name = html_module.escape(str(op.get("schema:name", "Unknown")))
            pids = dpp.get("dpp:productIdentifiers", [])
            gtin = next((p["dpp:value"] for p in pids if p.get("dpp:scheme") == "gtin"), "")
            labels = dpp.get("dpp:labels", [])
            label_tags = "".join(f'<span class="tag">{html_module.escape(l)}</span>' for l in labels[:5])

            # Extract product name from collection title or DPP ID
            collections = dpp.get("dpp:dataElementCollections", [])
            dopc_coll = next((c for c in collections if c.get("id") == "#dopc"), None)
            product_name = "Construction Product"
            if dopc_coll and "dpp:dopcMetadata" in dopc_coll:
                product_name = dopc_coll["dpp:dopcMetadata"].get("dpp:productName", product_name)
            if product_name == "Construction Product":
                # Derive from ID
                short = dpp_id.split(":")[-1].replace("-", " ").title()
                product_name = short

            encoded_id = dpp_id.replace("/", "%2F").replace(":", "%3A")
            gs1_link = f"/id/01/{gtin}" if gtin else ""

            product_cards += f"""
                <div class="product-card">
                    <div class="product-header">
                        <h3>{html_module.escape(product_name)}</h3>
                        <span class="operator">{op_name}</span>
                    </div>
                    <div class="product-body">
                        <div class="product-meta">
                            <div><strong>GTIN:</strong> <code>{html_module.escape(gtin)}</code></div>
                            <div><strong>DPP ID:</strong> <code style="font-size:11px">{html_module.escape(dpp_id)}</code></div>
                        </div>
                        <div class="tags">{label_tags}</div>
                    </div>
                    <div class="product-actions">
                        <a href="/dpps/{encoded_id}" class="btn btn-primary" title="HTML view in browser, JSON-LD via curl">View DPP</a>
                        <a href="{gs1_link}" class="btn btn-gs1" title="GS1 Digital Link resolver">GS1 Resolve</a>
                    </div>
                </div>
            """

        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta name="description" content="{META_DESCRIPTION}">
            <meta name="theme-color" content="#111">
            <meta property="og:title" content="Lignum DPP — Digital Product Passport Demo">
            <meta property="og:description" content="{META_DESCRIPTION}">
            <meta property="og:type" content="website">
            <link rel="icon" type="image/svg+xml" href="/favicon.svg">
            <title>Lignum DPP — Digital Product Passport Demo</title>
            <style>
                * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #fafafa; color: #1a1a1a; min-height: 100vh; line-height: 1.5; }}
                .demo-banner {{ position: fixed; top: 0; left: 0; right: 0; z-index: 9999; background: #b91c1c; color: white; text-align: center; padding: 6px 20px; font-size: 11px; font-weight: 600; letter-spacing: 0.3px; }}
                .page {{ max-width: 960px; margin: 0 auto; padding: 38px 24px 48px; }}
                .header {{ display: flex; align-items: flex-start; gap: 20px; margin-bottom: 16px; }}
                .header-text {{ flex: 1; }}
                .header h1 {{ font-size: 1.5em; font-weight: 700; color: #111; letter-spacing: -0.02em; margin-bottom: 4px; }}
                .header p {{ font-size: 13px; color: #666; line-height: 1.5; max-width: 600px; }}
                .standards {{ display: flex; gap: 5px; flex-wrap: wrap; margin-top: 8px; }}
                .standards span {{ background: #fff; border: 1px solid #ddd; padding: 2px 8px; font-size: 10px; color: #555; font-weight: 500; border-radius: 3px; }}
                .disclaimer-inline {{ font-size: 11px; color: #991b1b; background: #fef2f2; border: 1px solid #fecaca; border-radius: 3px; padding: 8px 12px; margin-bottom: 20px; line-height: 1.4; }}
                .section-title {{ font-size: 11px; font-weight: 700; color: #888; margin: 24px 0 10px; text-transform: uppercase; letter-spacing: 1px; }}
                .product-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
                @media (max-width: 768px) {{ .product-grid {{ grid-template-columns: 1fr; }} }}
                .product-card {{ background: #fff; border: 1px solid #e5e5e5; overflow: hidden; transition: border-color 0.15s; border-radius: 4px; display: flex; flex-direction: column; }}
                .product-card:hover {{ border-color: #999; }}
                .product-header {{ padding: 12px 14px 8px; }}
                .product-header h3 {{ font-size: 13px; color: #111; margin-bottom: 1px; font-weight: 600; line-height: 1.3; }}
                .operator {{ font-size: 11px; color: #999; }}
                .product-body {{ padding: 6px 14px 10px; flex: 1; }}
                .product-meta {{ font-size: 11px; color: #666; line-height: 1.6; }}
                .product-meta code {{ background: #f5f5f5; padding: 1px 4px; border-radius: 2px; font-size: 10px; color: #333; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; word-break: break-all; }}
                .tags {{ margin-top: 6px; display: flex; gap: 3px; flex-wrap: wrap; }}
                .tag {{ background: #f5f5f5; color: #666; padding: 1px 6px; border-radius: 2px; font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }}
                .product-actions {{ padding: 8px 14px 12px; display: flex; gap: 6px; }}
                .btn {{ padding: 5px 12px; border-radius: 3px; text-decoration: none; font-weight: 600; font-size: 11px; transition: all 0.1s; }}
                .btn-primary {{ background: #111; color: #fff; }}
                .btn-primary:hover {{ background: #333; }}
                .btn-gs1 {{ background: #fff; color: #333; border: 1px solid #ccc; }}
                .btn-gs1:hover {{ border-color: #999; background: #f5f5f5; }}
                .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 4px; }}
                @media (max-width: 640px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
                .demo-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
                @media (max-width: 640px) {{ .demo-grid {{ grid-template-columns: 1fr; }} }}
                .demo-card {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 16px; display: flex; flex-direction: column; gap: 8px; transition: border-color 0.15s; }}
                .demo-card:hover {{ border-color: #999; }}
                .demo-card-icon {{ width: 32px; height: 32px; background: #f5f5f5; border-radius: 6px; display: flex; align-items: center; justify-content: center; }}
                .demo-card h3 {{ font-size: 13px; font-weight: 700; color: #111; margin: 0; }}
                .demo-card p {{ font-size: 12px; color: #666; line-height: 1.4; flex: 1; margin: 0; }}
                .demo-card .demo-tags {{ display: flex; gap: 3px; flex-wrap: wrap; }}
                .demo-card .demo-tag {{ background: #f5f5f5; border: 1px solid #eee; color: #555; padding: 1px 6px; border-radius: 2px; font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }}
                .demo-card .btn {{ display: inline-block; }}
                .features {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
                @media (max-width: 768px) {{ .features {{ grid-template-columns: repeat(2, 1fr); }} }}
                .feature-card {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 12px; }}
                .feature-card h4 {{ color: #111; margin-bottom: 4px; font-size: 12px; font-weight: 700; }}
                .feature-card p {{ font-size: 11px; color: #666; line-height: 1.4; margin-bottom: 6px; }}
                .feature-card a {{ color: #2563eb; text-decoration: none; font-size: 11px; font-weight: 500; }}
                .feature-card a:hover {{ text-decoration: underline; }}
                .try-it {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 12px 14px; }}
                .try-it p {{ font-size: 12px; color: #555; }}
                .try-it strong {{ color: #111; }}
                .try-it code {{ background: #111; color: #a0ffa0; padding: 8px 12px; border-radius: 3px; display: block; font-size: 11px; overflow-x: auto; margin: 8px 0 4px; white-space: pre; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; }}
                .try-it .hint {{ font-size: 10px; color: #999; }}
                .footer {{ text-align: center; padding: 24px 0; color: #999; font-size: 11px; border-top: 1px solid #e5e5e5; margin-top: 32px; }}
                .footer a {{ color: #666; text-decoration: none; }}
                .footer a:hover {{ color: #111; }}
            </style>
        </head>
        <body>
            <div class="demo-banner">
                DEMO / PROOF OF CONCEPT — NOT an official DPP server — Sample data only — bS-Summit Porto
            </div>
            <div class="page">
                <div class="header">
                    <div class="header-text">
                        <h1>Digital Product Passport</h1>
                        <p>
                            Proof-of-concept <strong>prEN 18222:2025</strong> DPP API for construction products
                            — GS1 Digital Link, bSDD references, SHACL validation.
                        </p>
                        <div class="standards">
                            <span>prEN 18222</span>
                            <span>prEN 18223</span>
                            <span>GS1 Digital Link</span>
                            <span>bSDD</span>
                            <span>OWL + SHACL</span>
                            <span>EU CPR / DoPC</span>
                        </div>
                    </div>
                </div>
                <div class="disclaimer-inline">
                    <strong>Disclaimer:</strong> PoC demo (bS-Summit Porto). Not an official DPP system. Sample data only. Not affiliated with any manufacturer.
                </div>

                <h2 class="section-title">Sample Products</h2>
                <div class="product-grid">
                    {product_cards}
                </div>

                <h2 class="section-title">Demo Tools</h2>
                <div id="demo-grid" class="demo-grid">
                    <div class="demo-card">
                        <div class="demo-card-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
                        </div>
                        <h3>Create Your DPP</h3>
                        <p>Build a product passport from scratch. Define product properties, assign classifications, and generate a standards-compliant DPP.</p>
                        <div class="demo-tags">
                            <span class="demo-tag">prEN 18223</span>
                            <span class="demo-tag">JSON-LD</span>
                            <span class="demo-tag">Client-side</span>
                        </div>
                        <div>
                            <a class="btn btn-primary" onclick="openCreateForm();" style="cursor:pointer;">Get Started</a>
                        </div>
                    </div>
                    <div class="demo-card">
                        <div class="demo-card-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        </div>
                        <h3>Enrich IFC with DPP Data</h3>
                        <p>Upload an IFC file and enrich building elements with DPP data — property sets, bSDD classifications, EPD indicators, GS1 identifiers, and document references.</p>
                        <div class="demo-tags">
                            <span class="demo-tag">IFC 2x3 / 4</span>
                            <span class="demo-tag">bSDD</span>
                            <span class="demo-tag">EPD</span>
                            <span class="demo-tag">GS1</span>
                        </div>
                        <div>
                            <a href="/enrich/" class="btn btn-primary">Open Enrichment Tool</a>
                        </div>
                    </div>
                </div>

                <div id="create-section" hidden style="background:#fff;border:1px solid #e5e5e5;border-radius:3px;padding:24px;">
                    <div style="font-size:15px;font-weight:700;color:#111;margin-bottom:4px;">New Product Passport</div>
                    <div style="font-size:11px;color:#999;margin-bottom:16px;">Preview only. Runs in your browser, never sent to the server. Gone on reload.</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                        <div>
                            <label style="display:block;font-size:11px;font-weight:600;color:#555;margin-bottom:3px;text-transform:uppercase;letter-spacing:0.5px;">Product name</label>
                            <input id="cf-name" type="text" placeholder="e.g. CLT Panel 200mm" maxlength="80" style="width:100%;padding:7px 10px;border:1px solid #ddd;border-radius:3px;font-size:13px;font-family:inherit;outline:none;" onfocus="this.style.borderColor='#999'" onblur="this.style.borderColor='#ddd'">
                        </div>
                        <div>
                            <label style="display:block;font-size:11px;font-weight:600;color:#555;margin-bottom:3px;text-transform:uppercase;letter-spacing:0.5px;">Manufacturer</label>
                            <input id="cf-mfr" type="text" placeholder="e.g. Stora Enso" maxlength="80" style="width:100%;padding:7px 10px;border:1px solid #ddd;border-radius:3px;font-size:13px;font-family:inherit;outline:none;" onfocus="this.style.borderColor='#999'" onblur="this.style.borderColor='#ddd'">
                        </div>
                    </div>
                    <div style="margin-top:12px;">
                        <label style="display:block;font-size:11px;font-weight:600;color:#555;margin-bottom:3px;text-transform:uppercase;letter-spacing:0.5px;">Product type</label>
                        <select id="cf-type" style="width:100%;padding:7px 10px;border:1px solid #ddd;border-radius:3px;font-size:13px;font-family:inherit;background:#fff;outline:none;">
                            <option value="IfcBuildingElementProxy">General building element</option>
                            <option value="IfcSlab">Slab / panel</option>
                            <option value="IfcBeam">Beam / column</option>
                            <option value="IfcWall">Wall element</option>
                            <option value="IfcWindow">Window</option>
                            <option value="IfcDoor">Door</option>
                            <option value="IfcCovering">Insulation / covering</option>
                            <option value="IfcPipeSegment">Pipe segment</option>
                        </select>
                    </div>
                    <div style="display:flex;gap:8px;margin-top:16px;">
                        <button onclick="createLocalDpp()" style="padding:8px 20px;background:#111;color:#fff;border:none;border-radius:3px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;">Create</button>
                        <button onclick="closeCreateForm();" style="padding:8px 20px;background:#fff;color:#666;border:1px solid #ddd;border-radius:3px;font-size:12px;cursor:pointer;font-family:inherit;">Cancel</button>
                    </div>
                    <div id="cf-error" style="display:none;margin-top:8px;font-size:11px;color:#b91c1c;"></div>
                </div>
                <div id="user-dpps"></div>

                <script>
                function esc(s) {{ var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }}
                function openCreateForm() {{
                    document.getElementById('demo-grid').hidden = true;
                    document.getElementById('create-section').hidden = false;
                }}
                function closeCreateForm() {{
                    document.getElementById('create-section').hidden = true;
                    document.getElementById('demo-grid').hidden = false;
                }}
                function createLocalDpp() {{
                    var rawName = document.getElementById('cf-name').value.trim().substring(0, 80);
                    var rawMfr = document.getElementById('cf-mfr').value.trim().substring(0, 80);
                    var ifcType = document.getElementById('cf-type').value;
                    var errEl = document.getElementById('cf-error');
                    errEl.style.display = 'none';
                    if (!rawName || !rawMfr) {{ errEl.textContent = 'Product name and manufacturer are required.'; errEl.style.display = 'block'; return; }}
                    var name = esc(rawName);
                    var mfr = esc(rawMfr);
                    var type = esc(ifcType);
                    var card = '<div class="product-card" style="border-left:3px solid #16a34a;">'
                        + '<div class="product-header"><h3>' + name + '</h3><span class="operator">' + mfr + '</span></div>'
                        + '<div class="product-body"><div class="product-meta">'
                        + '<div style="font-size:11px;color:#999;">Client-side preview only</div>'
                        + '</div><div class="tags"><span class="tag">' + type + '</span><span class="tag">local preview</span></div></div>'
                        + '</div>';
                    document.getElementById('user-dpps').insertAdjacentHTML('beforeend', card);
                    document.getElementById('cf-name').value = '';
                    document.getElementById('cf-mfr').value = '';
                    closeCreateForm();
                }}
                </script>

                <div class="two-col">
                    <div>
                        <h2 class="section-title">Explore</h2>
                        <div class="features" style="grid-template-columns:1fr 1fr;">
                            <div class="feature-card">
                                <h4>OWL Ontology</h4>
                                <p>Formal DPP ontology — classes, properties, relationships.</p>
                                <a href="/ontology">View ontology</a>
                            </div>
                            <div class="feature-card">
                                <h4>SHACL Shapes</h4>
                                <p>Validation constraints for DPP data.</p>
                                <a href="/ontology/shacl">View shapes</a>
                            </div>
                            <div class="feature-card">
                                <h4>SHACL Validator</h4>
                                <p>Check DPP conformance against shapes.</p>
                                <a href="/docs#/Linked%20Data%20%26%20Ontology/validate_dpp_validate_post">Try validator</a>
                            </div>
                            <div class="feature-card">
                                <h4>API Documentation</h4>
                                <p>Interactive Swagger UI with examples.</p>
                                <a href="/docs">Open Swagger</a>
                            </div>
                        </div>
                    </div>
                    <div>
                        <h2 class="section-title">Content Negotiation</h2>
                        <div class="try-it">
                            <p>Same URL returns <strong>HTML</strong> in browser or <strong>JSON-LD</strong> via curl:</p>
                            <code>curl -H "Accept: application/ld+json" {BASE_URL}/id/01/04012345678901</code>
                            <p class="hint">Open in your browser for the HTML view with bSDD links and QR codes.</p>
                        </div>
                    </div>
                </div>

                <div class="footer">
                    bS-Summit Porto — buildingSMART International &middot;
                    <a href="/docs">API Docs</a> &middot;
                    <a href="/ontology">Ontology</a> &middot;
                    <a href="/ontology/shacl">SHACL</a>
                </div>
            </div>
        </body>
        </html>
        """)
    return {
        "name": "Lignum DPP API [DEMO]",
        "disclaimer": DEMO_DISCLAIMER,
        "version": "0.1.0-demo",
        "endpoints": {
            "landing_page": "/",
            "dpps": "/dpps",
            "docs": "/docs",
            "ontology": "/ontology",
            "shacl": "/ontology/shacl",
            "validate": "/validate",
            "health": "/health"
        }
    }

@app.post("/dpps", status_code=201, response_model=Dict, tags=["DPP CRUD"])
async def create_dpp(request: Request, response: Response):
    """Create a new Digital Product Passport.

    POST a JSON-LD DPP document. An `id` will be generated if not provided.
    """
    try:
        dpp_data = await request.json()
        
        # Validate required fields
        if "id" not in dpp_data:
            dpp_data["id"] = f"did:web:lignum.dev:dpp:{uuid.uuid4()}"
        
        dpp_id = dpp_data["id"]
        
        # Check if DPP already exists
        if dpp_id in dpp_storage:
            raise HTTPException(status_code=409, detail="DPP already exists")
        
        # Set metadata
        now = datetime.utcnow().isoformat() + "Z"
        dpp_data["dcterms:created"] = now
        dpp_data["dcterms:modified"] = now
        dpp_data["dpp:status"] = dpp_data.get("dpp:status", "active")
        
        # Add initial change log entry
        if "dpp:changeLog" not in dpp_data:
            dpp_data["dpp:changeLog"] = []
        
        dpp_data["dpp:changeLog"].append({
            "type": "dpp:ChangeEvent",
            "dpp:changeId": f"urn:uuid:{uuid.uuid4()}",
            "dpp:timestamp": now,
            "dpp:actor": {
                "type": "dpp:Agent",
                "schema:name": "API User"
            },
            "dpp:changeObject": "dpp:DigitalProductPassport",
            "dpp:changedProperties": ["initial creation"],
            "dpp:changeType": "create"
        })
        
        # Store DPP
        dpp_storage[dpp_id] = dpp_data
        
        # Set Location header
        response.headers["Location"] = f"/dpps/{dpp_id}"
        
        return dpp_data
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dpps", tags=["DPP CRUD"])
async def list_dpps(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    operatorId: Optional[str] = None
):
    """List DPPs with pagination"""
    dpps = list(dpp_storage.values())
    
    # Filter by operator if specified
    if operatorId:
        dpps = [
            dpp for dpp in dpps
            if dpp.get("dpp:economicOperator", {}).get("id") == operatorId
        ]
    
    # Pagination
    total = len(dpps)
    dpps = dpps[offset:offset + limit]
    
    # Create summaries
    items = []
    for dpp in dpps:
        items.append({
            "id": dpp.get("id"),
            "productIdentifiers": dpp.get("dpp:productIdentifiers", []),
            "status": dpp.get("dpp:status"),
            "modified": dpp.get("dcterms:modified")
        })
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/id/01/{gtin}", tags=["GS1 Digital Link"])
@app.get("/id/01/{gtin}/21/{serial}", tags=["GS1 Digital Link"])
@app.get("/id/01/{gtin}/10/{batch}", tags=["GS1 Digital Link"])
async def gs1_digital_link_resolver(request: Request, gtin: str, serial: Optional[str] = None, batch: Optional[str] = None):
    """Resolve a GS1 Digital Link URI to a DPP.

    This is what happens when someone scans a QR code on a physical product.
    The URI contains the GTIN (AI 01) and optionally a serial number (AI 21) or batch (AI 10).

    **Try these GTINs:**
    - `04012345678901` — Knauf Acoustic Batt
    - `07640123456789` — Schilliger Glulam GL24h
    - `05790001234561` — PVC Sewage Pipe DN110

    Returns HTML in browser, JSON-LD otherwise (content negotiation).
    """
    candidates: List[Dict] = []
    for dpp in dpp_storage.values():
        for pid in dpp.get("dpp:productIdentifiers", []):
            if pid.get("dpp:scheme") == "gtin" and pid.get("dpp:value") == gtin:
                candidates.append(dpp)
                break

    if not candidates:
        raise HTTPException(status_code=404, detail="No DPP found for GTIN")

    # Narrow by serial (AI 21) or batch/lot (AI 10) when multiple candidates
    qualifier = serial or batch
    if qualifier and len(candidates) > 1:
        narrowed: List[Dict] = []
        for dpp in candidates:
            for pid in dpp.get("dpp:productIdentifiers", []):
                if pid.get("dpp:value") == qualifier:
                    narrowed.append(dpp)
                    break
        if narrowed:
            candidates = narrowed

    resolved = candidates[0]
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(content=render_dpp_as_html(resolved))
    return JSONResponse(content=resolved, media_type="application/ld+json")

@app.get("/dpps/{dpp_id}", tags=["DPP CRUD"])
async def read_dpp_by_id(dpp_id: str, request: Request):
    """Get a DPP by ID (content negotiation).

    Returns **HTML** in a browser (with bSDD links, QR codes, DoPC data)
    or **JSON-LD** when requested via `Accept: application/ld+json`.

    **Try these IDs:**
    - `did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001`
    - `did:web:lignum.dev:dpp:schilliger-bsh-gl24h-2022-001`
    - `did:web:lignum.dev:dpp:pvc-sewage-dn110-2025-001`
    """
    # URL decode the ID
    dpp_id = unquote(dpp_id)
    
    if dpp_id not in dpp_storage:
        # Allow lookup by full localhost URL id as well
        base_url = str(request.base_url).rstrip("/")
        candidate_full = f"{base_url}/dpps/{dpp_id}"
        if candidate_full in dpp_storage:
            dpp_id = candidate_full
        else:
            raise HTTPException(status_code=404, detail="DPP not found")
    
    dpp = dpp_storage[dpp_id]
    
    # Check Accept header for content negotiation
    accept = request.headers.get("accept", "application/json")
    
    if "text/html" in accept:
        return HTMLResponse(content=render_dpp_as_html(dpp))
    else:
        return JSONResponse(content=dpp, media_type="application/ld+json")

@app.patch("/dpps/{dpp_id}", tags=["DPP CRUD"])
async def update_dpp_by_id(dpp_id: str, request: Request):
    """Update a DPP using JSON Merge Patch (RFC 7396)."""
    dpp_id = unquote(dpp_id)

    if dpp_id not in dpp_storage:
        raise HTTPException(status_code=404, detail="DPP not found")

    if DEMO_PROTECTED and dpp_id in _seed_dpp_ids:
        raise HTTPException(
            status_code=403,
            detail="Demo mode: seed product DPPs are protected and cannot be modified."
        )

    try:
        patch_data = await request.json()
        
        # Apply JSON Merge Patch
        current_dpp = dpp_storage[dpp_id].copy()
        
        # Simple merge (implement full RFC 7396 for production)
        def merge_patch(target, patch):
            for key, value in patch.items():
                if value is None:
                    target.pop(key, None)
                elif isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    merge_patch(target[key], value)
                else:
                    target[key] = value
        
        merge_patch(current_dpp, patch_data)
        
        # Update metadata
        now = datetime.utcnow().isoformat() + "Z"
        current_dpp["dcterms:modified"] = now
        
        # Add change log entry
        if "dpp:changeLog" not in current_dpp:
            current_dpp["dpp:changeLog"] = []
        
        current_dpp["dpp:changeLog"].append({
            "type": "dpp:ChangeEvent",
            "dpp:changeId": f"urn:uuid:{uuid.uuid4()}",
            "dpp:timestamp": now,
            "dpp:actor": {
                "type": "dpp:Agent",
                "schema:name": "API User"
            },
            "dpp:changeObject": "dpp:DigitalProductPassport",
            "dpp:changedProperties": list(patch_data.keys()),
            "dpp:changeType": "update"
        })
        
        # Store updated DPP
        dpp_storage[dpp_id] = current_dpp
        
        return JSONResponse(content=current_dpp, media_type="application/ld+json")
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/dpps/{dpp_id}", status_code=204, tags=["DPP CRUD"])
async def delete_dpp_by_id(dpp_id: str):
    """Delete a DPP by ID."""
    dpp_id = unquote(dpp_id)

    if dpp_id not in dpp_storage:
        raise HTTPException(status_code=404, detail="DPP not found")

    if DEMO_PROTECTED and dpp_id in _seed_dpp_ids:
        raise HTTPException(
            status_code=403,
            detail="Demo mode: seed product DPPs are protected and cannot be deleted."
        )

    del dpp_storage[dpp_id]
    return Response(status_code=204)

@app.get("/dppsByProductId/{product_id}", tags=["DPP CRUD"])
async def read_dpp_by_product_id(product_id: str):
    """Get a DPP by product identifier (GTIN, MPN, etc.)."""
    # Search for DPP with matching product ID
    for dpp in dpp_storage.values():
        for pid in dpp.get("dpp:productIdentifiers", []):
            if pid.get("dpp:value") == product_id:
                return JSONResponse(content=dpp, media_type="application/ld+json")
    
    raise HTTPException(status_code=404, detail="DPP not found for product ID")

@app.get("/dppsByProductId/{product_id}/versions", tags=["DPP CRUD"])
async def read_dpp_version_by_date(product_id: str, date: str):
    """Get DPP version at a specific date (PoC)."""
    # This would require version history storage
    # For now, return current version if it exists
    for dpp in dpp_storage.values():
        for pid in dpp.get("dpp:productIdentifiers", []):
            if pid.get("dpp:value") == product_id:
                # Check if date is before creation
                created = dpp.get("dcterms:created", "")
                if date < created:
                    raise HTTPException(status_code=404, detail="No version exists for this date")
                return JSONResponse(content=dpp, media_type="application/ld+json")
    
    raise HTTPException(status_code=404, detail="DPP not found for product ID")

@app.post("/registerDPP", status_code=201, tags=["Registry"])
async def register_dpp(registry_request: RegistryRequest):
    """Register a DPP with the EU registry (PoC simulation)."""
    # Generate registry ID
    registry_id = generate_registry_id()
    registry_url = f"/registry/{registry_id.split(':')[-1]}"
    
    # Store registry entry
    registry_storage[registry_id] = {
        "registryId": registry_id,
        "dppId": registry_request.dppId,
        "productIdentifiers": registry_request.productIdentifiers,
        "economicOperatorId": registry_request.economicOperatorId,
        "backupOperatorId": registry_request.backupOperatorId,
        "registeredAt": datetime.utcnow().isoformat() + "Z"
    }
    
    # Update DPP with registry info if it exists
    if registry_request.dppId in dpp_storage:
        dpp_storage[registry_request.dppId]["dpp:registry"] = {
            "id": registry_id,
            "schema:url": registry_url
        }
    
    return RegistryResponse(registryId=registry_id, registryUrl=registry_url)

@app.get("/registry/{registry_suffix}", tags=["Registry"])
async def get_registry_entry(registry_suffix: str):
    """Look up a registry entry (PoC simulation)."""
    key = None
    for rid in registry_storage.keys():
        if rid.endswith(registry_suffix):
            key = rid
            break
    if not key:
        raise HTTPException(status_code=404, detail="Registry entry not found")
    return registry_storage[key]

@app.get("/dpps/{dpp_id}/dataElements/{collection_id}", tags=["Data Elements"])
async def read_data_element_collection(dpp_id: str, collection_id: str):
    """Get a specific data element collection from a DPP.

    Collection IDs: `productProperties`, `epd`, `dopc`, `documents`, `carrier`, `classification`
    """
    dpp_id = unquote(dpp_id)
    
    if dpp_id not in dpp_storage:
        raise HTTPException(status_code=404, detail="DPP not found")
    
    dpp = dpp_storage[dpp_id]
    
    # Find collection by ID (without #)
    collection_id = collection_id if not collection_id.startswith('#') else collection_id[1:]
    
    for collection in dpp.get("dpp:dataElementCollections", []):
        coll_id = collection.get("id", "").lstrip("#")
        if coll_id == collection_id:
            return collection
    
    raise HTTPException(status_code=404, detail="Collection not found")

@app.patch("/dpps/{dpp_id}/dataElements/{collection_id}", tags=["Data Elements"])
async def update_data_element_collection(dpp_id: str, collection_id: str, request: Request):
    """Update a data element collection via JSON Merge Patch."""
    dpp_id = unquote(dpp_id)

    if dpp_id not in dpp_storage:
        raise HTTPException(status_code=404, detail="DPP not found")

    if DEMO_PROTECTED and dpp_id in _seed_dpp_ids:
        raise HTTPException(
            status_code=403,
            detail="Demo mode: seed product DPPs are protected and cannot be modified."
        )

    try:
        patch_data = await request.json()
        dpp = dpp_storage[dpp_id]
        
        collection_id = collection_id if not collection_id.startswith('#') else collection_id[1:]
        
        # Find and update collection
        for i, collection in enumerate(dpp.get("dpp:dataElementCollections", [])):
            coll_id = collection.get("id", "").lstrip("#")
            if coll_id == collection_id:
                # Apply patch
                def merge_patch(target, patch):
                    for key, value in patch.items():
                        if value is None:
                            target.pop(key, None)
                        elif isinstance(value, dict) and key in target and isinstance(target[key], dict):
                            merge_patch(target[key], value)
                        else:
                            target[key] = value
                
                merge_patch(dpp["dpp:dataElementCollections"][i], patch_data)
                
                # Update DPP metadata
                now = datetime.utcnow().isoformat() + "Z"
                dpp["dcterms:modified"] = now
                
                # Add change log
                if "dpp:changeLog" not in dpp:
                    dpp["dpp:changeLog"] = []
                
                dpp["dpp:changeLog"].append({
                    "type": "dpp:ChangeEvent",
                    "dpp:changeId": f"urn:uuid:{uuid.uuid4()}",
                    "dpp:timestamp": now,
                    "dpp:actor": {
                        "type": "dpp:Agent",
                        "schema:name": "API User"
                    },
                    "dpp:changeObject": f"dpp:DataElementCollection#{collection_id}",
                    "dpp:changedProperties": list(patch_data.keys()),
                    "dpp:changeType": "update"
                })
                
                dpp_storage[dpp_id] = dpp
                return dpp["dpp:dataElementCollections"][i]
        
        raise HTTPException(status_code=404, detail="Collection not found")
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

@app.get("/dpps/{dpp_id}/dataElements/{collection_id}/{element_id}", tags=["Data Elements"])
async def read_data_element(dpp_id: str, collection_id: str, element_id: str):
    """Get a specific data element within a collection."""
    dpp_id = unquote(dpp_id)
    
    if dpp_id not in dpp_storage:
        raise HTTPException(status_code=404, detail="DPP not found")
    
    dpp = dpp_storage[dpp_id]
    
    collection_id = collection_id if not collection_id.startswith('#') else collection_id[1:]
    element_id = element_id if not element_id.startswith('#') else element_id[1:]
    
    # Find collection and element
    for collection in dpp.get("dpp:dataElementCollections", []):
        coll_id = collection.get("id", "").lstrip("#")
        if coll_id == collection_id:
            for element in collection.get("dpp:elements", []):
                elem_id = element.get("id", "").lstrip("#")
                if elem_id == element_id:
                    return element
    
    raise HTTPException(status_code=404, detail="Element not found")

def _find_ontology_file(filename: str) -> Path:
    """Locate an ontology file, checking api/data first (Vercel), then project root."""
    api_path = Path(__file__).parent
    for candidate in [api_path / "data" / "ontology" / filename,
                      api_path.parent / "ontology" / filename]:
        if candidate.exists():
            return candidate
    return api_path.parent / "ontology" / filename  # fallback for error msg

@app.get("/ontology", tags=["Linked Data & Ontology"])
async def get_ontology():
    """Get the DPP OWL ontology (JSON-LD).

    Returns the formal OWL ontology defining DPP classes and properties.
    Use this to understand the DPP data model and its linked-data semantics.
    """
    ontology_path = _find_ontology_file("dpp-ontology.jsonld")
    if not ontology_path.exists():
        raise HTTPException(status_code=404, detail="Ontology file not found")
    with open(ontology_path, 'r') as f:
        ontology = json.load(f)
    return JSONResponse(content=ontology, media_type="application/ld+json")

@app.get("/ontology/shacl", tags=["Linked Data & Ontology"])
async def get_shacl_shapes():
    """Get SHACL validation shapes (JSON-LD).

    Returns the SHACL shapes graph that defines constraints on DPP instances.
    These shapes are used by the /validate endpoint.
    """
    shacl_path = _find_ontology_file("dpp-shacl.jsonld")
    if not shacl_path.exists():
        raise HTTPException(status_code=404, detail="SHACL shapes file not found")
    with open(shacl_path, 'r') as f:
        shapes = json.load(f)
    return JSONResponse(content=shapes, media_type="application/ld+json")

VALIDATE_EXAMPLE = {
    "summary": "Minimal DPP",
    "description": "A minimal DPP document to test validation. Try also fetching a full DPP from /dpps/{id} and POSTing it here.",
    "value": {
        "@context": {"dpp": "https://w3id.org/dpp#", "dcterms": "http://purl.org/dc/terms/", "schema": "https://schema.org/"},
        "id": "did:web:example.com:dpp:test-001",
        "type": "dpp:DigitalProductPassport",
        "dpp:status": "active",
        "dpp:dppSchemaVersion": "1.0.0",
        "dcterms:created": "2025-01-01T00:00:00Z",
        "dcterms:modified": "2025-01-01T00:00:00Z",
        "dpp:economicOperator": {"type": "schema:Organization", "schema:name": "Test Corp"},
        "dpp:productIdentifiers": [{"dpp:scheme": "gtin", "dpp:value": "01234567890123"}],
        "dpp:dataElementCollections": []
    }
}

@app.post("/validate", tags=["Linked Data & Ontology"],
           openapi_extra={
               "requestBody": {
                   "required": True,
                   "content": {
                       "application/json": {
                           "schema": {"type": "object"},
                           "example": VALIDATE_EXAMPLE["value"]
                       }
                   }
               }
           })
async def validate_dpp(request: Request):
    """Validate a DPP JSON-LD against SHACL shapes.

    POST a full DPP JSON-LD document and receive a SHACL-style validation report.

    **Tip:** Copy a DPP from `GET /dpps/{id}` and paste it here to validate,
    or use the minimal example provided.
    """
    try:
        dpp = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Load SHACL shapes
    shacl_path = _find_ontology_file("dpp-shacl.jsonld")
    if not shacl_path.exists():
        raise HTTPException(status_code=500, detail="SHACL shapes file not found")
    shapes = json.loads(shacl_path.read_text(encoding="utf-8"))

    # Build a lookup of shapes by @id
    shape_map: Dict[str, Dict] = {}
    for node in shapes.get("@graph", []):
        if node.get("@id"):
            shape_map[node["@id"]] = node

    findings: List[Dict[str, Any]] = []
    conforms = True

    def _check_value_type(val, expected_dt: str) -> bool:
        """Loose datatype check for demo purposes."""
        if expected_dt in ("xsd:string", "xsd:anyURI"):
            return isinstance(val, str)
        if expected_dt == "xsd:double":
            return isinstance(val, (int, float))
        if expected_dt in ("xsd:date", "xsd:dateTime"):
            return isinstance(val, str) and len(val) >= 8
        return True

    def _validate_node(data: Any, shape_id: str, path_prefix: str):
        nonlocal conforms
        shape = shape_map.get(shape_id)
        if not shape or not isinstance(data, dict):
            return

        props = shape.get("sh:property", [])
        if isinstance(props, dict):
            props = [props]

        for prop in props:
            prop_path = prop.get("sh:path", "")
            min_count = prop.get("sh:minCount", 0)
            datatype = prop.get("sh:datatype", "")
            allowed = None
            sh_in = prop.get("sh:in")
            if isinstance(sh_in, dict):
                allowed = sh_in.get("@list")

            full_path = f"{path_prefix}.{prop_path}" if path_prefix else prop_path
            val = data.get(prop_path)

            # Required check
            if min_count and min_count >= 1 and val is None:
                conforms = False
                findings.append({
                    "severity": "Violation",
                    "path": full_path,
                    "shape": shape_id,
                    "message": f"Required property '{prop_path}' is missing"
                })
                continue

            if val is None:
                continue

            # Datatype check (single values)
            if datatype and not isinstance(val, (list, dict)):
                if not _check_value_type(val, datatype):
                    conforms = False
                    findings.append({
                        "severity": "Violation",
                        "path": full_path,
                        "shape": shape_id,
                        "message": f"Expected {datatype}, got {type(val).__name__}"
                    })

            # Allowed values check
            if allowed is not None and val not in allowed:
                conforms = False
                findings.append({
                    "severity": "Violation",
                    "path": full_path,
                    "shape": shape_id,
                    "message": f"Value '{val}' not in allowed set {allowed}"
                })

            # Recurse into nested node shapes
            nested_shape = prop.get("sh:node")
            if nested_shape:
                items = val if isinstance(val, list) else [val]
                for item in items:
                    if isinstance(item, dict):
                        _validate_node(item, nested_shape, full_path)

            # sh:or — accept if any branch passes
            sh_or = prop.get("sh:or")
            if sh_or and isinstance(val, list):
                or_list = sh_or.get("@list", []) if isinstance(sh_or, dict) else []
                for item in val:
                    if isinstance(item, dict):
                        matched = False
                        for branch in or_list:
                            branch_node = branch.get("sh:node")
                            if branch_node and branch_node in shape_map:
                                # Quick check: see if required props exist
                                bs = shape_map[branch_node]
                                bprops = bs.get("sh:property", [])
                                if isinstance(bprops, dict):
                                    bprops = [bprops]
                                req_ok = all(
                                    item.get(bp.get("sh:path")) is not None
                                    for bp in bprops
                                    if bp.get("sh:minCount", 0) >= 1
                                )
                                if req_ok:
                                    matched = True
                                    _validate_node(item, branch_node, full_path)
                                    break
                        if not matched:
                            findings.append({
                                "severity": "Warning",
                                "path": full_path,
                                "shape": "sh:or",
                                "message": f"Element did not match any branch in sh:or"
                            })

    # Validate top-level DPP shape
    _validate_node(dpp, "dpp:DigitalProductPassportShape", "")

    # Validate nested collections
    for coll in dpp.get("dpp:dataElementCollections", []):
        coll_path = f"dpp:dataElementCollections[{coll.get('id', '?')}]"
        _validate_node(coll, "dpp:DataElementCollectionShape", coll_path)

    return {
        "conforms": conforms,
        "resultsCount": len(findings),
        "results": findings,
        "shapesUsed": "dpp-shacl.jsonld",
        "disclaimer": "Lightweight SHACL validation (demo) — not a full RDF/SHACL engine."
    }

@app.get("/favicon.svg", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve SVG favicon for browsers."""
    return Response(content=FAVICON_SVG, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=604800"})


@app.get("/health", tags=["System"])
async def health_check():
    """Health check — shows loaded DPP count."""
    return {
        "status": "healthy",
        "dpps_loaded": len(dpp_storage),
        "registry_entries": len(registry_storage)
    }

@app.post("/admin/reload", tags=["System"])
async def reload_dpps():
    """Reload DPP files from disk (admin)."""
    if DEMO_PROTECTED:
        raise HTTPException(
            status_code=403,
            detail="Demo mode: admin reload is disabled to protect demo data."
        )
    dpp_storage.clear()
    load_sample_dpps()
    return {
        "message": "DPPs reloaded from disk",
        "dpps_loaded": len(dpp_storage)
    }

# --- Module-level initialization (Vercel doesn't reliably call ASGI startup events) ---
# Mount static files AFTER all routes (mount is a catch-all)
_api_path = Path(__file__).parent
_base_path = _api_path.parent
# Serve PDFs: check api/data/files (Vercel), then project root data/, then legacy vLignum/
_files_dir = _api_path / "data" / "files"
if not _files_dir.exists():
    _files_dir = _base_path / "data"
if not _files_dir.exists():
    _files_dir = _base_path / "vLignum"
if _files_dir.exists():
    app.mount("/files", StaticFiles(directory=str(_files_dir)), name="files")

# Serve IFC enrichment tool static assets
_enrich_dir = _api_path / "static" / "enrich"
if _enrich_dir.exists():
    app.mount("/enrich", StaticFiles(directory=str(_enrich_dir), html=True), name="enrich")

# Load sample DPPs
load_sample_dpps()
print(f"DPP API initialized with {len(dpp_storage)} sample DPPs (BASE_URL={BASE_URL})")

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port_env = os.getenv("PORT", "8000")
    try:
        port = int(port_env)
    except ValueError:
        port = 8000

    reload_flag = os.getenv("RELOAD", "true").lower() in ("1", "true", "yes", "on")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_flag,
        log_level="info"
    )
