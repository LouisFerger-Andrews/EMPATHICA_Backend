# src/core/summarizer.py

"""
summarizer.py

Converts a FHIR Bundle into a concise plain‑text summary.
Supports:
  - Observation.valueQuantity
  - Observation.component (e.g. CBC/CMP)
  - MedicationStatement entries, resolving references to Medication resources
"""

from typing import Any, Dict, List

def summarize_fhir_bundle(bundle: Dict[str, Any]) -> str:
    entries = bundle.get("entry", [])
    # First, index all Medication resources by their ID
    med_index = {}
    for entry in entries:
        res = entry.get("resource", {})
        if res.get("resourceType") == "Medication":
            med_index[res["id"]] = res

    lines: List[str] = []
    for entry in entries:
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType")

        if rtype == "Observation":
            when = resource.get("effectiveDateTime") or resource.get("issued") or ""
            # Single‐value
            if "valueQuantity" in resource:
                coding = resource.get("code", {}).get("coding", [])
                name = coding[0].get("display") if coding else resource.get("code", {}).get("text")
                value = resource["valueQuantity"].get("value")
                unit  = resource["valueQuantity"].get("unit", "")
                if name and value is not None:
                    lines.append(f"{when}: {name} = {value}{unit}")
            # Component list
            for comp in resource.get("component", []):
                comp_name  = comp.get("code", {}).get("text")
                comp_value = comp.get("valueQuantity", {}).get("value")
                comp_unit  = comp.get("valueQuantity", {}).get("unit", "")
                if comp_name and comp_value is not None:
                    lines.append(f"{when}: {comp_name} = {comp_value}{comp_unit}")

        elif rtype == "MedicationStatement":
            status = resource.get("status")
            period = resource.get("effectivePeriod", {})
            start  = period.get("start") or ""
            # Resolve medicationReference → Medication resource ID
            ref = resource.get("medicationReference", {}).get("reference", "")
            # reference format: "urn:uuid:med-ondansetron"
            med_id = ref.rsplit("-", 1)[-1]
            med_res = med_index.get(med_id, {})
            # Try codeableConcept on the statement; fallback to Medication resource code
            med_name = (
                resource.get("medicationCodeableConcept", {})
                        .get("text")
                or med_res.get("code", {}).get("coding", [{}])[0].get("display")
                or med_id
            )
            lines.append(f"{start}: {med_name} (status: {status})")

    return "\n".join(lines) if lines else "No relevant data found."
