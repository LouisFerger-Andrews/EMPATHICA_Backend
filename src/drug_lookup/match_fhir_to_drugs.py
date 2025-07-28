import sqlite3
from typing import Optional

DB_PATH = "data/drugs/drugs.db"

def find_drug_by_rxnorm(rx_code: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM medication WHERE fhir_code = ?", (rx_code,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "slug_id": row[1],
            "name": row[3],
            "manufacturer": row[4],
            "strength": row[5],
            "form": row[6],
            "route": row[7],
        }
    return None

def find_drug_by_name(name: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM medication WHERE LOWER(name) LIKE ?", (f"%{name.lower()}%",))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "slug_id": row[1],
            "name": row[3],
            "manufacturer": row[4],
            "strength": row[5],
            "form": row[6],
            "route": row[7],
        }
    return None

def match_fhir_medication(med_fhir_entry: dict) -> Optional[dict]:
    code_info = med_fhir_entry.get("code", {}).get("coding", [{}])[0]
    rx_code = code_info.get("code")
    name    = code_info.get("display")

    if rx_code:
        result = find_drug_by_rxnorm(rx_code)
        if result:
            return result

    if name:
        return find_drug_by_name(name)

    return None
