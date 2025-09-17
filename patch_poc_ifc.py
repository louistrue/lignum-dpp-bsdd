# Write the IFC patch script to disk for the user to download and run locally.
script_path = "/mnt/data/patch_poc_ifc.py"
script_code = r'''#!/usr/bin/env python3
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
from typing import Dict, Any, Optional

try:
    import ifcopenshell
except Exception as e:
    print("This script requires ifcopenshell. Install with: pip install ifcopenshell")
    raise

# ----------------------- helpers -----------------------

def msg(s: str):
    print(f"[patch] {s}")

def first(items):
    return items[0] if items else None

def get_owner_history(ifc):
    # Try to reuse an existing OwnerHistory, otherwise create minimal one
    oh = first(ifc.by_type("IfcOwnerHistory"))
    if oh:
        return oh
    person = ifc.create_entity("IfcPerson", Identification="POC", FamilyName="LTplus")
    org = ifc.create_entity("IfcOrganization", Identification="LT+", Name="LTplus AG")
    person_and_org = ifc.create_entity("IfcPersonAndOrganization", ThePerson=person, TheOrganization=org)
    app = ifc.create_entity("IfcApplication", ApplicationDeveloper=org, Version="0.1", ApplicationFullName="LT+ POC Patcher", ApplicationIdentifier="LT+POC")
    return ifc.create_entity("IfcOwnerHistory", OwningUser=person_and_org, OwningApplication=app)

def ensure_rel_defines_by_properties(ifc, element, pset):
    # Link a pset to an element via IfcRelDefinesByProperties if not already linked
    rels = [r for r in ifc.by_type("IfcRelDefinesByProperties") if r.RelatingPropertyDefinition == pset and element in (r.RelatedObjects or [])]
    if not rels:
        ifc.create_entity("IfcRelDefinesByProperties", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[element], RelatingPropertyDefinition=pset)

def find_or_create_pset(ifc, element, pset_name: str):
    # Try to find an existing CPset_* by name on element
    for rel in element.IsDefinedBy or []:
        try:
            if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition and rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
                ps = rel.RelatingPropertyDefinition
                if ps.Name == pset_name:
                    return ps
        except:
            pass
    # Otherwise create it
    owner = get_owner_history(ifc)
    pset = ifc.create_entity("IfcPropertySet", GlobalId=ifcopenshell.guid.new(), OwnerHistory=owner, Name=pset_name, HasProperties=[])
    ensure_rel_defines_by_properties(ifc, element, pset)
    msg(f"Created {pset_name} on #{element.id()} {element.is_a()}")
    return pset

def ifc_measure(ifc, unit: Optional[str], value_text: str):
    """
    Returns an IFC measure entity for the given unit and string value.
    Rules for this POC:
      - W/mK -> IfcThermalConductivityMeasure (float)
      - kg/m3 -> IfcMassDensityMeasure (float)
      - mm or m -> IfcPositiveLengthMeasure (float)
      - '-' with numeric -> IfcReal
      - otherwise -> IfcLabel (text)
    """
    v = value_text.strip()
    # try numeric
    is_num = False
    try:
        num = float(v)
        is_num = True
    except:
        num = None
    if unit:
        u = unit.strip().lower()
    else:
        u = ""

    if u in ["w/mk", "w/m·k", "w m-1 k-1"] and is_num:
        return ifc.create_entity("IfcThermalConductivityMeasure", num)
    if u in ["kg/m3", "kg/m^3", "kg m-3"] and is_num:
        return ifc.create_entity("IfcMassDensityMeasure", num)
    if u in ["mm", "m"] and is_num:
        return ifc.create_entity("IfcPositiveLengthMeasure", num)
    if u in ["-", ""] and is_num:
        return ifc.create_entity("IfcReal", num)
    # fallback text
    return ifc.create_entity("IfcLabel", v)

def upsert_single_value(ifc, pset, name: str, value_entity, description: Optional[str] = None):
    # Update if existing, else create
    props = {p.Name: p for p in (pset.HasProperties or []) if p.is_a("IfcPropertySingleValue")}
    if name in props:
        prop = props[name]
        prop.NominalValue = value_entity
        if description is not None:
            prop.Description = description
    else:
        prop = ifc.create_entity("IfcPropertySingleValue", Name=name, Description=description, NominalValue=value_entity, Unit=None)
        pset.HasProperties = list(pset.HasProperties or []) + [prop]
    return prop

def get_or_create_doc_ref(ifc, name: str, uri: str):
    # Reuse if same Location and Name exists
    for d in ifc.by_type("IfcDocumentReference"):
        if (d.Location or "").strip() == uri.strip() and (d.Name or "") == name:
            return d
    return ifc.create_entity("IfcDocumentReference", Location=uri, Name=name, Description=None, Identification=None, ReferencedDocument=None)

def attach_doc_to(ifc, element, doc_ref):
    # Link via IfcRelAssociatesDocument
    for rel in ifc.by_type("IfcRelAssociatesDocument"):
        if rel.RelatingDocument == doc_ref and element in (rel.RelatedObjects or []):
            return
    ifc.create_entity("IfcRelAssociatesDocument", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[element], RelatingDocument=doc_ref)

def get_or_create_classification(ifc, name: str, location: str, edition: str = None, source: str = None):
    for c in ifc.by_type("IfcClassification"):
        if (c.Name or "") == name and (c.Location or "") == location:
            return c
    return ifc.create_entity("IfcClassification", Source=source, Edition=edition, Name=name, Description=None, Location=location, ReferenceTokens=None)

def get_or_create_class_ref(ifc, classification, class_uri: str, identification: str = None, name: str = None):
    for cr in ifc.by_type("IfcClassificationReference"):
        if cr.ReferencedSource == classification and (cr.Location or "") == class_uri:
            return cr
    return ifc.create_entity("IfcClassificationReference", Location=class_uri, Identification=identification, Name=name, ReferencedSource=classification)

def associate_class_to_element(ifc, element, class_ref):
    # IfcRelAssociatesClassification
    for rel in ifc.by_type("IfcRelAssociatesClassification"):
        if rel.RelatingClassification == class_ref and element in (rel.RelatedObjects or []):
            return
    ifc.create_entity("IfcRelAssociatesClassification", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[element], RelatingClassification=class_ref)

def link_class_to_material(ifc, material, class_ref):
    # IfcExternalReferenceRelationship for MaterialDefinition
    for rel in ifc.by_type("IfcExternalReferenceRelationship"):
        if rel.RelatingReference == class_ref and material in (rel.RelatedResourceObjects or []):
            return
    ifc.create_entity("IfcExternalReferenceRelationship", RelatingReference=class_ref, RelatedResourceObjects=[material])

def element_or_material_for_timber(ifc):
    # Prefer a structural member, else a material that looks like glulam
    cand = first(ifc.by_type("IfcMember")) or first(ifc.by_type("IfcBeam"))
    if cand:
        return ("element", cand)
    # search materials
    for m in ifc.by_type("IfcMaterial"):
        n = (m.Name or "").lower()
        if "glulam" in n or "brettschichtholz" in n or "schilliger" in n:
            return ("material", m)
    # fallback to wall
    w = first(ifc.by_type("IfcWallStandardCase")) or first(ifc.by_type("IfcWall"))
    return ("element", w) if w else (None, None)

def guess_pset_name(component: str) -> str:
    if component == "insulation":
        return "CPset_Insulation_Performance"
    if component == "pipe":
        return "CPset_Pipe_DimensionsAndRatings"
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
        # Try to infer component key from product name
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
    args = ap.parse_args()

    if not os.path.isfile(args.ifc):
        msg(f"IFC not found: {args.ifc}")
        sys.exit(2)
    if not os.path.isfile(args.mapping):
        msg(f"mapping.csv not found: {args.mapping}")
        sys.exit(2)

    dpp_classes = load_dpp_classes(args.dpp_dir)

    ifc = ifcopenshell.open(args.ifc)

    rows = read_mapping(args.mapping)
    # Aggregate dictionary URI and doc evidence per component
    dict_by_comp: Dict[str, str] = {}
    docs_by_comp = {}
    for r in rows:
        comp = r["component"].strip().lower()
        dict_by_comp.setdefault(comp, r.get("dictionary_uri", ""))
        ev = (r.get("evidence_file") or "").strip()
        if ev:
            docs_by_comp.setdefault(comp, set()).add(ev)

    # Iterate rows and write CPset properties
    for r in rows:
        comp = r["component"].strip().lower()
        element = find_target_element(ifc, comp)
        if element is None:
            msg(f"Skip component '{comp}': no target element found in IFC")
            continue

        pset_name = guess_pset_name(comp)
        pset = find_or_create_pset(ifc, element, pset_name)

        name = r["cp_property"].strip()
        val = str(r["value"]).strip()
        unit = (r.get("unit") or "").strip()
        bsdd_uri = (r.get("bsdd_property_uri") or "").strip()
        measure = ifc_measure(ifc, unit, val)
        # Store bSDD property URI in Description for traceability
        description = bsdd_uri if bsdd_uri else None
        upsert_single_value(ifc, pset, name, measure, description=description)

    # Create dictionary classifications and class references, then associate
    for comp, dict_uri in dict_by_comp.items():
        if not dict_uri:
            continue
        # Use last path part as short name
        name = dict_uri.rstrip("/").split("/")[-1]
        classification = get_or_create_classification(ifc, name=name, location=dict_uri, edition=None, source="demo2025")
        # Try to get a class URI from DPPs
        class_info = dpp_classes.get(comp)
        if class_info and class_info.get("uri"):
            class_ref = get_or_create_class_ref(ifc, classification, class_uri=class_info["uri"], identification=None, name=class_info.get("label"))
        else:
            # create a generic reference to the dictionary root
            class_ref = get_or_create_class_ref(ifc, classification, class_uri=dict_uri, identification=None, name=name)

        target = find_target_element(ifc, comp)
        if target:
            associate_class_to_element(ifc, target, class_ref)

        # Also try to link to a material if available
        if comp == "insulation":
            # find material of wall if any
            wall = find_target_element(ifc, "insulation")
            if wall and hasattr(wall, "HasAssociations"):
                # naive scan
                for rel in wall.HasAssociations or []:
                    if rel.is_a("IfcRelAssociatesMaterial"):
                        mat_def = rel.RelatingMaterial
                        link_class_to_material(ifc, mat_def, class_ref)
        if comp == "timber":
            kind, obj = element_or_material_for_timber(ifc)
            if obj:
                if kind == "material":
                    link_class_to_material(ifc, obj, class_ref)
                else:
                    associate_class_to_element(ifc, obj, class_ref)

    # Attach documents from mapping rows
    for comp, paths in docs_by_comp.items():
        element = find_target_element(ifc, comp)
        if not element:
            continue
        for p in paths:
            if not p:
                continue
            uri = p if p.startswith("http") or p.startswith("file://") else "file://" + p
            doc = get_or_create_doc_ref(ifc, name="datasource", uri=uri)
            attach_doc_to(ifc, element, doc)

    # Save IFC
    out = args.out
    if not out:
        root, ext = os.path.splitext(args.ifc)
        out = f"{root}_patched{ext or '.ifc'}"
    ifc.write(out)
    msg(f"Wrote {out}")
    msg("Done. Only CPset_* were created. bSDD URIs are preserved in property Descriptions and in classification links.")
    msg("Tip: validate with your IDS against CPset_* property names.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
with open(script_path, "w", encoding="utf-8") as f:
    f.write(script_code)

script_path
