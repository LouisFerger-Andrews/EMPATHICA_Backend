# verify_fhir_local.py

from src.core.fhir_query_builder import build_query
from src.fhir.client            import fetch_fhir_resources
from src.core.summarizer        import summarize_fhir_bundle

def main():
    # Load the entire patient bundle
    path   = build_query([], {"patient": "emily"})
    bundle = fetch_fhir_resources(path)
    print("\n=== Summary for emily ===\n")
    print(summarize_fhir_bundle(bundle))

if __name__ == "__main__":
    main()
