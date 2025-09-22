
# EMPATHICA\_Backend – 5‑Minute Quickstart

A **copy/paste friendly** guide to get the project running locally: create the drug DB, build FAISS indexes, load FHIR bundles, and test the RAG pipeline.

---

## TL;DR (run this first)

```bash
# 0) Clone & enter
git clone git@github.com:LouisFerger-Andrews/EMPATHICA_Backend.git
cd EMPATHICA_Backend

# 1) Python env
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt   # or: pip install -r requirements-dev.txt

# 2) Build drug DB (or skip if you already have data/drugs/drugs.db)
python scripts/build_drug_db.py --raw data/drugs/raw --out data/drugs/drugs.db

# 3) Create vector indexes
python scripts/build_faiss_index.py --in data/drugs/drugs.db --out data/drugs/faiss_index
python scripts/build_fhir_index.py  --in data/fhir/ --out data/fhir/faiss_index

# 4) Set env vars (example)
export OPENAI_API_KEY=sk-...
export DEFAULT_PATIENT_ID=maria

# 5) Smoke test
python testing_first_llm_fhir_RAG.py  # ask a few prompts
```

> Adjust script names/paths if yours differ (see **Scripts & Entry Points** below).

---

## Requirements

* **Python** ≥ 3.10 (3.11+ recommended)
* gcc/clang toolchain (for `faiss-cpu` wheels sometimes)
* (Optional) **Git LFS** if you ever need to push large artifacts: `git lfs install`
* OS: macOS/Linux/WSL2 (Windows native works, but paths differ)

### Core Python Libraries

These *should* already be in `requirements.txt`, but if you’re installing manually:

* `faiss-cpu` (or `faiss-gpu` if you want GPU)
* `fhir.resources` (or `fhirclient`) for FHIR parsing
* `pydantic`, `pandas`, `numpy`
* `langchain` / `llama-index` / your chosen RAG stack
* `openai` (or other model SDK you use)
* `sqlalchemy` (if you manipulate the SQLite drug DB)
* `uvicorn`, `fastapi` (if you expose an API server)

---

## Project Structure (key folders)

```
EMPATHICA_Backend/
├── data/
│   ├── drugs/
│   │   ├── raw/                 # raw CSV/JSON source files for drug data
│   │   ├── drugs.db             # generated SQLite DB (ignore in git)
│   │   ├── faiss_index/         # vector index output
│   │   └── faiss_metadata.json  # index metadata
│   └── fhir/
│       ├── emily.json
│       ├── maria.json
│       └── faiss_index/
├── src/
│   ├── core/
│   │   └── rag_controller.py
│   ├── fhir/
│   │   ├── client.py
│   │   └── getters.py
│   └── drugs/
│       └── build_db.py          # (example) script code
├── scripts/                      # CLI helpers (build_db, build_index, etc.)
├── testing_first_llm_fhir_RAG.py
├── requirements.txt
└── README.md
```

(Your actual tree may vary—update this section to match.)

---

## Step-by-Step Setup

### 1. Clone & virtualenv

```bash
git clone git@github.com:LouisFerger-Andrews/EMPATHICA_Backend.git
cd EMPATHICA_Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. (Re)Create the Drug SQLite DB

If `data/drugs/drugs.db` is missing (because it was stripped from git):

```bash
python scripts/build_drug_db.py \
  --raw data/drugs/raw \
  --out data/drugs/drugs.db
```

**What this script should do:**

* Parse CSV/JSON under `data/drugs/raw`
* Normalize fields (name, ndc, etc.)
* Insert into SQLite (`drugs.db`)

> If you don’t have this script yet, write one quickly (see template below).

### 3. Build FAISS Indexes

#### Drugs

```bash
python scripts/build_faiss_index.py \
  --in data/drugs/drugs.db \
  --out data/drugs/faiss_index
```

This should:

* Read rows from `drugs.db`
* Embed with your model (OpenAI, HF, etc.)
* Save FAISS index + `faiss_metadata.json`

#### FHIR Bundles

```bash
python scripts/build_fhir_index.py \
  --in data/fhir/ \
  --out data/fhir/faiss_index
```

This should:

* Load each `*.json` FHIR bundle
* Chunk & embed narrative + structured text
* Save FAISS index

### 4. Environment Variables

Create a `.env` or export manually:

```bash
export OPENAI_API_KEY=sk-...
export DEFAULT_PATIENT_ID=maria        # or emily
export DRUG_DB_PATH=data/drugs/drugs.db
export DRUGS_FAISS_PATH=data/drugs/faiss_index
export FHIR_FAISS_PATH=data/fhir/faiss_index
```

(Adjust names as your code expects.)

### 5. Run the Test Script

```bash
python testing_first_llm_fhir_RAG.py
```

You should see prompts like:

```
>>> PROMPT: What allergies do I have?
[fhir] ...
```

If you still get placeholders like `[Medication 1]`, see **Troubleshooting**.

---

## Scripts & Entry Points

Update these names to match your repo. Typical structure:

| Script                          | Purpose                               | Example                                                                          |
| ------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------- |
| `scripts/build_drug_db.py`      | Build `drugs.db` from raw files       | `python scripts/build_drug_db.py --raw data/drugs/raw --out data/drugs/drugs.db` |
| `scripts/build_faiss_index.py`  | Create FAISS for drugs                | `--in data/drugs/drugs.db --out data/drugs/faiss_index`                          |
| `scripts/build_fhir_index.py`   | Create FAISS for FHIR bundles         | `--in data/fhir --out data/fhir/faiss_index`                                     |
| `testing_first_llm_fhir_RAG.py` | Simple REPL to query RAG              | `python testing_first_llm_fhir_RAG.py`                                           |
| `src/fhir/getters.py`           | Extractors for specific FHIR sections | Imported by RAG pipeline                                                         |

---

## Troubleshooting

### Placeholders like `[Medication 1]`

Cause: `get_current_medications` only looks at `MedicationStatement.medicationReference`. Your bundles use `medicationCodeableConcept`.

**Fix:** In `src/fhir/getters.py`:

```python
def get_current_medications(resources):
    meds = []
    for r in resources:
        if r.get("resourceType") == "MedicationStatement":
            # Handle both forms
            concept = r.get("medicationCodeableConcept", {})
            name = concept.get("text")
            if not name:
                ref = r.get("medicationReference", {}).get("reference", "")
                # ...existing lookup logic
            status = r.get("status", "")
            if name:
                meds.append(f"{name} (status: {status})")
    return "\n".join(meds) if meds else "No current medications."
```

### `JSONDecodeError` on bundle load

* Check your JSON file has no trailing commas / invalid UTF-8
* Ensure you open the correct path in `fetch_fhir_resources(path)`
* Confirm `Bundle.type` is `transaction` if your loader expects it (or handle `document`).

### Git push blocked (100MB limit)

* Remove big files with `git filter-repo`
* Re‑add remote & force-push (see earlier message)

### FAISS import error

* Install `faiss-cpu` specifically: `pip install faiss-cpu` (on Apple Silicon it’s fine)

### OpenAI quota / key missing

* Ensure `OPENAI_API_KEY` is set
* Wrap embed calls with try/except to log failures

