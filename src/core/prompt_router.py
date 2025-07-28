import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from .response_generator import generate_response


load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
DEFAULT_PATIENT_ID = os.getenv("DEFAULT_PATIENT_ID", "emily")


FUNCTION_FHIR = "get_fhir_resources"
FUNCTION_DRUG = "get_drug_info"

ALLOWED_CATEGORIES = [
    "generalInfo",
    "allergies",
    "conditions",
    "currentMedications",
    "observations",
    "carePlan",
]

FHIR_FUNCTION_DEF = json.dumps({
    "name": FUNCTION_FHIR,
    "description": "Fetch patient-specific FHIR data categories",
    "parameters": {
        "type": "object",
        "properties": {
            "patient": {"type": "string", "description": "The patient identifier"},
            "categories": {
                "type": "array",
                "items": {"type": "string", "enum": ALLOWED_CATEGORIES},
                "description": "Which FHIR categories to retrieve"
            }
        },
        "required": ["patient", "categories"]
    }
}, indent=2)

DRUG_FUNCTION_DEF = json.dumps({
    "name": FUNCTION_DRUG,
    "description": "Look up information for a given drug",
    "parameters": {
        "type": "object",
        "properties": {
            "drug_name": {"type": "string", "description": "Name of the drug to look up"}
        },
        "required": ["drug_name"]
    }
}, indent=2)

def route_prompt(prompt: str) -> Dict[str, Any]:
    system_instruction = (
        "You are a clinical assistant. Based on the user's prompt, choose exactly ONE function:\n"
        f"- {FUNCTION_FHIR}(patient, categories)\n"
        f"- {FUNCTION_DRUG}(drug_name)\n\n"
        "Respond ONLY with JSON in this exact format:\n"
        "{\n"
        '  "name": "<function name>",\n'
        '  "arguments": {<arguments JSON>}\n'
        "}\n"
        "DO NOT provide any other explanation or text.\n\n"
        f"Use '{DEFAULT_PATIENT_ID}' as the patient identifier by default.\n"
        f"Allowed categories for FHIR are: {', '.join(ALLOWED_CATEGORIES)}.\n"
    )

    full_prompt = (
        f"{system_instruction}\n\n"
        f"Available functions:\n{FHIR_FUNCTION_DEF}\n{DRUG_FUNCTION_DEF}\n\n"
        f"User prompt: {prompt}\n\n"
        "Respond with ONLY the JSON object specifying the chosen function and arguments."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "format": "json",
        "stream": False
    }

    resp = requests.post(OLLAMA_API_URL, json=payload)
    resp.raise_for_status()
    data = resp.json()

    if 'response' not in data:
        raise RuntimeError(f"Ollama API returned unexpected response: {data}")

    try:
        response_json = json.loads(data["response"])
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Could not decode JSON from Ollama response: {data['response']}") from e

    function_name = response_json.get("name")
    arguments = response_json.get("arguments", {})

    if not function_name:
        return {"function": None, "arguments": {}}

    return {
        "function": function_name,
        "arguments": arguments
    }
