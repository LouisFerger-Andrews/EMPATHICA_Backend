import os, json, re, sqlite3, uuid

RAW = 'data/drugs/raw'
DB  = 'data/drugs/drugs.db'

def normalize(x):
    if isinstance(x, list):
        return '; '.join(x)
    return x or ''

def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def process(path):
    with open(path) as f:
        raw = json.load(f)
    med_id = str(uuid.uuid4())
    ofda = raw.get('openfda', {})

    name = normalize(ofda.get('brand_name') or ofda.get('generic_name'))
    manufacturer = normalize(ofda.get('manufacturer_name'))
    slug_id = slugify(f"{name} {manufacturer}")

    drug = {
        'id': med_id,
        'slug_id': slug_id,
        'fhir_code': ofda.get('rxcui', [''])[0] or ofda.get('rxnorm_code', [''])[0],
        'name': name,
        'manufacturer': manufacturer,
        'form': normalize(raw.get('dosage_form')),
        'route': normalize(ofda.get('route')),
        'last_updated': raw.get('effective_time')
    }

    knowledge = {
        'medication_id': med_id,
        'indications': normalize(raw.get('indications_and_usage')),
        'contraindications': normalize(raw.get('contraindications')),
        'side_effects': normalize(raw.get('adverse_reactions')),
        'interactions': normalize(raw.get('drug_interactions')),
        'warnings': normalize(raw.get('warnings_and_cautions')),
        'raw_text': json.dumps(raw),
        'fhir_blob': None
    }

    return drug, knowledge

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medication (
        id TEXT PRIMARY KEY,
        slug_id TEXT UNIQUE,
        fhir_code TEXT,
        name TEXT,
        manufacturer TEXT,
        form TEXT,
        route TEXT,
        last_updated TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS medication_knowledge (
        medication_id TEXT PRIMARY KEY,
        indications TEXT,
        contraindications TEXT,
        side_effects TEXT,
        interactions TEXT,
        warnings TEXT,
        raw_text TEXT,
        fhir_blob TEXT
    )""")

    for fname in os.listdir(RAW):
        if fname.endswith(".json"):
            drug, know = process(os.path.join(RAW, fname))
            cur.execute("""INSERT OR IGNORE INTO medication VALUES (:id, :slug_id, :fhir_code, :name, :manufacturer, :form, :route, :last_updated)""", drug)
            cur.execute("""INSERT OR IGNORE INTO medication_knowledge VALUES (:medication_id, :indications, :contraindications, :side_effects, :interactions, :warnings, :raw_text, :fhir_blob)""", know)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
