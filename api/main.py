"""
buildingSMART DPP API Server [DEMO]
Proof-of-concept conforming to prEN 18222:2025 - API specification
NOT an official Digital Product Passport server.
"""

import json
import hashlib
import html as html_module
import uuid
from _landing_page import build_landing_html
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

# SVG favicon — stylised tree-ring cross-section
FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#fff"/>
  <circle cx="16" cy="16" r="11" fill="none" stroke="#8b6f47" stroke-width="1.5" opacity=".35"/>
  <circle cx="16" cy="16" r="8" fill="none" stroke="#8b6f47" stroke-width="1.5" opacity=".5"/>
  <circle cx="16" cy="16" r="5" fill="none" stroke="#8b6f47" stroke-width="1.5" opacity=".7"/>
  <circle cx="16" cy="16" r="2" fill="#8b6f47"/>
</svg>"""

FAVICON_DATA_URI = "data:image/svg+xml," + FAVICON_SVG.replace("#", "%23").replace("\n", "").replace("  ", "")

# Floating QR code widget — dynamically encodes current page URL so demo attendees can follow along on mobile.
QR_CODE_WIDGET = """
<div id="qr-widget" style="position:fixed;bottom:20px;right:20px;z-index:9999;background:#fff;border:1px solid #e5e0da;border-radius:10px;padding:10px;box-shadow:0 4px 20px rgba(0,0,0,0.12);display:flex;flex-direction:column;align-items:center;gap:4px;transition:opacity 0.2s;">
  <img id="qr-img" width="90" height="90" style="border-radius:4px;" alt="QR code for this page">
  <span style="font-size:9px;color:#999;font-family:sans-serif;">Scan to follow along</span>
  <button onclick="this.parentElement.style.display='none'" style="position:absolute;top:2px;right:6px;background:none;border:none;color:#ccc;cursor:pointer;font-size:14px;line-height:1;">&times;</button>
</div>
<script>
(function(){var q=document.getElementById('qr-img');if(q){var u=encodeURIComponent(location.href);q.src='https://api.qrserver.com/v1/create-qr-code/?size=180x180&data='+u;}})();
</script>
"""

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
    title="buildingSMART DPP API [DEMO] — bS-Summit Porto",
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
    <meta name="theme-color" content="#2c2418">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <title>{esc(product_name)} &mdash; DPP [DEMO]</title>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{ --oak: #6b5534; --oak-light: #a68b5b; --oak-muted: #c4a97d; --ink: #1e1a14; --ink-soft: #4a4035; --muted: #8a7e70; --border: #e5e0da; --border-light: #f0ece6; --card: #fff; --radius: 8px; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Outfit', 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #fff; color: var(--ink); min-height: 100vh; line-height: 1.6; -webkit-font-smoothing: antialiased; }}
        .demo-banner {{ position: fixed; top: 0; left: 0; right: 0; z-index: 9999; background: var(--ink); color: #a09080; text-align: center; padding: 8px 20px; font-size: 11px; font-weight: 400; letter-spacing: 0.2px; }}
        .container {{ max-width: 860px; margin: 0 auto; padding: 52px 24px 48px; }}
        .header {{ margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid var(--border); }}
        .header h1 {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 1.85em; font-weight: 700; color: var(--ink); margin-bottom: 4px; letter-spacing: -0.02em; }}
        .header .operator {{ font-size: 0.95em; color: var(--muted); font-weight: 300; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 1px; margin: 24px 0; background: var(--border); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }}
        .meta-item {{ background: #fafaf8; padding: 14px 16px; }}
        .meta-item .lbl {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); margin-bottom: 4px; font-weight: 600; }}
        .meta-item .val {{ font-size: 13px; color: var(--ink); word-break: break-all; }}
        .meta-item .val code {{ background: var(--border-light); padding: 2px 5px; border-radius: 4px; font-size: 12px; color: var(--ink-soft); font-family: 'JetBrains Mono', 'SF Mono', Monaco, monospace; }}
        .status {{ display: inline-block; padding: 2px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
        .status-active {{ background: #dcfce7; color: #166534; }}
        .section {{ margin: 32px 0; }}
        .section-title {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 15px; font-weight: 600; color: var(--ink); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid var(--ink); text-transform: uppercase; letter-spacing: 0.5px; }}
        .card {{ background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 12px; }}
        .prop-row {{ display: flex; justify-content: space-between; align-items: baseline; padding: 8px 0; border-bottom: 1px solid var(--border-light); }}
        .prop-row:last-child {{ border-bottom: none; }}
        .prop-name {{ font-size: 13px; color: var(--ink-soft); flex: 1; }}
        .prop-value {{ font-size: 13px; font-weight: 600; color: var(--ink); text-align: right; }}
        .prop-unit {{ font-size: 12px; color: var(--muted); margin-left: 4px; font-weight: 400; }}
        .bsdd-link {{ display: inline-block; margin-left: 6px; padding: 1px 6px; background: #f0f7ff; border: 1px solid #c5d9ed; border-radius: 4px; font-size: 10px; color: #2563eb; text-decoration: none; font-weight: 600; letter-spacing: 0.3px; }}
        .bsdd-link:hover {{ background: #dbeafe; }}
        .dopc-header {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: var(--radius); padding: 16px; margin-bottom: 14px; }}
        .dopc-header strong {{ color: #1e40af; font-size: 14px; }}
        .dopc-meta {{ font-size: 13px; color: var(--ink-soft); line-height: 1.8; }}
        .doc-item {{ display: flex; align-items: center; gap: 10px; padding: 12px 14px; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 6px; text-decoration: none; color: var(--ink); transition: border-color 0.15s; }}
        .doc-item:hover {{ border-color: var(--oak-muted); }}
        .doc-badge {{ font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 8px; border-radius: 4px; white-space: nowrap; }}
        .doc-badge-dop {{ background: #fef3c7; color: #92400e; }}
        .doc-badge-epd {{ background: #d1fae5; color: #065f46; }}
        .doc-badge-sheet {{ background: #e0e7ff; color: #3730a3; }}
        .doc-icon {{ font-size: 16px; color: var(--muted); }}
        .doc-name {{ font-size: 13px; font-weight: 500; }}
        .indicator-table {{ width: 100%; border-collapse: collapse; }}
        .indicator-table th {{ background: #fafaf8; color: var(--ink-soft); padding: 10px 14px; text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; border-bottom: 2px solid var(--border); }}
        .indicator-table td {{ padding: 9px 14px; border-bottom: 1px solid var(--border-light); font-size: 13px; color: var(--ink-soft); }}
        .indicator-table tr:hover td {{ background: #fafaf8; }}
        .carrier-card {{ background: #fafaf8; border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; text-align: center; }}
        .carrier-card h3 {{ font-family: 'Source Serif 4', Georgia, serif; color: var(--ink); margin-bottom: 12px; font-size: 15px; font-weight: 600; }}
        .carrier-card img {{ margin: 12px auto; display: block; }}
        .carrier-card code {{ display: block; background: var(--border-light); padding: 10px; border-radius: 6px; font-size: 11px; color: var(--ink-soft); margin-top: 12px; word-break: break-all; font-family: 'JetBrains Mono', 'SF Mono', Monaco, monospace; }}
        .carrier-card .gs1-label {{ font-size: 11px; color: var(--muted); margin-top: 8px; }}
        .class-card {{ display: flex; align-items: center; gap: 16px; padding: 16px; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 8px; }}
        .class-info {{ flex: 1; }}
        .class-info .scheme {{ font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }}
        .class-info .name {{ font-family: 'Source Serif 4', Georgia, serif; font-size: 15px; font-weight: 600; color: var(--ink); margin: 4px 0; }}
        .class-info a {{ color: var(--oak); font-size: 12px; text-decoration: none; }}
        .class-info a:hover {{ text-decoration: underline; }}
        .json-toggle {{ display: inline-block; margin-top: 20px; padding: 7px 16px; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); color: var(--ink-soft); font-size: 13px; text-decoration: none; font-weight: 500; transition: border-color 0.15s; }}
        .json-toggle:hover {{ background: #fafaf8; border-color: var(--oak-muted); }}
        .footer {{ text-align: center; padding: 28px 0; color: var(--muted); font-size: 12px; margin-top: 24px; border-top: 1px solid var(--border); font-weight: 300; }}
        .footer a {{ color: var(--oak); text-decoration: none; font-weight: 400; }}
        .footer a:hover {{ color: var(--ink); }}
        a.back-link {{ color: var(--oak); text-decoration: none; font-size: 13px; font-weight: 400; }}
        a.back-link:hover {{ color: var(--ink); }}
    </style>
</head>
<body>
    <div class="demo-banner">
        DEMO &middot; Proof of concept &middot; Sample data only &middot; buildingSMART Summit Porto
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
            # Group documents by category
            docs_by_cat: list[tuple[str, str, str, str]] = []  # (category, badge_class, fname, url)
            for element in elements:
                if element.get("type") == "dpp:Document":
                    fname = str(element.get("dpp:fileName", "Document"))
                    url = str(element.get("schema:url", "#"))
                    eid = str(element.get("id", ""))
                    fl = fname.lower()
                    el = eid.lower()
                    if "dop" in el or "declaration" in el or "dop" in fl or "leistungserkl" in fl:
                        docs_by_cat.append(("DoP", "doc-badge-dop", fname, url))
                    elif "epd" in el or "epd" in fl or "nepd" in fl:
                        docs_by_cat.append(("EPD", "doc-badge-epd", fname, url))
                    else:
                        docs_by_cat.append(("Product Sheet", "doc-badge-sheet", fname, url))
            # Sort: DoP first, then EPD, then Product Sheet
            cat_order = {"DoP": 0, "EPD": 1, "Product Sheet": 2}
            docs_by_cat.sort(key=lambda x: cat_order.get(x[0], 9))
            for cat, badge_cls, fname, url in docs_by_cat:
                html += f'<a href="{esc(url)}" class="doc-item" target="_blank"><span class="doc-badge {badge_cls}">{esc(cat)}</span><span class="doc-name">{esc(fname)}</span></a>'
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
        <pre id="json-panel" style="display:none;background:#fafaf8;border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-top:16px;overflow-x:auto;font-size:12px;color:var(--ink-soft);max-height:600px;overflow-y:auto;font-family:'JetBrains Mono','SF Mono',Monaco,monospace;"><code id="json-view"></code></pre>
        <div class="footer">
            <a href="/">Home</a> &middot;
            <a href="/docs">API Docs</a> &middot;
            <a href="/ontology">Ontology</a><br>
            bS-Summit Porto — buildingSMART International
        </div>
    </div>
{QR_CODE_WIDGET}
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

        return HTMLResponse(content=build_landing_html(
            product_cards_html=product_cards,
            meta_description=META_DESCRIPTION,
            base_url=BASE_URL,
            qr_code_widget=QR_CODE_WIDGET,
        ))
    return {
        "name": "buildingSMART DPP API [DEMO]",
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
            dpp_data["id"] = f"did:web:bsi-dpp.org:dpp:{uuid.uuid4()}"
        
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
    - `did:web:bsi-dpp.org:dpp:knauf-acoustic-batt-2025-001`
    - `did:web:bsi-dpp.org:dpp:schilliger-bsh-gl24h-2022-001`
    - `did:web:bsi-dpp.org:dpp:pvc-sewage-dn110-2025-001`
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
# Serve PDFs: check api/data/files (Vercel), then project root data/
_files_dir = _api_path / "data" / "files"
if not _files_dir.exists():
    _files_dir = _base_path / "data"
if _files_dir.exists():
    app.mount("/files", StaticFiles(directory=str(_files_dir)), name="files")

# Serve IFC enrichment tool static assets
_enrich_dir = _api_path / "static" / "enrich"
if _enrich_dir.exists():
    app.mount("/enrich", StaticFiles(directory=str(_enrich_dir), html=True), name="enrich")

# Serve emissions calculator static assets
_emissions_dir = _api_path / "static" / "emissions"
if _emissions_dir.exists():
    app.mount("/emissions", StaticFiles(directory=str(_emissions_dir), html=True), name="emissions")

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
