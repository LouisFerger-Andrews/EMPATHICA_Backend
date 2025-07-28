# src/core/fhir_query_builder.py

"""
fhir_query_builder.py

For local bundles: picks the correct patient file by ID (filters['patient'])
and ignores resource_types entirely (you’ll filter within the bundle).
"""

import os
from typing import List, Dict

LOCAL_FHIR_DATA_DIR = os.getenv("LOCAL_FHIR_DATA_DIR", "./data/fhir")

def build_query(
    resource_types: List[str],
    filters: Dict[str, str]
) -> str:
    """
    Returns the filesystem path for the patient’s bundle JSON.

    Expects:
      filters['patient'] == patient_id  (e.g. 'emily')
    """
    patient_id = filters.get("patient")
    if not patient_id:
        raise ValueError("Missing 'patient' filter for local FHIR lookup")

    file_path = os.path.join(LOCAL_FHIR_DATA_DIR, f"{patient_id}.json")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"No local FHIR file for patient '{patient_id}': {file_path}")
    return file_path
