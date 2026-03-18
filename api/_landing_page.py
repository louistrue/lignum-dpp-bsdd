"""
Redesigned landing page HTML generator for buildingSMART DPP.

Editorial, structured layout with clear visual hierarchy.
"""

import html as html_module


def build_landing_html(
    *,
    product_cards_html: str,
    meta_description: str,
    base_url: str,
    qr_code_widget: str,
) -> str:
    """Return the full landing page HTML string."""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta_description}">
    <meta name="theme-color" content="#2c2418">
    <meta property="og:title" content="buildingSMART DPP — Digital Product Passport Demo">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:type" content="website">
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <title>buildingSMART DPP — Digital Product Passport Demo</title>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --oak: #6b5534;
            --oak-light: #a68b5b;
            --oak-muted: #c4a97d;
            --cream: #f8f5f0;
            --parchment: #eee9e0;
            --ink: #1e1a14;
            --ink-soft: #4a4035;
            --muted: #8a7e70;
            --border: #ddd6ca;
            --card: #fff;
            --radius: 10px;
            --radius-lg: 14px;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Outfit', sans-serif;
            background: var(--cream);
            color: var(--ink);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }}
        a {{ color: var(--oak); text-decoration: none; font-weight: 500; }}
        a:hover {{ text-decoration: underline; }}
        code {{ font-family: 'JetBrains Mono', monospace; }}

        /* ── Banner ── */
        .banner {{
            background: var(--ink);
            color: #a09080;
            font-size: 11px;
            font-weight: 400;
            letter-spacing: 0.2px;
            padding: 8px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}
        .banner-label {{
            background: #b91c1c;
            color: #fff;
            padding: 2px 8px;
            border-radius: 3px;
            font-weight: 600;
            font-size: 10px;
            letter-spacing: 0.5px;
            flex-shrink: 0;
        }}
        .banner-text {{ flex: 1; }}
        .banner-links {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-shrink: 0;
        }}
        .banner-links a {{
            color: #807060;
            display: inline-flex;
            transition: color 0.15s;
            font-weight: 400;
        }}
        .banner-links a:hover {{ color: var(--oak-muted); text-decoration: none; }}

        /* ── Layout ── */
        .page {{ max-width: 1100px; margin: 0 auto; padding: 0 32px 48px; }}
        @media (max-width: 640px) {{ .page {{ padding: 0 16px 32px; }} }}

        /* ── Hero ── */
        .hero {{
            padding: 56px 0 48px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 48px;
        }}
        .hero-eyebrow {{
            font-size: 11px;
            font-weight: 600;
            color: var(--oak);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 14px;
        }}
        .hero h1 {{
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 38px;
            font-weight: 700;
            color: var(--ink);
            letter-spacing: -0.02em;
            line-height: 1.15;
            margin-bottom: 16px;
        }}
        @media (max-width: 640px) {{ .hero h1 {{ font-size: 28px; }} }}
        .hero-desc {{
            font-size: 16px;
            color: var(--muted);
            line-height: 1.7;
            max-width: 640px;
            font-weight: 300;
        }}
        .hero-desc strong {{ color: var(--ink-soft); font-weight: 500; }}
        .hero-standards {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 24px;
        }}
        .hero-standards span {{
            padding: 5px 14px;
            font-size: 11px;
            font-weight: 500;
            color: var(--oak);
            border: 1px solid var(--border);
            border-radius: 100px;
            background: var(--card);
            letter-spacing: 0.3px;
        }}

        /* ── Section headers ── */
        .section {{
            margin-bottom: 48px;
        }}
        .section-head {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 20px;
        }}
        .section-title {{
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 22px;
            font-weight: 600;
            color: var(--ink);
            letter-spacing: -0.01em;
        }}
        .section-count {{
            font-size: 12px;
            color: var(--muted);
            font-weight: 400;
        }}

        /* ── Product cards ── */
        .product-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}
        @media (max-width: 860px) {{ .product-grid {{ grid-template-columns: 1fr 1fr; }} }}
        @media (max-width: 540px) {{ .product-grid {{ grid-template-columns: 1fr; }} }}
        .product-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            display: flex;
            flex-direction: column;
            transition: box-shadow 0.25s, border-color 0.25s, transform 0.25s;
        }}
        .product-card:hover {{
            border-color: var(--oak-muted);
            box-shadow: 0 8px 24px rgba(107,85,52,0.08);
            transform: translateY(-2px);
        }}
        .product-header {{ padding: 20px 20px 8px; }}
        .product-header h3 {{
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 16px;
            color: var(--ink);
            font-weight: 600;
            margin-bottom: 3px;
            line-height: 1.3;
        }}
        .operator {{ font-size: 12px; color: var(--muted); font-weight: 400; }}
        .product-body {{ padding: 6px 20px 18px; flex: 1; }}
        .product-meta {{ font-size: 12px; color: var(--ink-soft); line-height: 1.9; }}
        .product-meta code {{
            background: var(--parchment);
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 10.5px;
            color: var(--ink-soft);
            word-break: break-all;
        }}
        .tags {{ margin-top: 12px; display: flex; gap: 5px; flex-wrap: wrap; }}
        .tag {{
            background: var(--parchment);
            color: var(--oak);
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}
        .product-actions {{
            padding: 14px 20px;
            display: flex;
            gap: 8px;
            border-top: 1px solid var(--parchment);
        }}

        /* ── Buttons ── */
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 18px;
            border-radius: 7px;
            text-decoration: none;
            font-weight: 600;
            font-size: 12px;
            transition: all 0.2s;
            cursor: pointer;
            border: none;
            font-family: inherit;
            letter-spacing: 0.2px;
        }}
        .btn-primary {{
            background: var(--ink);
            color: #fff;
        }}
        .btn-primary:hover {{ background: #332e26; text-decoration: none; }}
        .btn-outline {{
            background: var(--card);
            color: var(--ink-soft);
            border: 1px solid var(--border);
        }}
        .btn-outline:hover {{ border-color: var(--oak-muted); color: var(--ink); text-decoration: none; }}
        .btn-gs1 {{
            background: var(--card);
            color: var(--oak);
            border: 1px solid var(--border);
        }}
        .btn-gs1:hover {{ border-color: var(--oak-muted); background: var(--parchment); text-decoration: none; }}
        .btn-sm {{ padding: 6px 14px; font-size: 11px; }}
        .btn-arrow::after {{ content: '\u2192'; margin-left: 2px; }}

        /* ── Tools grid ── */
        .tools-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}
        @media (max-width: 900px) {{ .tools-grid {{ grid-template-columns: 1fr; }} }}
        .tool-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 28px 24px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            transition: box-shadow 0.25s, border-color 0.25s, transform 0.25s;
            position: relative;
        }}
        .tool-card:hover {{
            border-color: var(--oak-muted);
            box-shadow: 0 8px 24px rgba(107,85,52,0.08);
            transform: translateY(-2px);
        }}
        .tool-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: var(--parchment);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--oak);
            margin-bottom: 4px;
        }}
        .tool-card h3 {{
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 17px;
            font-weight: 600;
            color: var(--ink);
            margin: 0;
            line-height: 1.3;
        }}
        .tool-card p {{
            font-size: 13px;
            color: var(--muted);
            line-height: 1.55;
            margin: 0;
            flex: 1;
        }}
        .tool-tags {{ display: flex; gap: 5px; flex-wrap: wrap; }}
        .tool-tag {{
            background: var(--parchment);
            color: var(--oak);
            padding: 3px 9px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}

        /* ── Create form ── */
        .create-form {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 32px;
        }}
        .create-form h3 {{
            font-family: 'Source Serif 4', Georgia, serif;
            font-size: 20px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 2px;
        }}
        .create-form .form-hint {{ font-size: 13px; color: var(--muted); font-weight: 300; }}
        .form-section {{
            font-size: 11px;
            font-weight: 600;
            color: var(--oak);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 24px 0 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .form-section:first-of-type {{ margin-top: 24px; }}
        .form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }}
        @media (max-width: 640px) {{ .form-row {{ grid-template-columns: 1fr; }} }}
        .form-group {{ display: flex; flex-direction: column; gap: 5px; }}
        .form-label {{ font-size: 12px; font-weight: 500; color: var(--ink-soft); }}
        .form-input {{
            padding: 10px 14px;
            border: 1px solid var(--border);
            border-radius: 7px;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
            background: var(--card);
        }}
        .form-input:focus {{ border-color: var(--oak); box-shadow: 0 0 0 3px rgba(107,85,52,0.1); }}
        .form-actions {{ display: flex; gap: 10px; margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--parchment); }}

        /* ── Explore links ── */
        .explore-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }}
        @media (max-width: 640px) {{ .explore-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
        .explore-link {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding: 16px 18px;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            transition: border-color 0.2s, transform 0.2s;
        }}
        .explore-link:hover {{
            border-color: var(--oak-muted);
            text-decoration: none;
            transform: translateY(-1px);
        }}
        .explore-link strong {{ font-size: 13px; color: var(--ink); }}
        .explore-link span {{ font-size: 11px; color: var(--muted); font-weight: 300; }}

        /* ── Validation ── */
        .validate-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 24px;
        }}
        .validate-card p {{ font-size: 13px; color: var(--ink-soft); margin-bottom: 12px; line-height: 1.6; }}
        .validate-card textarea {{
            width: 100%;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            padding: 12px 14px;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            resize: vertical;
            background: var(--card);
            outline: none;
            transition: border-color 0.2s;
        }}
        .validate-card textarea:focus {{ border-color: var(--oak); }}

        /* ── Conneg card ── */
        .conneg-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 24px;
        }}
        .conneg-card p {{ font-size: 13px; color: var(--ink-soft); margin-bottom: 12px; }}
        .conneg-card code {{
            background: var(--ink);
            color: #b8d4a0;
            padding: 14px 18px;
            border-radius: 8px;
            display: block;
            font-size: 12px;
            overflow-x: auto;
            white-space: pre;
        }}
        .conneg-card .hint {{ font-size: 11px; color: var(--muted); margin-top: 10px; }}

        /* ── Footer ── */
        .footer {{
            text-align: center;
            padding: 28px 0;
            color: var(--muted);
            font-size: 12px;
            margin-top: 12px;
            border-top: 1px solid var(--border);
            font-weight: 300;
        }}
        .footer a {{ color: var(--oak-light); font-weight: 400; }}
        .footer a:hover {{ color: var(--oak); }}

        /* ── Animations ── */
        @keyframes fadeUp {{
            from {{ opacity: 0; transform: translateY(16px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .hero {{ animation: fadeUp 0.5s ease-out; }}
        .section {{ animation: fadeUp 0.5s ease-out both; }}
        .section:nth-child(2) {{ animation-delay: 0.06s; }}
        .section:nth-child(3) {{ animation-delay: 0.12s; }}
        .section:nth-child(4) {{ animation-delay: 0.18s; }}
        .section:nth-child(5) {{ animation-delay: 0.24s; }}
    </style>
</head>
<body>
    <div class="banner">
        <span class="banner-label">DEMO</span>
        <span class="banner-text">Proof of concept &middot; Sample data only &middot; buildingSMART Summit Porto</span>
        <div class="banner-links">
            <a href="https://www.lt.plus/" style="font-size:12px;font-weight:500;">lt.plus</a>
            <a href="https://github.com/louistrue/openDPP" title="GitHub"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg></a>
            <a href="https://www.linkedin.com/in/louistrue" title="LinkedIn"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></a>
        </div>
    </div>

    <div class="page">
        <div class="hero">
            <div class="hero-eyebrow">buildingSMART DPP</div>
            <h1>Digital Product Passport<br>for Construction</h1>
            <p class="hero-desc">
                A proof-of-concept <strong>prEN 18222:2025</strong> API for construction product passports
                &mdash; with GS1 Digital Link resolution, bSDD property references, and SHACL validation.
            </p>
            <div class="hero-standards">
                <span>prEN 18222</span>
                <span>prEN 18223</span>
                <span>GS1 Digital Link</span>
                <span>bSDD</span>
                <span>OWL + SHACL</span>
                <span>EU CPR / DoPC</span>
            </div>
        </div>

        <!-- ── Products ── -->
        <div class="section">
            <div class="section-head">
                <h2 class="section-title">Sample Products</h2>
            </div>
            <div id="product-grid" class="product-grid">
                {product_cards_html}
            </div>
        </div>

        <!-- ── Tools ── -->
        <div class="section">
            <div class="section-head">
                <h2 class="section-title">Tools</h2>
            </div>
            <div id="demo-cards" class="tools-grid">
                <div class="tool-card">
                    <div class="tool-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
                    </div>
                    <h3>Create DPP</h3>
                    <p>Build a product passport with properties, identifiers, labels, and bSDD classification.</p>
                    <div class="tool-tags">
                        <span class="tool-tag">prEN 18223</span>
                        <span class="tool-tag">JSON-LD</span>
                    </div>
                    <div><button class="btn btn-primary btn-arrow" onclick="openCreateForm();">Create</button></div>
                </div>
                <div class="tool-card">
                    <div class="tool-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    </div>
                    <h3>IFC Enrichment</h3>
                    <p>Upload an IFC file and enrich building elements with DPP data, bSDD classifications, and EPD indicators.</p>
                    <div class="tool-tags">
                        <span class="tool-tag">IFC 2x3 / 4</span>
                        <span class="tool-tag">bSDD</span>
                        <span class="tool-tag">EPD</span>
                    </div>
                    <div><a href="/enrich/" class="btn btn-primary btn-arrow">Enrich</a></div>
                </div>
                <div class="tool-card">
                    <div class="tool-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="12" width="4" height="9"/><rect x="10" y="5" width="4" height="16"/><rect x="17" y="1" width="4" height="20"/></svg>
                    </div>
                    <h3>Emissions Calculator</h3>
                    <p>Calculate whole-building environmental impacts from an IFC model using EPD data. Supports EN 15804 life cycle modules.</p>
                    <div class="tool-tags">
                        <span class="tool-tag">EN 15804</span>
                        <span class="tool-tag">LCA</span>
                        <span class="tool-tag">GWP</span>
                    </div>
                    <div><a href="/emissions/" class="btn btn-primary btn-arrow">Calculate</a></div>
                </div>
            </div>
        </div>

        <!-- ── Create form ── -->
        <div id="create-section" hidden style="margin-top:-32px;margin-bottom:48px;">
            <div class="create-form">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;">
                    <div>
                        <h3>New Product Passport</h3>
                        <div class="form-hint">Client-side preview &mdash; appears in the products grid above. Not persisted.</div>
                    </div>
                    <button onclick="closeCreateForm();" class="btn btn-outline" style="flex-shrink:0;">&times; Close</button>
                </div>

                <div class="form-section">General</div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Product name *</label>
                        <input id="cf-name" type="text" placeholder="e.g. CLT Panel 200mm" maxlength="100" class="form-input">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Manufacturer *</label>
                        <input id="cf-mfr" type="text" placeholder="e.g. Stora Enso" maxlength="100" class="form-input">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">GTIN</label>
                        <input id="cf-gtin" type="text" placeholder="e.g. 04012345678901" maxlength="14" class="form-input" style="font-family:'JetBrains Mono',monospace;font-size:13px;">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Product type (IFC)</label>
                        <select id="cf-type" class="form-input">
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
                </div>

                <div class="form-section">Labels &amp; Classification</div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Labels <span style="font-weight:300;color:var(--muted);">(comma-separated)</span></label>
                        <input id="cf-labels" type="text" placeholder="e.g. construction, timber, structural" maxlength="200" class="form-input">
                    </div>
                    <div class="form-group">
                        <label class="form-label">bSDD classification</label>
                        <input id="cf-bsdd" type="text" placeholder="e.g. Cross Laminated Timber" maxlength="100" class="form-input">
                    </div>
                </div>

                <div class="form-section">
                    Properties
                    <button type="button" onclick="addPropertyRow();" class="btn btn-outline btn-sm">+ Add row</button>
                </div>
                <div id="cf-props">
                    <div class="form-row prop-row" style="margin-bottom:8px;">
                        <div class="form-group"><input type="text" placeholder="Name, e.g. Thermal conductivity" class="form-input prop-name" maxlength="80"></div>
                        <div class="form-group" style="display:flex;gap:8px;">
                            <input type="text" placeholder="Value, e.g. 0.035" class="form-input prop-val" style="flex:1;" maxlength="40">
                            <input type="text" placeholder="Unit" class="form-input prop-unit" style="width:80px;" maxlength="20">
                        </div>
                    </div>
                </div>

                <div id="cf-error" style="display:none;margin-top:12px;font-size:12px;color:#b91c1c;background:#fef2f2;padding:10px 14px;border-radius:7px;"></div>
                <div class="form-actions">
                    <button onclick="createLocalDpp()" class="btn btn-primary" style="padding:10px 28px;font-size:13px;">Create DPP</button>
                    <button onclick="closeCreateForm();" class="btn btn-outline" style="padding:10px 22px;font-size:13px;">Cancel</button>
                </div>
            </div>
        </div>

        <script>
        function esc(s) {{ var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }}
        function removeRow(btn) {{ btn.closest('.prop-row').remove(); }}
        function addPropertyRow() {{
            var html = '<div class="form-row prop-row" style="margin-bottom:8px;">'
                + '<div class="form-group"><input type="text" placeholder="Property name" class="form-input prop-name" maxlength="80"></div>'
                + '<div class="form-group" style="display:flex;gap:8px;">'
                + '<input type="text" placeholder="Value" class="form-input prop-val" style="flex:1;" maxlength="40">'
                + '<input type="text" placeholder="Unit" class="form-input prop-unit" style="width:80px;" maxlength="20">'
                + '<button type="button" onclick="removeRow(this)" style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:18px;padding:0 6px;line-height:1;" title="Remove">&times;</button>'
                + '</div></div>';
            document.getElementById('cf-props').insertAdjacentHTML('beforeend', html);
        }}
        function openCreateForm() {{
            document.getElementById('demo-cards').style.display = 'none';
            document.getElementById('create-section').hidden = false;
            document.getElementById('cf-name').focus();
        }}
        function closeCreateForm() {{
            document.getElementById('create-section').hidden = true;
            document.getElementById('demo-cards').style.display = '';
        }}
        function createLocalDpp() {{
            var rawName = document.getElementById('cf-name').value.trim().substring(0, 100);
            var rawMfr = document.getElementById('cf-mfr').value.trim().substring(0, 100);
            var gtin = esc(document.getElementById('cf-gtin').value.trim().substring(0, 14));
            var ifcType = document.getElementById('cf-type').value;
            var rawLabels = document.getElementById('cf-labels').value.trim();
            var bsdd = esc(document.getElementById('cf-bsdd').value.trim().substring(0, 100));
            var errEl = document.getElementById('cf-error');
            errEl.style.display = 'none';
            if (!rawName || !rawMfr) {{ errEl.textContent = 'Product name and manufacturer are required.'; errEl.style.display = 'block'; return; }}
            var name = esc(rawName);
            var mfr = esc(rawMfr);

            var labels = rawLabels ? rawLabels.split(',').map(function(l) {{ return l.trim(); }}).filter(Boolean).slice(0, 8) : [ifcType];
            var tagHtml = labels.map(function(l) {{ return '<span class="tag">' + esc(l) + '</span>'; }}).join('');

            var propRows = document.querySelectorAll('#cf-props .prop-row');
            var propsHtml = '';
            propRows.forEach(function(row) {{
                var pn = row.querySelector('.prop-name').value.trim();
                var pv = row.querySelector('.prop-val').value.trim();
                var pu = row.querySelector('.prop-unit').value.trim();
                if (pn && pv) {{
                    propsHtml += '<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--parchment);font-size:12px;">'
                        + '<span style="color:var(--ink-soft);">' + esc(pn) + '</span>'
                        + '<span style="font-weight:600;color:var(--ink);">' + esc(pv) + (pu ? ' <span style="color:var(--muted);font-weight:400;">' + esc(pu) + '</span>' : '') + '</span></div>';
                }}
            }});

            var metaHtml = '';
            if (gtin) {{ metaHtml += '<div><strong>GTIN:</strong> <code>' + gtin + '</code></div>'; }}
            metaHtml += '<div><strong>DPP ID:</strong> <code style="font-size:10px;">did:web:local:dpp:' + rawName.toLowerCase().replace(/[^a-z0-9]+/g, '-') + '</code></div>';
            var classHtml = bsdd ? '<div style="margin-top:6px;font-size:11px;color:var(--ink-soft);"><strong>Classification:</strong> ' + esc(bsdd) + '</div>' : '';

            var card = '<div class="product-card" style="border-left:3px solid var(--oak);">'
                + '<div class="product-header"><h3>' + name + '</h3><span class="operator">' + mfr + '</span></div>'
                + '<div class="product-body">'
                + '<div class="product-meta">' + metaHtml + classHtml + '</div>'
                + (propsHtml ? '<div style="margin-top:10px;">' + propsHtml + '</div>' : '')
                + '<div class="tags">' + tagHtml + '</div>'
                + '</div></div>';

            document.getElementById('product-grid').insertAdjacentHTML('beforeend', card);
            document.getElementById('cf-name').value = '';
            document.getElementById('cf-mfr').value = '';
            document.getElementById('cf-gtin').value = '';
            document.getElementById('cf-labels').value = '';
            document.getElementById('cf-bsdd').value = '';
            document.getElementById('cf-props').innerHTML = '<div class="form-row prop-row" style="margin-bottom:8px;">'
                + '<div class="form-group"><input type="text" placeholder="Name, e.g. Thermal conductivity" class="form-input prop-name" maxlength="80"></div>'
                + '<div class="form-group" style="display:flex;gap:8px;">'
                + '<input type="text" placeholder="Value, e.g. 0.035" class="form-input prop-val" style="flex:1;" maxlength="40">'
                + '<input type="text" placeholder="Unit" class="form-input prop-unit" style="width:80px;" maxlength="20">'
                + '</div></div>';
            closeCreateForm();
        }}
        </script>

        <!-- ── Explore ── -->
        <div class="section">
            <div class="section-head">
                <h2 class="section-title">Explore</h2>
            </div>
            <div class="explore-grid">
                <a class="explore-link" href="/validate" onclick="event.preventDefault(); document.getElementById('validate-section').scrollIntoView({{behavior:'smooth'}})"><strong>Validate DPP</strong><span>SHACL conformance check</span></a>
                <a class="explore-link" href="/ontology"><strong>OWL Ontology</strong><span>Classes &amp; properties</span></a>
                <a class="explore-link" href="/ontology/shacl"><strong>SHACL Shapes</strong><span>Constraint definitions</span></a>
                <a class="explore-link" href="/docs"><strong>API Docs</strong><span>Swagger UI</span></a>
            </div>

            <div id="validate-section" class="validate-card" style="margin-top: 16px;">
                <p><strong>SHACL Validation</strong> &mdash; load a sample DPP or paste your own JSON-LD to check conformance.</p>
                <div style="display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap;">
                    <button onclick="loadDpp('timber')" class="btn btn-outline btn-sm validate-sample-btn" data-key="timber">Timber (Glulam)</button>
                    <button onclick="loadDpp('insulation')" class="btn btn-outline btn-sm validate-sample-btn" data-key="insulation">Insulation (Knauf)</button>
                    <button onclick="loadDpp('pipe')" class="btn btn-outline btn-sm validate-sample-btn" data-key="pipe">Pipe (PVC DN110)</button>
                </div>
                <textarea id="validate-input" rows="5" placeholder="Select a sample above or paste your own DPP JSON-LD here&hellip;"></textarea>
                <div style="display: flex; gap: 8px; margin-top: 10px; align-items: center;">
                    <button onclick="runValidation()" class="btn btn-primary btn-sm">Validate</button>
                    <button onclick="clearValidation()" class="btn btn-outline btn-sm">Clear</button>
                    <span id="validate-loaded" style="font-size: 11px; color: var(--muted); margin-left: auto;"></span>
                </div>
                <pre id="validate-result" style="display:none; margin-top: 12px; padding: 12px 14px; background: var(--ink); color: #d0d0d0; border-radius: var(--radius); font-size: 11px; max-height: 240px; overflow-y: auto; white-space: pre-wrap;"></pre>
            </div>
        </div>
        <script>
        const DPP_IDS = {{
            timber: 'did:web:bsdd-dpp.dev:dpp:schilliger-bsh-gl24h-2022-001',
            insulation: 'did:web:bsdd-dpp.dev:dpp:knauf-acoustic-batt-2025-001',
            pipe: 'did:web:bsdd-dpp.dev:dpp:pvc-sewage-dn110-2025-001'
        }};
        async function loadDpp(key) {{
            const ta = document.getElementById('validate-input');
            const label = document.getElementById('validate-loaded');
            const out = document.getElementById('validate-result');
            out.style.display = 'none';
            document.querySelectorAll('.validate-sample-btn').forEach(b => b.style.borderColor = '');
            const btn = document.querySelector('[data-key="'+key+'"]');
            if (btn) btn.style.borderColor = 'var(--oak)';
            ta.value = 'Loading\u2026';
            try {{
                const id = DPP_IDS[key];
                const res = await fetch('/dpps/' + encodeURIComponent(id), {{headers: {{'Accept': 'application/ld+json'}}}});
                const dpp = await res.json();
                ta.value = JSON.stringify(dpp, null, 2);
                label.textContent = 'Loaded: ' + (dpp['dcterms:title'] || dpp.id || key);
            }} catch(e) {{ ta.value = 'Error loading: ' + e.message; label.textContent = ''; }}
        }}
        function clearValidation() {{
            document.getElementById('validate-input').value = '';
            document.getElementById('validate-result').style.display = 'none';
            document.getElementById('validate-loaded').textContent = '';
            document.querySelectorAll('.validate-sample-btn').forEach(b => b.style.borderColor = '');
        }}
        async function runValidation() {{
            const ta = document.getElementById('validate-input');
            const out = document.getElementById('validate-result');
            out.style.display = 'block';
            if (!ta.value.trim()) {{ out.textContent = 'Select a sample or paste DPP JSON-LD first.'; out.style.color = '#888'; return; }}
            try {{
                const body = JSON.parse(ta.value);
                const res = await fetch('/validate', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(body)}});
                const result = await res.json();
                const conforms = result.conforms;
                const count = (result.results || []).length;
                let summary = conforms ? '\u2705 Conforms! No violations found.' : '\u274c ' + count + ' violation(s) found:';
                if (!conforms) {{
                    for (const r of result.results || []) {{
                        summary += '\\n\\n\u2022 ' + (r.message || r.detail || JSON.stringify(r));
                    }}
                }}
                out.textContent = summary;
                out.style.color = conforms ? '#4ade80' : '#f87171';
            }} catch(e) {{ out.textContent = 'Error: ' + e.message; out.style.color = '#f87171'; }}
        }}
        </script>

        <!-- ── Content Negotiation ── -->
        <div class="section">
            <div class="section-head">
                <h2 class="section-title">Content Negotiation</h2>
            </div>
            <div class="conneg-card">
                <p>The same URL returns <strong>HTML</strong> in a browser or <strong>JSON-LD</strong> via curl:</p>
                <code>curl -H "Accept: application/ld+json" {base_url}/id/01/04012345678901</code>
                <div class="hint">Open in browser for HTML view with bSDD links and QR codes.</div>
            </div>
        </div>

        <div class="footer">
            <a href="/docs">API Docs</a> &middot;
            <a href="/ontology">Ontology</a> &middot;
            <a href="/ontology/shacl">SHACL</a>
            &middot; buildingSMART Summit Porto
        </div>
    </div>
    {qr_code_widget}
</body>
</html>"""
