#!/usr/bin/env python3
"""
Generate QR codes for DPP data carriers
Conforming to prEN 18220:2025 - Data Carrier specification
"""

import json
import qrcode
from pathlib import Path
from typing import Dict, Optional, List

def generate_qr_code(uri: str, filename: str, box_size: int = 10, border: int = 4) -> None:
    """
    Generate a QR code for a given URI
    
    Args:
        uri: The URI to encode (GS1 Digital Link or DID resolver URL)
        filename: Output filename for the QR code image
        box_size: Size of each box in pixels
        border: Border size in boxes
    """
    qr = qrcode.QRCode(
        version=None,  # Auto-determine version
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"✅ Generated QR code: {filename}")
    print(f"   URI: {uri}")

def extract_carrier_uri(dpp_file: Path) -> Optional[Dict[str, str]]:
    """
    Extract carrier URI from a DPP JSON-LD file
    
    Args:
        dpp_file: Path to the DPP JSON-LD file
    
    Returns:
        Dictionary with 'uri' and 'resolverUri' or None if not found
    """
    try:
        with open(dpp_file, 'r') as f:
            dpp = json.load(f)
        
        # Find carrier collection
        for collection in dpp.get('dpp:dataElementCollections', []):
            if collection.get('id') == '#carrier':
                for element in collection.get('dpp:elements', []):
                    if element.get('id') == '#qrLink':
                        return element.get('dpp:value', {})
        
        return None
    except Exception as e:
        print(f"❌ Error reading {dpp_file}: {e}")
        return None

def main():
    """Generate exactly three QR codes (one per product) and an HTML viewer with links."""

    output_dir = Path("qr_codes")
    output_dir.mkdir(exist_ok=True)

    # Clean old QR codes to avoid confusion
    for png in output_dir.glob("*.png"):
        try:
            png.unlink()
        except Exception:
            pass

    # DPP files to process: (file, slug, label)
    dpp_files = [
        ("dpp_knauf_acoustic_batt.jsonld", "knauf_acoustic_batt", "Knauf Acoustic Batt"),
        ("dpp_schilliger_glulam.jsonld", "schilliger_glulam", "Schilliger Glulam"),
        ("dpp_pvc_sewage_pipe.jsonld", "pvc_sewage_pipe", "PVC Sewage Pipe"),
    ]

    print("🔄 Generating QR codes for Digital Product Passports...")
    print("=" * 60)

    cards: List[Dict[str, str]] = []

    for dpp_filename, slug, label in dpp_files:
        dpp_path = Path(dpp_filename)

        if not dpp_path.exists():
            print(f"⚠️  Skipping {dpp_filename} - file not found")
            continue

        carrier_data = extract_carrier_uri(dpp_path) or {}
        gs1_uri = carrier_data.get('uri')
        dpp_uri = carrier_data.get('resolverUri')

        # Prefer GS1 Digital Link for the QR payload; fallback to DPP URI
        qr_payload = gs1_uri or dpp_uri
        if not qr_payload:
            print(f"⚠️  No carrier data found in {dpp_filename}")
            continue

        output_file = output_dir / f"{slug}.png"
        generate_qr_code(qr_payload, output_file)

        cards.append({
            "title": label,
            "image": output_file.name,
            "dpp_uri": dpp_uri or "",
            "gs1_uri": gs1_uri or qr_payload,
        })

        print("-" * 60)

    print("\n✅ QR code generation complete!")
    print(f"📁 Output directory: {output_dir.absolute()}")

    # Generate HTML viewer with clickable links
    generate_html_viewer(output_dir, cards)

def generate_html_viewer(output_dir: Path, cards: List[Dict[str, str]]):
    """Generate an HTML file to view QR codes and provide clickable links."""
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DPP QR Codes - prEN 18220 Data Carriers</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        .qr-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }
        .qr-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #dee2e6;
        }
        .qr-card img {
            max-width: 200px;
            margin: 20px auto;
            border: 1px solid #dee2e6;
            padding: 10px;
            background: white;
        }
        .qr-title {
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
        }
        .qr-type {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            background: #3498db;
            color: white;
            font-size: 12px;
            margin-bottom: 10px;
        }
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Digital Product Passport QR Codes</h1>
        <div class="info-box">
            <strong>ℹ️ Conformance:</strong> These QR codes conform to <code>prEN 18220:2025</code> - Data Carrier specification.
            They encode either GS1 Digital Links or DID resolver URLs that point to the DPP endpoints.
        </div>
        
        <h2>📦 Product DPP QR Codes</h2>
        <div class="qr-grid">
"""

    for card in cards:
        title = card["title"]
        img = card["image"]
        dpp_uri = card["dpp_uri"]
        gs1_uri = card["gs1_uri"]

        html += f"""
            <div class=\"qr-card\">
                <div class=\"qr-title\">{title}</div>
                <img src=\"{img}\" alt=\"{title} QR Code\">
                <div style=\"margin-top:10px;\">
                    <a href=\"{dpp_uri or gs1_uri}\" target=\"_blank\">Open DPP</a>
                    &nbsp;|&nbsp;
                    <a href=\"{gs1_uri}\" target=\"_blank\">GS1 Link</a>
                </div>
            </div>
"""
    
    html += """
        </div>
        
        <h2>📋 Implementation Notes</h2>
        <div class="info-box">
            <p><strong>Data Carrier Requirements (prEN 18220):</strong></p>
            <ul>
                <li>✅ Encodes unique product identifier</li>
                <li>✅ Supports model/batch/item granularity</li>
                <li>✅ Vendor-neutral and interoperable</li>
                <li>✅ Readable by consumer devices without custom apps</li>
                <li>✅ Resolves to DPP JSON-LD endpoint or HTML view</li>
            </ul>
        </div>
        
        <h2>🔗 URI Schemes</h2>
        <div class="info-box">
            <p><strong>GS1 Digital Link:</strong></p>
            <code>http://localhost:8000/id/01/04012345678901/21/KI-AB-2025-001?linkType=dpp</code>
            
            <p style="margin-top: 15px;"><strong>DID Resolver:</strong></p>
            <code>http://localhost:8000/dpps/did:web:lignum.dev:dpp:knauf-acoustic-batt-2025-001</code>
        </div>
    </div>
</body>
</html>
"""
    
    viewer_path = output_dir / "index.html"
    with open(viewer_path, 'w') as f:
        f.write(html)
    
    print(f"📄 Generated HTML viewer: {viewer_path.absolute()}")

if __name__ == "__main__":
    main()
