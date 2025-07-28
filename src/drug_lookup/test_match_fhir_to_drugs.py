
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.drug_lookup.match_fhir_to_drugs import match_fhir_medication


# Example FHIR medication with RxNorm code (try replacing with one from your DB!)
test_med = {
    "resourceType": "Medication",
    "id": "dexamethasone",
    "code": {
        "coding": [{
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "code": "5640",   # Replace with a valid one from your database
            "display": "Dexamethasone"
        }]
    }
}

if __name__ == "__main__":
    match = match_fhir_medication(test_med)
    if match:
        print("✅ Match found:")
        for k, v in match.items():
            print(f"  {k}: {v}")
    else:
        print("❌ No match found.")



