import sqlite3

DB_PATH = "data/drugs/drugs.db"

def get_drug_knowledge(slug_id: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT indications, contraindications, side_effects, interactions, warnings
        FROM medication_knowledge
        JOIN medication ON medication.id = medication_knowledge.medication_id
        WHERE medication.slug_id = ?
    """, (slug_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return "No detailed information found."

    sections = ["Indications", "Contraindications", "Side Effects", "Interactions", "Warnings"]
    return "\n".join([f"{sec}: {val}" for sec, val in zip(sections, row) if val])
