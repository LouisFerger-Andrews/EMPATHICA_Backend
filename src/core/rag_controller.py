# src/core/rag_controller.py

import os
from typing import Dict, Any

import src.fhir.getters as getters
from src.core.prompt_router import route_prompt, FUNCTION_FHIR, FUNCTION_DRUG
from src.core.fhir_query_builder import build_query
from src.fhir.client import fetch_fhir_resources
from .response_generator import generate_response

from src.drug_lookup.match_fhir_to_drugs import match_fhir_medication
from src.drug_lookup.query_drug_knowledge import get_drug_knowledge

DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "emily")

CATEGORY_GETTERS = {
    "generalInfo":        getters.get_general_info,
    "allergies":          getters.get_allergies,
    "conditions":         getters.get_conditions,
    "currentMedications": getters.get_current_medications,
    "observations":       getters.get_observations,
    "carePlan":           getters.get_carePlan,
}


def rag_inference(user_prompt: str) -> Dict[str, Any]:
    route = route_prompt(user_prompt)
    fn = route.get("function")  # ← keep "function" to match your router
    args = route.get("arguments", {})

    if fn == FUNCTION_FHIR:
        pid = args.get("patient", DEFAULT_PATIENT_ID)
        categories = args.get("categories", [])

        # Fetch patient bundle
        path = build_query([], {"patient": pid})
        bundle_data = fetch_fhir_resources(path)  # returns full FHIR Bundle
        bundle = [entry["resource"] for entry in bundle_data.get("entry", [])]  # flat list of resources

        # FHIR section assembly
        parts = []
        for cat in categories:
            getter = CATEGORY_GETTERS.get(cat)
            if getter:
                parts.append(getter(bundle))

        retrieved_data = "\n\n".join(parts) or "No data found."

        # Add drug facts if we're getting current medications
        if "currentMedications" in categories:
            drug_facts = []
            med_resources = [r for r in bundle if r.get("resourceType") == "Medication"]
            for med in med_resources:
                match = match_fhir_medication(med)
                if match:
                    drug_info = get_drug_knowledge(match["slug_id"])
                    if drug_info:
                        drug_facts.append(f"• {match['name']}:\n{drug_info}")

            if drug_facts:
                retrieved_data += "\n\n--- Drug Information ---\n" + "\n\n".join(drug_facts)

        print("\n--- RAG RETRIEVED DATA ---")
        print(retrieved_data)

        final_response = generate_response(user_prompt, retrieved_data)
        return {"source": "fhir", "response": final_response}

    elif fn == FUNCTION_DRUG:
        drug = args.get("drug_name")
        if drug:
            match = match_fhir_medication({"name": drug})
            if match:
                drug_info = get_drug_knowledge(match["slug_id"])
                return {"source": "drug", "response": f"🧪 {match['name']}:\n{drug_info}"}
            else:
                return {"source": "drug", "response": f"Sorry, I couldn’t find info on '{drug}'."}
        else:
            return {"source": "drug", "response": "No drug name provided."}

    else:
        return {"source": None, "response": "Sorry, I didn’t understand your request."}


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Which medications am I taking?"
    res = rag_inference(q)
    print(f"[{res['source']}] {res['response']}")
