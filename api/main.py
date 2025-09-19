"""
Lignum DPP API Server
Conforming to prEN 18222:2025 - API specification
"""

import json
import hashlib
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

# Initialize FastAPI app
app = FastAPI(
    title="Lignum DPP API",
    description="Digital Product Passport API conforming to prEN 18222:2025",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
dpp_storage: Dict[str, Dict] = {}
registry_storage: Dict[str, Dict] = {}

# Load sample DPPs from JSON-LD files
def load_sample_dpps():
    """Load sample DPP files from dpp/products directory"""
    base_path = Path(__file__).parent.parent
    dpp_dir = base_path / "dpp" / "products"
    if not dpp_dir.exists():
        # Fallback to legacy project root (pre‑refactor)
        candidates = [
            base_path / "dpp_knauf_acoustic_batt.jsonld",
            base_path / "dpp_schilliger_glulam.jsonld",
            base_path / "dpp_pvc_sewage_pipe.jsonld",
        ]
    else:
        candidates = sorted(dpp_dir.glob("*.jsonld"))

    for filepath in candidates:
        try:
            with open(filepath, 'r') as f:
                dpp_data = json.load(f)
            dpp_id = dpp_data.get("id")
            if dpp_id:
                dpp_storage[dpp_id] = dpp_data
                print(f"Loaded sample DPP: {dpp_id}")
        except Exception as e:
            print(f"Warning: failed to load DPP {filepath}: {e}")

# Load samples on startup
@app.on_event("startup")
async def startup_event():
    load_sample_dpps()
    print(f"DPP API started with {len(dpp_storage)} sample DPPs loaded")
    # Mount local static files for documents used in DPPs
    base_path = Path(__file__).parent.parent
    # Prefer new /data directory; fallback to legacy vLignum
    data_dir = base_path / "data"
    legacy_dir = base_path / "vLignum"
    mount_dir = data_dir if data_dir.exists() else legacy_dir if legacy_dir.exists() else None
    if mount_dir is not None:
        try:
            app.mount("/files", StaticFiles(directory=str(mount_dir)), name="files")
        except Exception:
            # Already mounted
            pass

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
    """Render DPP as HTML for human viewing"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Digital Product Passport</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            h3 {{ color: #7f8c8d; }}
            .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
            .info-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }}
            .label {{ font-weight: bold; color: #555; }}
            .value {{ color: #333; margin-left: 10px; }}
            .collection {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
            .element {{ margin: 10px 0; padding: 10px; background: white; border-radius: 5px; }}
            .indicator-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            .indicator-table th {{ background: #3498db; color: white; padding: 10px; text-align: left; }}
            .indicator-table td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            .document-link {{ color: #3498db; text-decoration: none; }}
            .document-link:hover {{ text-decoration: underline; }}
            .qr-section {{ margin: 30px 0; padding: 20px; background: #ecf0f1; border-radius: 8px; text-align: center; }}
            .status-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; background: #27ae60; color: white; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Digital Product Passport</h1>
            
            <div class="info-grid">
                <div class="info-card">
                    <span class="label">DPP ID:</span>
                    <span class="value">{dpp.get('id', 'N/A')}</span>
                </div>
                <div class="info-card">
                    <span class="label">Status:</span>
                    <span class="status-badge">{dpp.get('dpp:status', 'N/A')}</span>
                </div>
                <div class="info-card">
                    <span class="label">Schema Version:</span>
                    <span class="value">{dpp.get('dpp:dppSchemaVersion', 'N/A')}</span>
                </div>
                <div class="info-card">
                    <span class="label">Last Modified:</span>
                    <span class="value">{dpp.get('dcterms:modified', 'N/A')}</span>
                </div>
            </div>
    """
    
    # Economic Operator
    if 'dpp:economicOperator' in dpp:
        op = dpp['dpp:economicOperator']
        html += f"""
            <h2>📦 Economic Operator</h2>
            <div class="info-card">
                <div><span class="label">Name:</span> <span class="value">{op.get('schema:name', 'N/A')}</span></div>
                <div><span class="label">LEI:</span> <span class="value">{op.get('dpp:lei', 'N/A')}</span></div>
                <div><span class="label">GLN:</span> <span class="value">{op.get('dpp:gln', 'N/A')}</span></div>
            </div>
        """
    
    # Product Identifiers
    if 'dpp:productIdentifiers' in dpp:
        html += "<h2>🏷️ Product Identifiers</h2><div class='info-grid'>"
        for pid in dpp['dpp:productIdentifiers']:
            html += f"""
                <div class="info-card">
                    <span class="label">{pid.get('dpp:scheme', 'Unknown')}:</span>
                    <span class="value">{pid.get('dpp:value', 'N/A')}</span>
                </div>
            """
        html += "</div>"
    
    # Data Element Collections
    if 'dpp:dataElementCollections' in dpp:
        html += "<h2>📊 Data Collections</h2>"
        for collection in dpp['dpp:dataElementCollections']:
            title = collection.get('dcterms:title', 'Untitled Collection')
            html += f"<div class='collection'><h3>{title}</h3>"
            
            if 'dpp:elements' in collection:
                for element in collection['dpp:elements']:
                    if element.get('type') == 'dpp:Document':
                        # Render document
                        html += f"""
                            <div class="element">
                                📄 <a href="{element.get('schema:url', '#')}" class="document-link" target="_blank">
                                    {element.get('dpp:fileName', 'Document')}
                                </a>
                            </div>
                        """
                    elif 'dpp:value' in element and isinstance(element['dpp:value'], list):
                        # Render indicator table
                        path = element.get('dpp:path', '')
                        if 'indicators' in path:
                            html += "<table class='indicator-table'><thead><tr><th>Indicator</th><th>Module</th><th>Value</th><th>Unit</th></tr></thead><tbody>"
                            for ind in element['dpp:value']:
                                html += f"""
                                    <tr>
                                        <td>{ind.get('indicator', 'N/A')}</td>
                                        <td>{ind.get('module', 'N/A')}</td>
                                        <td>{ind.get('value', 'N/A')}</td>
                                        <td>{ind.get('unit', 'N/A')}</td>
                                    </tr>
                                """
                            html += "</tbody></table>"
                    elif 'dpp:valueElement' in element:
                        # Render single value
                        ve = element['dpp:valueElement']
                        name = element.get('dpp:name', 'Property')
                        value = ve.get('dpp:numericValue') or ve.get('dpp:textValue', 'N/A')
                        unit = ve.get('dpp:unit', '')
                        html += f"""
                            <div class="element">
                                <span class="label">{name}:</span>
                                <span class="value">{value} {unit}</span>
                            </div>
                        """
            html += "</div>"
    
    # QR Code section
    for collection in dpp.get('dpp:dataElementCollections', []):
        if collection.get('id') == '#carrier':
            for element in collection.get('dpp:elements', []):
                if element.get('id') == '#qrLink':
                    qr_uri = element.get('dpp:value', {}).get('uri', '')
                    if qr_uri:
                        html += f"""
                            <div class="qr-section">
                                <h3>📱 Data Carrier QR Code</h3>
                                <p>Scan to access this DPP:</p>
                                <code>{qr_uri}</code>
                            </div>
                        """
    
    html += """
        </div>
    </body>
    </html>
    """
    return html

# API Endpoints

@app.post("/dpps", status_code=201, response_model=Dict)
async def create_dpp(request: Request, response: Response):
    """CreateDPP - Create a new Digital Product Passport"""
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

@app.get("/dpps")
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

@app.get("/id/01/{gtin}")
@app.get("/id/01/{gtin}/21/{serial}")
@app.get("/id/01/{gtin}/10/{batch}")
async def gs1_digital_link_resolver(gtin: str, serial: Optional[str] = None, batch: Optional[str] = None):
    """Resolve GS1 Digital Link to a DPP (PoC).

    Returns the first matching DPP JSON-LD for the provided GTIN, optionally using serial to disambiguate.
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

    return JSONResponse(content=candidates[0], media_type="application/ld+json")

@app.get("/dpps/{dpp_id}")
async def read_dpp_by_id(dpp_id: str, request: Request):
    """ReadDPPById - Retrieve a DPP by its ID"""
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

@app.patch("/dpps/{dpp_id}")
async def update_dpp_by_id(dpp_id: str, request: Request):
    """UpdateDPPById - Update DPP using JSON Merge Patch (RFC 7396)"""
    dpp_id = unquote(dpp_id)
    
    if dpp_id not in dpp_storage:
        raise HTTPException(status_code=404, detail="DPP not found")
    
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

@app.delete("/dpps/{dpp_id}", status_code=204)
async def delete_dpp_by_id(dpp_id: str):
    """DeleteDPPById - Delete a DPP"""
    dpp_id = unquote(dpp_id)
    
    if dpp_id not in dpp_storage:
        raise HTTPException(status_code=404, detail="DPP not found")
    
    del dpp_storage[dpp_id]
    return Response(status_code=204)

@app.get("/dppsByProductId/{product_id}")
async def read_dpp_by_product_id(product_id: str):
    """ReadDPPByProductId - Retrieve DPP by product identifier"""
    # Search for DPP with matching product ID
    for dpp in dpp_storage.values():
        for pid in dpp.get("dpp:productIdentifiers", []):
            if pid.get("dpp:value") == product_id:
                return JSONResponse(content=dpp, media_type="application/ld+json")
    
    raise HTTPException(status_code=404, detail="DPP not found for product ID")

@app.get("/dppsByProductId/{product_id}/versions")
async def read_dpp_version_by_date(product_id: str, date: str):
    """ReadDPPVersionByProductIdAndDate - Get DPP version at specific date"""
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

@app.post("/registerDPP", status_code=201)
async def register_dpp(registry_request: RegistryRequest):
    """PostNewDPPToRegistry - Register DPP with EU registry"""
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

@app.get("/registry/{registry_suffix}")
async def get_registry_entry(registry_suffix: str):
    """Local registry lookup (PoC)."""
    key = None
    for rid in registry_storage.keys():
        if rid.endswith(registry_suffix):
            key = rid
            break
    if not key:
        raise HTTPException(status_code=404, detail="Registry entry not found")
    return registry_storage[key]

@app.get("/dpps/{dpp_id}/dataElements/{collection_id}")
async def read_data_element_collection(dpp_id: str, collection_id: str):
    """ReadDataElementCollection - Get specific data collection"""
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

@app.patch("/dpps/{dpp_id}/dataElements/{collection_id}")
async def update_data_element_collection(dpp_id: str, collection_id: str, request: Request):
    """UpdateDataElementCollection - Update specific collection"""
    dpp_id = unquote(dpp_id)
    
    if dpp_id not in dpp_storage:
        raise HTTPException(status_code=404, detail="DPP not found")
    
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

@app.get("/dpps/{dpp_id}/dataElements/{collection_id}/{element_id}")
async def read_data_element(dpp_id: str, collection_id: str, element_id: str):
    """ReadDataElement - Get specific data element"""
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "dpps_loaded": len(dpp_storage),
        "registry_entries": len(registry_storage)
    }

@app.post("/admin/reload")
async def reload_dpps():
    """Reload DPP files from disk (admin endpoint)"""
    dpp_storage.clear()
    load_sample_dpps()
    return {
        "message": "DPPs reloaded from disk",
        "dpps_loaded": len(dpp_storage)
    }

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
