# test_llm_integration.py

import os
from dotenv import load_dotenv
from src.core.rag_controller import rag_inference

load_dotenv()  # so OLLAMA_MODEL gets loaded

if __name__ == "__main__":
    prompts = [
        "What allergies do I have?",
        "Show me my current medications.",
        "List my labs and current meds.",
        "Give me my birth date and gender.",
        "What therapy sessions are scheduled?"
    ]

    for p in prompts:
        print(f"\n>>> PROMPT: {p}")
        result = rag_inference(p)
        print(f"[{result['source']}]\n{result['response']}")
