#!/usr/bin/env python3
"""
Generate QR codes for DPP data carriers
Conforming to prEN 18220:2025 - Data Carrier specification

Uses DPP_API_URL env var (defaults to deployed Vercel API).
Set DPP_API_URL=http://localhost:8000 for local dev.
"""

import json
import os
import qrcode
from pathlib import Path
from typing import Dict, Optional, List

# Base URL — deployed API by default
BASE_URL = os.environ.get("DPP_API_URL", "https://bsdd-dpp.dev").rstrip("/")


def generate_qr_code(uri: str, filename: str, box_size: int = 10, border: int = 4) -> None:
    """Generate a QR code PNG for a given URI."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"  Generated: {filename}")
    print(f"  URI: {uri}")


def extract_carrier_uri(dpp_file: Path) -> Optional[Dict[str, str]]:
    """Extract carrier URI from a DPP JSON-LD file, replacing localhost with BASE_URL."""
    try:
        raw = dpp_file.read_text()
        # Replace localhost URLs with the configured base URL
        raw = raw.replace("http://localhost:8000", BASE_URL)
        dpp = json.loads(raw)

        for collection in dpp.get('dpp:dataElementCollections', []):
            if collection.get('id') == '#carrier':
                for element in collection.get('dpp:elements', []):
                    if element.get('id') == '#qrLink':
                        return element.get('dpp:value', {})
        return None
    except Exception as e:
        print(f"  Error reading {dpp_file}: {e}")
        return None


def main():
    """Generate QR codes (one per product) and an HTML viewer."""

    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "qr_codes"
    output_dir.mkdir(exist_ok=True)

    # Clean old QR codes
    for png in output_dir.glob("*.png"):
        try:
            png.unlink()
        except Exception:
            pass

    dpp_files = [
        ("dpp_knauf_acoustic_batt.jsonld", "knauf_acoustic_batt", "Knauf Acoustic Batt"),
        ("dpp_schilliger_glulam.jsonld", "schilliger_glulam", "Schilliger Glulam GL24h"),
        ("dpp_pvc_sewage_pipe.jsonld", "pvc_sewage_pipe", "PVC Sewage Pipe DN110"),
    ]

    print(f"Generating QR codes (target: {BASE_URL})")
    print("=" * 60)

    cards: List[Dict[str, str]] = []

    for dpp_filename, slug, label in dpp_files:
        dpp_path = project_root / "dpp" / "products" / dpp_filename
        if not dpp_path.exists():
            print(f"  Skipping {dpp_filename} - not found")
            continue

        carrier_data = extract_carrier_uri(dpp_path) or {}
        gs1_uri = carrier_data.get('uri')
        dpp_uri = carrier_data.get('resolverUri')

        qr_payload = gs1_uri or dpp_uri
        if not qr_payload:
            print(f"  No carrier data in {dpp_filename}")
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

    print(f"\nQR codes saved to: {output_dir.absolute()}")
    generate_html_viewer(output_dir, cards)


def generate_html_viewer(output_dir: Path, cards: List[Dict[str, str]]):
    """Generate an HTML file to view QR codes and provide clickable links."""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DPP QR Codes - prEN 18220 Data Carriers</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #fff; color: #1a1a1a; padding: 32px 24px; }}
        .container {{ max-width: 960px; margin: 0 auto; }}
        h1 {{ font-size: 1.5em; font-weight: 700; color: #111; margin-bottom: 8px; }}
        h2 {{ font-size: 0.8em; font-weight: 700; color: #444; text-transform: uppercase; letter-spacing: 1px; margin: 32px 0 16px; padding-bottom: 8px; border-bottom: 2px solid #111; }}
        .info-box {{ background: #f8fafc; border: 1px solid #e5e5e5; border-radius: 3px; padding: 12px 16px; margin: 16px 0; font-size: 13px; color: #555; line-height: 1.6; }}
        .info-box strong {{ color: #111; }}
        code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: 'SF Mono', Monaco, monospace; font-size: 12px; }}
        .qr-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin: 16px 0; }}
        .qr-card {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 3px; padding: 20px; text-align: center; }}
        .qr-card img {{ max-width: 180px; margin: 16px auto; display: block; }}
        .qr-title {{ font-weight: 600; color: #111; font-size: 14px; margin-bottom: 4px; }}
        .qr-links {{ margin-top: 12px; font-size: 13px; }}
        .qr-links a {{ color: #2563eb; text-decoration: none; }}
        .qr-links a:hover {{ text-decoration: underline; }}
        .note {{ font-size: 12px; color: #999; margin-top: 24px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Digital Product Passport QR Codes</h1>
        <div class="info-box">
            <strong>prEN 18220:2025</strong> Data Carrier specification. QR codes encode GS1 Digital Links
            that resolve to the DPP API at <code>{BASE_URL}</code>.
        </div>

        <h2>Product QR Codes</h2>
        <div class="qr-grid">
"""

    for card in cards:
        title = card["title"]
        img = card["image"]
        dpp_uri = card["dpp_uri"]
        gs1_uri = card["gs1_uri"]

        html += f"""
            <div class="qr-card">
                <div class="qr-title">{title}</div>
                <img src="{img}" alt="{title} QR Code">
                <div class="qr-links">
                    <a href="{dpp_uri or gs1_uri}" target="_blank">Open DPP</a>
                    &nbsp;&middot;&nbsp;
                    <a href="{gs1_uri}" target="_blank">GS1 Link</a>
                </div>
            </div>
"""

    html += f"""
        </div>

        <h2>URI Schemes</h2>
        <div class="info-box">
            <p><strong>GS1 Digital Link:</strong></p>
            <code>{BASE_URL}/id/01/04012345678901/21/KI-AB-2025-001?linkType=dpp</code>

            <p style="margin-top: 12px;"><strong>DID Resolver:</strong></p>
            <code>{BASE_URL}/dpps/did:web:bsdd-dpp.dev:dpp:knauf-acoustic-batt-2025-001</code>
        </div>

        <div class="note">
            buildingSMART DPP Demo &mdash; bS-Summit Porto &mdash; buildingSMART International
        </div>
    </div>
</body>
</html>
"""

    viewer_path = output_dir / "index.html"
    with open(viewer_path, 'w') as f:
        f.write(html)
    print(f"HTML viewer: {viewer_path.absolute()}")


if __name__ == "__main__":
    main()
