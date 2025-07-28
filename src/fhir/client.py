"""
client.py

Loads FHIR data exclusively from local JSON files. Always treats the provided
path as a filesystem path and returns its parsed JSON content.
"""
import json
from typing import Dict, Any

def fetch_fhir_resources(file_path: str) -> Dict[str, Any]:
    """
    Reads the given file_path from disk and returns its JSON content as a dict.

    Parameters:
        file_path: Path to a local FHIR JSON file.

    Returns:
        Parsed JSON as a Python dict.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
