"""
getters.py

Small functions that extract exactly one category from a FHIR resource list.
Each returns a plain‑text summary of that section.
"""

from typing import List, Dict, Any

def get_general_info(resources: List[Dict[str, Any]]) -> str:
    for r in resources:
        if r.get("resourceType") == "Patient":
            name = " ".join(r.get("name", [{}])[0].get("given", [])) + " " + r.get("name", [{}])[0].get("family", "")
            gender = r.get("gender", "unknown")
            dob = r.get("birthDate", "unknown")
            return f"Patient: {name.strip()}, Gender: {gender}, DOB: {dob}"
    return "No patient demographics found."


def get_allergies(resources: List[Dict[str, Any]]) -> str:
    lines = []
    for r in resources:
        if r.get("resourceType") == "AllergyIntolerance":
            code = r.get("code", {}).get("text") or r.get("code", {}).get("coding", [{}])[0].get("display")
            lines.append(f"Allergy: {code}")
    return "\n".join(lines) if lines else "No allergies recorded."


def get_conditions(resources: List[Dict[str, Any]]) -> str:
    lines = []
    for r in resources:
        if r.get("resourceType") == "Condition":
            code = r.get("code", {}).get("text") or r.get("code", {}).get("coding", [{}])[0].get("display")
            onset = r.get("onsetDateTime", "unknown date")
            lines.append(f"{onset}: {code}")
    return "\n".join(lines) if lines else "No conditions recorded."


def get_current_medications(resources: List[Dict[str, Any]]) -> str:
    # build med index for names
    med_index = {}
    for r in resources:
        if r.get("resourceType") == "Medication":
            med_index[r["id"]] = (
                r.get("code", {}).get("coding", [{}])[0].get("display")
                or r.get("code", {}).get("text")
            )

    lines = []
    for r in resources:
        if r.get("resourceType") == "MedicationStatement":
            ref = r.get("medicationReference", {}).get("reference", "")
            med_id = ref.split("/")[-1].split("-")[-1]
            name = med_index.get(med_id, med_id)
            status = r.get("status", "")
            lines.append(f"{name} (status: {status})")
    return "\n".join(lines) if lines else "No current medications."


def get_observations(resources: List[Dict[str, Any]]) -> str:
    lines = []
    for r in resources:
        if r.get("resourceType") == "Observation":
            when = r.get("effectiveDateTime", "")
            for c in r.get("component", []):
                name = c.get("code", {}).get("text")
                val  = c.get("valueQuantity", {}).get("value")
                unit = c.get("valueQuantity", {}).get("unit", "")
                if name and val is not None:
                    lines.append(f"{when}: {name} = {val}{unit}")
    return "\n".join(lines) if lines else "No observations."


def get_carePlan(resources: List[Dict[str, Any]]) -> str:
    lines = []
    for r in resources:
        if r.get("resourceType") == "CarePlan":
            for act in r.get("activity", []):
                txt = act.get("detail", {}).get("code", {}).get("text")
                lines.append(f"CarePlan: {txt}")
    return "\n".join(lines) if lines else "No care plan activities."
