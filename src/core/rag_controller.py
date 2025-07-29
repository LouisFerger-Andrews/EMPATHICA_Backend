import os
import re
from typing import Dict, Any
from functools import lru_cache

import src.fhir.getters as getters
from src.core.prompt_router import route_prompt, FUNCTION_FHIR, FUNCTION_DRUG
from src.core.fhir_query_builder import build_query
from src.fhir.client import fetch_fhir_resources
from .response_generator import generate_response

from src.drug_lookup.match_fhir_to_drugs import match_fhir_medication
from src.drug_lookup.query_drug_knowledge import get_drug_knowledge
from src.core.memory import PromptMemory

memory = PromptMemory()
DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "emily")

CATEGORY_GETTERS = {
    "generalInfo":        getters.get_general_info,
    "allergies":          getters.get_allergies,
    "conditions":         getters.get_conditions,
    "currentMedications": getters.get_current_medications,
    "observations":       getters.get_observations,
    "carePlan":           getters.get_carePlan,
}

# Cache drug knowledge lookups to avoid repeated SQLite hits
@lru_cache(maxsize=128)
def get_cached_drug_knowledge(slug_id: str) -> str:
    return get_drug_knowledge(slug_id)

# Very basic keyword-based name extractor (optional to refine later)
def extract_possible_drug_names(text: str) -> list:
    return re.findall(r"\b[A-Z][a-z]{2,}\b", text)  # Matches capitalized words like "Aspirin", "Ibuprofen"


def rag_inference(user_prompt: str) -> Dict[str, Any]:
    route = route_prompt(user_prompt)
    fn = route.get("function")
    args = route.get("arguments", {})

    if fn == FUNCTION_FHIR:
        pid = args.get("patient", DEFAULT_PATIENT_ID)
        categories = args.get("categories", [])
        path = build_query([], {"patient": pid})
        bundle_data = fetch_fhir_resources(path)
        bundle = [entry["resource"] for entry in bundle_data.get("entry", [])]

        parts = []
        for cat in categories:
            getter = CATEGORY_GETTERS.get(cat)
            if getter:
                parts.append(getter(bundle))

        retrieved_data = "\n\n".join(parts) or "No data found."

        # If the prompt suggests a medication-related query, extract possible drug names and filter accordingly
        drug_keywords = ["drug", "med", "side effect", "dosage", "pill", "prescription"]
        if any(kw in user_prompt.lower() for kw in drug_keywords):
            mentioned_drugs = extract_possible_drug_names(user_prompt)
            mentioned_drugs = [name.lower() for name in mentioned_drugs]

            drug_facts = []
            med_resources = [r for r in bundle if r.get("resourceType") == "Medication"]
            for med in med_resources:
                match = match_fhir_medication(med)
                if match:
                    name = match['name']
                    if name.lower() in mentioned_drugs and not memory.already_mentioned(name):
                        drug_info = get_cached_drug_knowledge(match["slug_id"])
                        if drug_info:
                            drug_facts.append(f"• {name}:\n{drug_info}")
                            memory.remember_drug(name)

            if drug_facts:
                retrieved_data += "\n\n--- Drug Information ---\n" + "\n\n".join(drug_facts)

        final_response = generate_response(user_prompt, retrieved_data)
        memory.update(user_prompt, final_response)

        return {"source": "fhir", "response": final_response}

    elif fn == FUNCTION_DRUG:
        drug = args.get("drug_name")
        if drug:
            match = match_fhir_medication({"name": drug})
            if match:
                drug_info = get_cached_drug_knowledge(match["slug_id"])
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
