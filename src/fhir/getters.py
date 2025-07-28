"""
getters.py

Small functions that extract exactly one category from a FHIR resource list.
Each returns a plain‑text summary of that section.
"""

from typing import List, Dict, Any, Optional

# ---------- small helpers ----------

def _codeable_text(obj: Dict[str, Any]) -> Optional[str]:
    """Return the best human-readable text from a FHIR CodeableConcept-like dict."""
    if not obj:
        return None
    if isinstance(obj, dict):
        if obj.get("text"):
            return obj["text"]
        codings = obj.get("coding") or []
        for c in codings:
            if c.get("display"):
                return c["display"]
            if c.get("code"):
                return c["code"]
    return None

def _resolve_med_name(ms: Dict[str, Any], med_index: Dict[str, str]) -> str:
    """
    Get medication name from a MedicationStatement.
    Handles both medicationCodeableConcept and medicationReference.
    """
    # 1) Inline CodeableConcept (Mary style)
    cc = ms.get("medicationCodeableConcept")
    txt = _codeable_text(cc)
    if txt:
        return txt

    # 2) Reference (Emily style)
    ref = (ms.get("medicationReference") or {}).get("reference")  # e.g. "urn:uuid:med-ibuprofen" or "Medication/ibuprofen"
    if ref:
        # Try direct lookup with whole ref
        if ref in med_index:
            return med_index[ref]
        # Strip common prefixes
        key = ref.split("/")[-1]  # after "Medication/"
        if key in med_index:
            return med_index[key]
        # Also store/try uuid part
        if ref.startswith("urn:uuid:"):
            uuid_part = ref.split("urn:uuid:")[-1]
            return med_index.get(uuid_part, uuid_part)

    return "Unknown medication"

def _id(resource: Dict[str, Any]) -> str:
    return resource.get("id", "unknown-id")


# ---------- getters ----------

def get_general_info(resources: List[Dict[str, Any]]) -> str:
    for r in resources:
        if r.get("resourceType") == "Patient":
            name_part = r.get("name", [{}])[0]
            given = " ".join(name_part.get("given", []))
            family = name_part.get("family", "")
            full = (given + " " + family).strip() or name_part.get("text", "Unknown")
            gender = r.get("gender", "unknown")
            dob = r.get("birthDate", "unknown")
            return f"Patient: {full}, Gender: {gender}, DOB: {dob}"
    return "No patient demographics found."


def get_allergies(resources: List[Dict[str, Any]]) -> str:
    lines = []
    for r in resources:
        if r.get("resourceType") == "AllergyIntolerance":
            # R4 uses 'code', older examples may use 'substance'
            code_txt = _codeable_text(r.get("code")) or _codeable_text(r.get("substance"))
            # reactions
            manifests = []
            for react in r.get("reaction", []):
                for m in react.get("manifestation", []):
                    t = _codeable_text(m) or m.get("text")
                    if t:
                        manifests.append(t)
            man_str = "; ".join(manifests) if manifests else ""
            status = r.get("status", "")
            if code_txt:
                if man_str:
                    lines.append(f"Allergy: {code_txt} – {man_str} (status: {status})")
                else:
                    lines.append(f"Allergy: {code_txt} (status: {status})")
    return "\n".join(lines) if lines else "No allergies recorded."


def get_conditions(resources: List[Dict[str, Any]]) -> str:
    lines = []
    for r in resources:
        if r.get("resourceType") == "Condition":
            code = _codeable_text(r.get("code")) or "(no description)"
            onset = r.get("onsetDateTime") or r.get("recordedDate") or "unknown date"
            lines.append(f"{onset}: {code}")
    return "\n".join(lines) if lines else "No conditions recorded."


def get_current_medications(resources: List[Dict[str, Any]]) -> str:
    # Build med index by various keys we might see in references
    med_index: Dict[str, str] = {}
    for r in resources:
        if r.get("resourceType") == "Medication":
            display = _codeable_text(r.get("code")) or _id(r)
            rid = _id(r)
            med_index[rid] = display
            med_index[f"Medication/{rid}"] = display
            med_index[f"urn:uuid:{rid}"] = display  # cover urn form

    lines = []
    for r in resources:
        if r.get("resourceType") == "MedicationStatement":
            name = _resolve_med_name(r, med_index)
            status = r.get("status", "")
            lines.append(f"{name} (status: {status})")
    return "\n".join(lines) if lines else "No current medications."


def get_observations(resources: List[Dict[str, Any]]) -> str:
    lines = []
    for r in resources:
        if r.get("resourceType") == "Observation":
            when = r.get("effectiveDateTime") or r.get("effectivePeriod", {}).get("start", "")
            # Some observations have a single value, not component
            if "component" in r and r["component"]:
                comps = r["component"]
            else:
                comps = [{"code": r.get("code", {}), "valueQuantity": r.get("valueQuantity")}]

            for c in comps:
                name = _codeable_text(c.get("code")) or c.get("code", {}).get("text")
                vq = c.get("valueQuantity") or {}
                val = vq.get("value")
                unit = vq.get("unit", "")
                if name and val is not None:
                    lines.append(f"{when}: {name} = {val}{unit}")
    return "\n".join(lines) if lines else "No observations."


def get_carePlan(resources: List[Dict[str, Any]]) -> str:
    lines = []
    for r in resources:
        if r.get("resourceType") == "CarePlan":
            title = r.get("title")
            if title:
                lines.append(f"CarePlan Title: {title}")
            for act in r.get("activity", []):
                txt = _codeable_text(act.get("detail", {}).get("code")) or act.get("detail", {}).get("description")
                sched = act.get("detail", {}).get("scheduledPeriod", {})
                sched_txt = ""
                if sched:
                    sched_txt = f" [{sched.get('start', '')} → {sched.get('end', '')}]"
                if txt:
                    lines.append(f"- {txt}{sched_txt}")
    return "\n".join(lines) if lines else "No care plan activities."
