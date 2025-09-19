#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IFC patch script for the BuildingSmart Summit POC
- Aligns with the modular DPP ontology approach (Identifier, Quantities and Units, Provenance patterns)
- Adds only CPset_* property sets (no Pset_*)
- Creates bSDD-style classification references using your demo2025 dictionaries
- Attaches manufacturer PDFs as IfcDocumentReference
- Values are taken from a mapping CSV (component-scoped) and, if present, DPP JSON-LD files

Author: LT+ (POC script)
Requirements: ifcopenshell (IFC4 or IFC4x3 model)

Example:
  python patch_poc_ifc.py \
    --ifc POC_Wall.ifc \
    --mapping /path/to/mapping.csv \
    --dpp-dir /path/to/DPP \
    --out POC_Wall_patched.ifc

CSV format (header expected):
  component,cp_property,value,unit,bsdd_property_uri,dictionary_uri,evidence_file,standard,note

Components supported in this POC:
  - insulation  -> first IfcWallStandardCase (fallback to any IfcWall)
  - pipe        -> first IfcPipeSegment
  - timber      -> IfcMember/IfcBeam or a material named like "Glulam" or "Schilliger" (fallback: wall)

CPsets created:
  - CPset_Insulation_Performance
  - CPset_Pipe_DimensionsAndRatings
  - CPset_Timber_Performance
"""
import argparse
import csv
import json
import os
import sys
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, unquote

try:
    import ifcopenshell
except Exception:
    print("This script requires ifcopenshell. Install with: pip install ifcopenshell")
    raise

try:
    from ifcopenshell import guid as ifc_guid
except Exception:
    ifc_guid = None

# ----------------------- helpers -----------------------

def msg(s: str):
    print(f"[patch] {s}")

def first(items):
    return items[0] if items else None

def get_owner_history(ifc):
    oh = first(ifc.by_type("IfcOwnerHistory"))
    if oh:
        return oh
    person = ifc.create_entity("IfcPerson", Identification="POC", FamilyName="LTplus")
    org = ifc.create_entity("IfcOrganization", Identification="LT+", Name="LTplus AG")
    person_and_org = ifc.create_entity("IfcPersonAndOrganization", ThePerson=person, TheOrganization=org)
    app = ifc.create_entity("IfcApplication", ApplicationDeveloper=org, Version="0.1", ApplicationFullName="LT+ POC Patcher", ApplicationIdentifier="LT+POC")
    return ifc.create_entity("IfcOwnerHistory", OwningUser=person_and_org, OwningApplication=app)

def ensure_rel_defines_by_properties(ifc, element, pset):
    rels = [r for r in ifc.by_type("IfcRelDefinesByProperties") if r.RelatingPropertyDefinition == pset and element in (r.RelatedObjects or [])]
    if not rels:
        gid = ifc_guid.new() if ifc_guid else None
        ifc.create_entity("IfcRelDefinesByProperties", GlobalId=gid, RelatedObjects=[element], RelatingPropertyDefinition=pset)

def find_or_create_pset(ifc, element, pset_name: str):
    for rel in element.IsDefinedBy or []:
        try:
            if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition and rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
                ps = rel.RelatingPropertyDefinition
                if ps.Name == pset_name:
                    return ps
        except Exception:
            pass
    owner = get_owner_history(ifc)
    pset = ifc.create_entity("IfcPropertySet", GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner, Name=pset_name, HasProperties=[])
    ensure_rel_defines_by_properties(ifc, element, pset)
    msg(f"Created {pset_name} on #{element.id()} {element.is_a()}")
    return pset

def ifc_measure(ifc, unit: Optional[str], value_text: str):
    v = value_text.strip()
    try:
        num = float(v)
        is_num = True
    except Exception:
        num = None
        is_num = False
    u = (unit or "").strip().lower()
    # Normalize common unicode superscripts
    u = u.replace("³", "3").replace("·", "/")
    if u in ["w/mk", "w/m/k", "w/m·k", "w m-1 k-1"] and is_num:
        return ifc.create_entity("IfcThermalConductivityMeasure", num)
    if u in ["kg/m3", "kg/m^3", "kg m-3"] and is_num:
        return ifc.create_entity("IfcMassDensityMeasure", num)
    # Common EPD indicator units → numeric real
    epd_units = {
        "kgco2e", "kg co2e", "kgco2eq", "kg co2eq",
        "kgso2e", "kg so2e", "kgcfc-11e", "kg cfc-11e",
        "kgpo4e", "kg po4e", "mje", "mjd", "mj", "kj",
    }
    if u.replace(" ", "") in epd_units and is_num:
        return ifc.create_entity("IfcReal", num)
    if u in ["mm", "m"] and is_num:
        return ifc.create_entity("IfcPositiveLengthMeasure", num)
    if u in ["-", ""] and is_num:
        return ifc.create_entity("IfcReal", num)
    return ifc.create_entity("IfcLabel", v)

def upsert_single_value(ifc, pset, name: str, value_entity, description: Optional[str] = None):
    props = {p.Name: p for p in (pset.HasProperties or []) if p.is_a("IfcPropertySingleValue")}
    if name in props:
        prop = props[name]
        prop.NominalValue = value_entity
        if description is not None:
            prop.Description = description
    else:
        prop = ifc.create_entity("IfcPropertySingleValue", Name=name, Description=description, NominalValue=value_entity, Unit=None)
        pset.HasProperties = list(pset.HasProperties or []) + [prop]
    # Link bSDD property URI as an external reference when provided in description
    try:
        if description and isinstance(description, str) and description.startswith("http"):
            ext_ref = get_or_create_external_ref(
                ifc,
                location=description,
                identification=None,
                name=f"bSDD property: {name}",
            )
            # Create ExternalReferenceRelationship to the property
            linked = False
            for rel in ifc.by_type("IfcExternalReferenceRelationship"):
                if rel.RelatingReference == ext_ref and prop in (rel.RelatedResourceObjects or []):
                    linked = True
                    break
            if not linked:
                ifcopenshell.api = getattr(ifcopenshell, 'api', None)  # safe guard if API is not available
                ifc.create_entity(
                    "IfcExternalReferenceRelationship",
                    RelatingReference=ext_ref,
                    RelatedResourceObjects=[prop],
                )
    except Exception:
        pass
    return prop

def get_or_create_doc_ref(ifc, name: str, uri: str):
    for d in ifc.by_type("IfcDocumentReference"):
        if (d.Location or "").strip() == uri.strip() and (d.Name or "") == name:
            return d
    return ifc.create_entity("IfcDocumentReference", Location=uri, Name=name, Description=None, Identification=None, ReferencedDocument=None)

def attach_doc_to(ifc, element, doc_ref):
    # Skip if already associated by same reference or by any reference with same URL
    for rel in ifc.by_type("IfcRelAssociatesDocument"):
        if element not in (rel.RelatedObjects or []):
            continue
        if rel.RelatingDocument == doc_ref:
            return
        try:
            if (getattr(rel.RelatingDocument, "Location", None) or "").strip() == (doc_ref.Location or "").strip():
                return
        except Exception:
            pass
    ifc.create_entity("IfcRelAssociatesDocument", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[element], RelatingDocument=doc_ref)

def _derive_identification(identification: Optional[str], url: str, fallback_name: str) -> str:
    if identification and identification.strip():
        return identification.strip()
    try:
        p = urlparse(url)
        last = unquote(p.path.split("/")[-1]) if p.path else ""
        ident = last or p.netloc or fallback_name or "DOC"
        return ident
    except Exception:
        return fallback_name or "DOC"

def _is_generic_label(value: Optional[str]) -> bool:
    v = (value or "").strip().lower()
    return v in {"*", "datasource", "external", "1.0.0", "1.0"}

def get_or_create_doc_info(ifc, name: str, identification: Optional[str], url: str, description: Optional[str] = None):
    # Reuse by URL if present; update generic names later
    for di in ifc.by_type("IfcDocumentInformation"):
        if (di.Location or "").strip() == (url or "").strip():
            # Upgrade metadata if generic
            if name and (not di.Name or _is_generic_label(di.Name)):
                di.Name = name
            if description and not di.Description:
                di.Description = description
            if identification and (not di.Identification or _is_generic_label(di.Identification)):
                di.Identification = identification
            return di
    ident_value = _derive_identification(identification, url, name)
    # Only pass attributes we intend to set to avoid non-optional None errors
    return ifc.create_entity("IfcDocumentInformation", Identification=ident_value, Name=name, Description=description, Location=url)

def get_or_create_doc_ref_for_info(ifc, info, name: Optional[str] = None, identification: Optional[str] = None, description: Optional[str] = None):
    # Reuse by ReferencedDocument or by URL
    for d in ifc.by_type("IfcDocumentReference"):
        same_url = (getattr(d, "Location", None) or "").strip() == (info.Location or "").strip()
        if d.ReferencedDocument == info or same_url:
            if name and (not d.Name or _is_generic_label(d.Name)):
                d.Name = name
            if identification and (not d.Identification or _is_generic_label(d.Identification)):
                d.Identification = identification
            if description and not d.Description:
                d.Description = description
            if d.ReferencedDocument is None:
                d.ReferencedDocument = info
            return d
    ident_value = _derive_identification(identification, info.Location or "", name or info.Name or "")
    return ifc.create_entity("IfcDocumentReference", Location=info.Location, Identification=ident_value, Name=name or info.Name, Description=description, ReferencedDocument=info)

def infer_doc_metadata(url: str) -> Dict[str, Optional[str]]:
    u = (url or "").strip()
    name = "External Document"
    identification = None
    description = None
    if "/dpps/" in u:
        name = "Digital Product Passport (resolver)"
        identification = u.split("/dpps/")[-1]
        description = "Resolver URL for DPP JSON-LD/HTML"
    elif "/id/01/" in u:
        name = "GS1 Digital Link (QR target)"
        identification = u.split("/id/")[-1]
        description = "GS1 Digital Link to DPP"
    elif "NEPD" in u or "epd" in u.lower():
        name = "Environmental Product Declaration (EPD)"
        identification = next((part for part in u.replace("_","-").split("/") if part.startswith("NEPD")), None)
    elif "Leistungserklaerung" in u or "DoP" in u:
        name = "Declaration of Performance (DoP)"
    elif "Datasheet" in u or "Data.pdf" in u:
        name = "Product Datasheet"
    return {"name": name, "identification": identification, "description": description}

def get_or_create_external_ref(ifc, location: str, identification: str = None, name: str = None):
    for er in ifc.by_type("IfcExternalReference"):
        if (er.Location or "").strip() == location.strip() and (er.Identification or None) == identification and (er.Name or None) == name:
            return er
    return ifc.create_entity("IfcExternalReference", Location=location, Identification=identification, Name=name)

def associate_external_to_element(ifc, element, ext_ref):
    # Prefer IfcRelAssociatesExternal (IFC4+), fallback to IfcRelAssociatesDocument
    try:
        for rel in ifc.by_type("IfcRelAssociatesExternal"):
            if rel.RelatingReference == ext_ref and element in (rel.RelatedObjects or []):
                return
        ifc.create_entity(
            "IfcRelAssociatesExternal",
            GlobalId=ifc_guid.new() if ifc_guid else None,
            RelatedObjects=[element],
            RelatingReference=ext_ref,
        )
    except Exception:
        doc_ref = get_or_create_doc_ref(ifc, name=(ext_ref.Name or "external"), uri=(ext_ref.Location or ""))
        attach_doc_to(ifc, element, doc_ref)

def link_external_to_material(ifc, material, ext_ref):
    for rel in ifc.by_type("IfcExternalReferenceRelationship"):
        if rel.RelatingReference == ext_ref and material in (rel.RelatedResourceObjects or []):
            return
    ifc.create_entity("IfcExternalReferenceRelationship", RelatingReference=ext_ref, RelatedResourceObjects=[material])

def element_or_material_for_timber(ifc):
    cand = first(ifc.by_type("IfcMember")) or first(ifc.by_type("IfcBeam"))
    if cand:
        return ("element", cand)
    for m in ifc.by_type("IfcMaterial"):
        n = (m.Name or "").lower()
        if "glulam" in n or "brettschichtholz" in n or "schilliger" in n:
            return ("material", m)
    w = first(ifc.by_type("IfcWallStandardCase")) or first(ifc.by_type("IfcWall"))
    return ("element", w) if w else (None, None)

def _collect_base_materials_from_def(mat_def) -> List:
    mats: List = []
    try:
        if not mat_def:
            return mats
        if mat_def.is_a("IfcMaterial"):
            return [mat_def]
        # Profile usage → profile set → profiles → material
        if mat_def.is_a("IfcMaterialProfileSetUsage"):
            mps = getattr(mat_def, "ForProfileSet", None)
            if mps:
                for mp in (getattr(mps, "MaterialProfiles", None) or []):
                    m = getattr(mp, "Material", None)
                    if m:
                        mats.append(m)
        # Layer usage → layer set → layers → material
        if mat_def.is_a("IfcMaterialLayerSetUsage"):
            mls = getattr(mat_def, "ForLayerSet", None)
            if mls:
                for ml in (getattr(mls, "MaterialLayers", None) or []):
                    m = getattr(ml, "Material", None)
                    if m:
                        mats.append(m)
        # Direct sets
        if mat_def.is_a("IfcMaterialProfileSet"):
            for mp in (getattr(mat_def, "MaterialProfiles", None) or []):
                m = getattr(mp, "Material", None)
                if m:
                    mats.append(m)
        if mat_def.is_a("IfcMaterialLayerSet"):
            for ml in (getattr(mat_def, "MaterialLayers", None) or []):
                m = getattr(ml, "Material", None)
                if m:
                    mats.append(m)
    except Exception:
        pass
    return mats

def _element_materials(ifc, element) -> List:
    mats: List = []
    try:
        for rel in element.HasAssociations or []:
            if rel.is_a("IfcRelAssociatesMaterial"):
                mats.extend(_collect_base_materials_from_def(rel.RelatingMaterial))
    except Exception:
        pass
    return mats

def _is_wood_material(mat) -> bool:
    name = (getattr(mat, "Name", "") or "").lower()
    category = (getattr(mat, "Category", "") or "").lower()
    txt = f"{name} {category}"
    return any(tag in txt for tag in ["wood", "glulam", "timber", "bsh"])

def is_epd_row(r: Dict[str, Any]) -> bool:
    try:
        name = (r.get("cp_property") or "").strip().lower()
        std = (r.get("standard") or "").strip().lower()
        note = (r.get("note") or "").strip().lower()
        return name.startswith("epd_") or "en 15804" in std or "epd" in note
    except Exception:
        return False

def pick_epd_doc_url_for_component(comp: str, dpp_docs_by_comp: Dict[str, List[str]], demo_fallback_docs: Dict[str, List[str]]) -> Optional[str]:
    def is_epd(u: str) -> bool:
        ul = u.lower()
        return ("nepd" in ul) or ("epd" in ul)
    for u in dpp_docs_by_comp.get(comp, []):
        if u and u.startswith("http") and is_epd(u):
            return u
    for u in demo_fallback_docs.get(comp, []):
        if u and u.startswith("http") and is_epd(u):
            return u
    return None

def link_property_to_doc(ifc, prop, url: str):
    if not url:
        return
    info = get_or_create_doc_info(ifc, name="Environmental Product Declaration (EPD)", identification=None, url=url, description="EPD document")
    ref = get_or_create_doc_ref_for_info(ifc, info, name=info.Name, identification=info.Identification, description=info.Description)
    # Create ExternalReferenceRelationship from property to the document reference
    for rel in ifc.by_type("IfcExternalReferenceRelationship"):
        if rel.RelatingReference == ref and prop in (rel.RelatedResourceObjects or []):
            return
    ifc.create_entity("IfcExternalReferenceRelationship", RelatingReference=ref, RelatedResourceObjects=[prop])

def find_target_elements(ifc, component: str) -> List:
    comp = (component or "").lower()
    if comp == "insulation":
        walls = list(ifc.by_type("IfcWallStandardCase")) + list(ifc.by_type("IfcWall"))
        named = [w for w in walls if "insulation" in ((w.Name or "") or "").lower()]
        return named or walls
    if comp == "pipe":
        return list(ifc.by_type("IfcPipeSegment"))
    if comp == "timber":
        elems = list(ifc.by_type("IfcColumn")) + list(ifc.by_type("IfcBeam")) + list(ifc.by_type("IfcMember"))
        wood_elems = []
        for e in elems:
            mats = _element_materials(ifc, e)
            if any(_is_wood_material(m) for m in mats):
                wood_elems.append(e)
        return wood_elems or elems
    return []

def guess_pset_name(component: str, cp_property: Optional[str] = None, standard: Optional[str] = None, note: Optional[str] = None) -> str:
    # Check if it's an EPD property
    is_epd_prop = (cp_property and cp_property.upper().startswith("EPD_")) or \
                  (standard and "en 15804" in standard.lower()) or \
                  (note and "epd" in note.lower())
    
    if is_epd_prop:
        return "CPset_EPD_Indicators"
    
    if component == "insulation":
        return "CPset_Insulation_Performance"
    if component == "pipe":
        return "CPset_Pipe_Performance"
    if component == "timber":
        return "CPset_Timber_Performance"
    return f"CPset_{component}"

def find_target_element(ifc, component: str):
    if component == "insulation":
        return first(ifc.by_type("IfcWallStandardCase")) or first(ifc.by_type("IfcWall"))
    if component == "pipe":
        return first(ifc.by_type("IfcPipeSegment"))
    if component == "timber":
        kind, obj = element_or_material_for_timber(ifc)
        return obj
    return None

def load_dpp_classes(dpp_dir: Optional[str]) -> Dict[str, Dict[str, Any]]:
    classes = {}
    if not dpp_dir or not os.path.isdir(dpp_dir):
        return classes
    for fn in os.listdir(dpp_dir):
        if not fn.lower().endswith((".json", ".jsonld")):
            continue
        try:
            data = json.load(open(os.path.join(dpp_dir, fn), "r", encoding="utf-8"))
        except Exception:
            continue
        name = (data.get("product", {}).get("name") or data.get("dpp:hasName") or "").lower()
        if "knauf" in name or "insulation" in name:
            key = "insulation"
        elif "wavin" in name or "pex" in name or "pipe" in name:
            key = "pipe"
        elif "schilliger" in name or "glulam" in name or "brettschichtholz" in name:
            key = "timber"
        else:
            key = None
        cls = data.get("product", {}).get("class") or data.get("dpp:hasClassification") or {}
        uri = cls.get("uri") or cls.get("dpp:hasConceptUri")
        label = cls.get("label") or cls.get("dpp:hasName")
        if key and uri:
            classes[key] = {"uri": uri, "label": label}
    return classes

def load_dpp_docs(dpp_dir: Optional[str]) -> Dict[str, List[str]]:
    """Collect document URLs (schema:url) from DPP files, grouped by component key."""
    docs: Dict[str, List[str]] = {"insulation": [], "pipe": [], "timber": []}
    if not dpp_dir or not os.path.isdir(dpp_dir):
        return docs
    for fn in os.listdir(dpp_dir):
        if not fn.lower().endswith((".json", ".jsonld")):
            continue
        try:
            data = json.load(open(os.path.join(dpp_dir, fn), "r", encoding="utf-8"))
        except Exception:
            continue
        name = (data.get("product", {}).get("name") or data.get("dpp:hasName") or "").lower()
        if "knauf" in name or "insulation" in name:
            key = "insulation"
        elif "wavin" in name or "pipe" in name or "pvc" in name:
            key = "pipe"
        elif "schilliger" in name or "glulam" in name or "brettschichtholz" in name:
            key = "timber"
        else:
            # Also try by DPP id keywords
            did = (data.get("id") or "").lower()
            if "knauf" in did:
                key = "insulation"
            elif "pvc" in did or "sewage" in did:
                key = "pipe"
            elif "schilliger" in did or "gl24" in did:
                key = "timber"
            else:
                key = None
        if not key:
            continue
        for coll in data.get("dpp:dataElementCollections", []):
            if coll.get("id") == "#documents":
                for el in coll.get("dpp:elements", []):
                    if el.get("type") == "dpp:Document":
                        url = (el.get("schema:url") or "").strip()
                        if url and url.startswith("http"):
                            docs.setdefault(key, []).append(url)
    return docs

def load_dpp_links(dpp_dir: Optional[str]) -> Dict[str, List[str]]:
    """Collect DPP resolver and GS1 Digital Link URLs from carrier sections, grouped by component."""
    links: Dict[str, List[str]] = {"insulation": [], "pipe": [], "timber": []}
    if not dpp_dir or not os.path.isdir(dpp_dir):
        return links
    for fn in os.listdir(dpp_dir):
        if not fn.lower().endswith((".json", ".jsonld")):
            continue
        try:
            data = json.load(open(os.path.join(dpp_dir, fn), "r", encoding="utf-8"))
        except Exception:
            continue
        # infer component key
        did = (data.get("id") or "").lower()
        name = (data.get("product", {}).get("name") or data.get("dpp:hasName") or "").lower()
        if "knauf" in did or "insulation" in name:
            key = "insulation"
        elif "pvc" in did or "sewage" in did or "pipe" in name:
            key = "pipe"
        elif "schilliger" in did or "glulam" in did or "gl24" in did or "brettschichtholz" in name:
            key = "timber"
        else:
            key = None
        if not key:
            continue
        # find carrier links
        for coll in data.get("dpp:dataElementCollections", []):
            if coll.get("id") == "#carrier":
                for el in coll.get("dpp:elements", []):
                    if el.get("id") == "#qrLink":
                        val = el.get("dpp:value", {})
                        # Prefer resolver first, then GS1 DL, both HTTP
                        resolver = (val.get("resolverUri") or "").strip()
                        gs1 = (val.get("uri") or "").strip()
                        for u in [resolver, gs1]:
                            if u and u.startswith("http"):
                                links.setdefault(key, []).append(u)
    return links

def read_mapping(mapping_csv: str):
    rows = []
    with open(mapping_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

# ----------------------- main -----------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ifc", required=True, help="Path to IFC file to patch")
    ap.add_argument("--mapping", required=True, help="CSV with component-scoped property values")
    ap.add_argument("--dpp-dir", default=None, help="Optional folder with DPP JSON-LD files to get class URIs")
    ap.add_argument("--out", default=None, help="Output IFC file. Default: adds _patched before extension")
    ap.add_argument(
        "--mode",
        choices=["values_and_refs", "refs_only"],
        default="values_and_refs",
        help="Whether to write property values from mapping (values_and_refs) or only attach external references (refs_only)",
    )
    args = ap.parse_args()

    if not os.path.isfile(args.ifc):
        msg(f"IFC not found: {args.ifc}")
        sys.exit(2)
    if not os.path.isfile(args.mapping):
        msg(f"mapping.csv not found: {args.mapping}")
        sys.exit(2)

    dpp_classes = load_dpp_classes(args.dpp_dir)
    dpp_docs_by_comp = load_dpp_docs(args.dpp_dir)
    dpp_links_by_comp = load_dpp_links(args.dpp_dir)

    # Demo fallbacks for localhost /files if no DPP docs were found
    demo_fallback_docs: Dict[str, List[str]] = {
        "insulation": [
            "http://localhost:8000/files/insul/Acoustic%20Batt%20Datasheet%20.pdf",
            "http://localhost:8000/files/insul/Data.pdf",
        ],
        "pipe": [
            "http://localhost:8000/files/pipe/NEPD-3589-2252_PVC-Sewage-Pipe.pdf",
        ],
        "timber": [
            "http://localhost:8000/files/bsh/01-Leistungserklaerung_BSH-SHI-01-01062022.pdf",
            "http://localhost:8000/files/bsh/EPD%20Schilliger_glued_laminated_timber_Glulam_as_per_EN_140802013.pdf",
        ],
    }

    ifc = ifcopenshell.open(args.ifc)

    rows = read_mapping(args.mapping)
    dict_by_comp: Dict[str, str] = {}
    docs_by_comp = {}
    for r in rows:
        comp = r["component"].strip().lower()
        dict_by_comp.setdefault(comp, r.get("dictionary_uri", ""))
        ev = (r.get("evidence_file") or "").strip()
        if ev:
            docs_by_comp.setdefault(comp, set()).add(ev)

    for r in rows:
        comp = r["component"].strip().lower()
        elements = find_target_elements(ifc, comp)
        if not elements:
            msg(f"Skip component '{comp}': no target elements found in IFC")
            continue

        # pick EPD doc url for property-to-EPD referencing
        epd_doc_url = pick_epd_doc_url_for_component(comp, dpp_docs_by_comp, demo_fallback_docs)

        for element in elements:
            # Determine Pset name (route EPD indicators to dedicated set)
            prop_name_lower = (r["cp_property"] or "").strip().lower()
            is_epd = is_epd_row(r)
            pset_name = guess_pset_name(comp, r.get("cp_property"), r.get("standard"), r.get("note"))
            pset = find_or_create_pset(ifc, element, pset_name)

            if args.mode == "values_and_refs":
                name = r["cp_property"].strip()
                val = str(r["value"]).strip()
                unit = (r.get("unit") or "").strip()
                bsdd_uri = (r.get("bsdd_property_uri") or "").strip()
                measure = ifc_measure(ifc, unit, val)
                description = bsdd_uri if bsdd_uri else None
                prop = upsert_single_value(ifc, pset, name, measure, description=description)
                # Optionally link epd property to EPD document
                if is_epd and epd_doc_url:
                    try:
                        link_property_to_doc(ifc, prop, epd_doc_url)
                    except Exception:
                        pass
            else:
                # refs_only: do not write values. Ensure the Pset exists for IDS compliance.
                _ = pset

    for comp, dict_uri in dict_by_comp.items():
        if not dict_uri:
            continue
        # Choose the most specific URI available (prefer DPP class URI, else dictionary root)
        name = dict_uri.rstrip("/").split("/")[-1]
        class_info = dpp_classes.get(comp)
        ref_uri = class_info.get("uri") if class_info and class_info.get("uri") else dict_uri
        ref_name = class_info.get("label") if class_info and class_info.get("label") else name
        ext_ref = get_or_create_external_ref(ifc, location=ref_uri, identification=None, name=ref_name)

        targets = find_target_elements(ifc, comp)
        for target in targets:
            if target:
                associate_external_to_element(ifc, target, ext_ref)
                # Also expose the classification as a document link for viewers
                try:
                    info = get_or_create_doc_info(
                        ifc,
                        name="bSDD Classification",
                        identification=None,
                        url=ref_uri,
                        description=f"Classification concept: {ref_name}",
                    )
                    ref = get_or_create_doc_ref_for_info(
                        ifc,
                        info,
                        name="bSDD Classification",
                        identification=None,
                        description=f"Classification concept: {ref_name}",
                    )
                    attach_doc_to(ifc, target, ref)
                except Exception:
                    pass

        if comp == "insulation":
            for wall in find_target_elements(ifc, "insulation"):
                for rel in (getattr(wall, "HasAssociations", None) or []):
                    if rel.is_a("IfcRelAssociatesMaterial"):
                        mat_def = rel.RelatingMaterial
                        link_external_to_material(ifc, mat_def, ext_ref)
        if comp == "timber":
            for elem in find_target_elements(ifc, "timber"):
                mats = _element_materials(ifc, elem)
                if mats:
                    for m in mats:
                        link_external_to_material(ifc, m, ext_ref)
                else:
                    associate_external_to_element(ifc, elem, ext_ref)
        if comp == "pipe":
            for pipe_elem in find_target_elements(ifc, "pipe"):
                mats = _element_materials(ifc, pipe_elem)
                if mats:
                    for m in mats:
                        link_external_to_material(ifc, m, ext_ref)
                else:
                    associate_external_to_element(ifc, pipe_elem, ext_ref)

    # Attach evidence documents with proper localhost HTTP URLs.
    for comp, paths in docs_by_comp.items():
        elements = find_target_elements(ifc, comp)
        if not elements:
            continue
        # Merge CSV-provided paths with DPP-derived docs and demo fallbacks
        merged_http_urls: List[str] = []
        # Keep only HTTP(S) from CSV entries
        for p in paths:
            if not p:
                continue
            p = p.strip()
            if p.startswith("http://") or p.startswith("https://"):
                merged_http_urls.append(p)
        # Add DPP-derived document URLs (EPD/DoP PDFs)
        merged_http_urls.extend(dpp_docs_by_comp.get(comp, []))
        # Add DPP resolver + GS1 Digital Link URLs
        merged_http_urls.extend(dpp_links_by_comp.get(comp, []))
        # If still empty, add demo fallbacks
        if not merged_http_urls:
            merged_http_urls.extend(demo_fallback_docs.get(comp, []))

        # De-duplicate while preserving order
        seen = set()
        ordered_unique = []
        for u in merged_http_urls:
            if u not in seen:
                seen.add(u)
                ordered_unique.append(u)

        for uri in ordered_unique:
            meta = infer_doc_metadata(uri)
            info = get_or_create_doc_info(
                ifc,
                name=meta.get("name") or "External Document",
                identification=meta.get("identification"),
                url=uri,
                description=meta.get("description"),
            )
            ref = get_or_create_doc_ref_for_info(
                ifc,
                info,
                name=meta.get("name") or info.Name,
                identification=meta.get("identification"),
                description=meta.get("description"),
            )
            for element in elements:
                attach_doc_to(ifc, element, ref)

    out = args.out
    if not out:
        root, ext = os.path.splitext(args.ifc)
        out = f"{root}_patched{ext or '.ifc'}"
    ifc.write(out)
    msg(f"Wrote {out}")
    msg("Done. Only CPset_* were created. bSDD URIs are preserved in property Descriptions and as external references.")
    msg("Tip: validate with your IDS against CPset_* property names.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
