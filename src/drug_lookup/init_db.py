import sqlite3

conn = sqlite3.connect("data/drugs/drugs.db")
cur = conn.cursor()

# Create medication table
cur.execute("""
CREATE TABLE IF NOT EXISTS medication (
    id TEXT PRIMARY KEY,
    slug_id TEXT,
    fhir_code TEXT,
    name TEXT,
    manufacturer TEXT,
    strength TEXT,
    form TEXT,
    route TEXT,
    last_updated TEXT
);
""")

# Create knowledge table
cur.execute("""
CREATE TABLE IF NOT EXISTS medication_knowledge (
    medication_id TEXT PRIMARY KEY,
    indications TEXT,
    contraindications TEXT,
    side_effects TEXT,
    interactions TEXT,
    warnings TEXT,
    pharmacology TEXT,
    pregnancy_category TEXT,
    source_url TEXT,
    raw_text TEXT,
    fhir_blob TEXT
);
""")

conn.commit()
conn.close()
