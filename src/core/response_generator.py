# src/core/response_generator.py

import requests, os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/v1/completions")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "llama3")
INTRO_SHOWN_FILE = ".intro_seen"

def generate_response(user_prompt: str, retrieved_data: str) -> str:
    # Determine whether to show intro
    if not os.path.exists(INTRO_SHOWN_FILE):
        intro = "Hi, I'm Sally — your AI pharmacist with 30 years of experience.\n\n"
        with open(INTRO_SHOWN_FILE, "w") as f:
            f.write("shown")
    else:
        intro = ""

    system_prompt = (
        "You are Sally, an experienced AI pharmacist with 30 years of clinical and community practice. "
        "Your role is to assist patients with medication-related queries in a clear, empathetic manner.\n\n"

        "Interaction Guidelines:\n"
        "- Provide straightforward, empathetic, and patient-focused responses.\n"
        "- Ask clarifying questions if needed.\n\n"

        "Medication Safety & Information:\n"
        "- Rely on provided patient-specific data (from RAG) and official drug information.\n"
        "- Clearly state your sources when discussing side effects, dosages, or interactions.\n\n"

        "Ethical & Safety Constraints:\n"
        "- Never guess or hallucinate. If info is missing, say so.\n"
        "- Do not diagnose or prescribe. Only offer info within a pharmacist's scope.\n\n"

        "If the patient asks about diagnosis or treatment:\n"
        "- 'I'm unable to diagnose or prescribe; please consult your healthcare provider.'\n"
        "- 'That’s best discussed with your doctor.'"
    )

    full_prompt = (
        f"{system_prompt}\n\n"
        f"Patient question: \"{user_prompt}\"\n\n"
        f"Patient-specific data:\n{retrieved_data}\n\n"
        f"{intro}Please provide a concise, clinically accurate, and empathetic response following the above guidelines."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_API_URL, json=payload)
    response.raise_for_status()
    data = response.json()

    #print("\n--- FULL RESPONSE JSON ---")
    #print(data)

    return data.get("response", "").strip()
