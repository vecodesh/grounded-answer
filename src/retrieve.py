
from pathlib import Path
import json
import faiss
from sentence_transformers import SentenceTransformer

DATA_DIR = Path("data")

INDEX_FILE = DATA_DIR / "faiss.index"
META_FILE = DATA_DIR / "metadata.json"

# Same model used during indexing
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load index and metadata once
index = faiss.read_index(str(INDEX_FILE))
metadata = json.loads(META_FILE.read_text(encoding="utf-8"))


def retrieve(query: str, top_k: int = 5):
    """
    Returns the top_k most relevant clauses.
    """

    query_vector = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores, indices = index.search(query_vector, top_k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        clause = metadata[idx]

        results.append({
            "clause_id": clause["clause_id"],
            "text": clause["text"],
            "score": float(score)
        })

    return results


if __name__ == "__main__":

    question = input("Ask a policy question: ")

    results = retrieve(question)

    print("\nTop Matches\n")

    for r in results:
        print(f"{r['clause_id']}  Score: {r['score']:.3f}")
        print(r["text"])
        print("-" * 50)