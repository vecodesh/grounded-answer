
from pathlib import Path
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR = Path("data")

CLAUSE_FILE = DATA_DIR / "clauses.json"
INDEX_FILE = DATA_DIR / "faiss.index"
META_FILE = DATA_DIR / "metadata.json"

# Load embedding model (384-dimensional vectors)
model = SentenceTransformer("all-MiniLM-L6-v2")


def main():
    clauses = json.loads(CLAUSE_FILE.read_text(encoding="utf-8"))

    texts = [c["text"] for c in clauses]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))

    faiss.write_index(index, str(INDEX_FILE))

    META_FILE.write_text(
        json.dumps(clauses, indent=2),
        encoding="utf-8"
    )

    print(f"Indexed {len(clauses)} clauses")
    print(f"Vector dimension: {dimension}")


if __name__ == "__main__":
    main()