import sqlite3, faiss, json
from sentence_transformers import SentenceTransformer

DB = 'data/drugs/drugs.db'
INDEX = 'data/drugs/faiss_index.bin'
META = 'data/drugs/faiss_metadata.json'

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT m.name, k.side_effects, k.interactions, k.warnings
        FROM medication m JOIN medication_knowledge k ON m.id = k.medication_id
    """)
    rows = cur.fetchall()
    conn.close()

    texts, metadata = [], []
    for name, side, inter, warn in rows:
        for section, text in [('side_effects', side), ('interactions', inter), ('warnings', warn)]:
            if text:
                texts.append(text)
                metadata.append({'drug': name, 'section': section})

    model = SentenceTransformer('all-MiniLM-L6-v2')
    embs = model.encode(texts, show_progress_bar=True)
    faiss.normalize_L2(embs)

    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(embs)

    faiss.write_index(index, INDEX)
    with open(META, 'w') as f:
        json.dump({'texts': texts, 'metadata': metadata}, f)

    print(f"✓ Built FAISS index with {len(texts)} entries.")

if __name__ == "__main__":
    main()
