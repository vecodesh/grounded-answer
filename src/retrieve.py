from pathlib import Path
import json
import re
import faiss
from sentence_transformers import SentenceTransformer

DATA_DIR = Path("data")

INDEX_FILE = DATA_DIR / "faiss.index"
META_FILE = DATA_DIR / "metadata.json"

model = SentenceTransformer("all-MiniLM-L6-v2")

index = faiss.read_index(str(INDEX_FILE))
metadata = json.loads(META_FILE.read_text(encoding="utf-8"))

STOP_WORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "from",
    "by", "is", "are", "be", "can", "could", "would", "should", "do", "does",
    "did", "what", "when", "where", "how", "why", "who", "which", "under",
    "this", "that", "it", "i", "me", "my", "you", "your", "have", "has", "had",
    "receive", "get", "program", "under", "with", "at", "may"
}

IMPORTANT_CONCEPTS = {
    "earnings", "disregard", "resource", "income", "address",
    "absence", "medical", "application", "evidence", "review",
    "appeal", "sanction", "overpayment"
}


def stem_word(w: str) -> str:
    w = w.lower().strip(".,()\"'?-:;*")
    for suffix in ["ings", "ing", "ed", "ly", "es", "s", "al", "ment", "able", "tion", "ance", "ence"]:
        if len(w) > len(suffix) + 3 and w.endswith(suffix):
            return w[:-len(suffix)]
    return w


def tokenize_words(text: str):
    words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def compute_lexical_overlap(query: str, clause_text: str):
    q_words = tokenize_words(query)
    c_words = tokenize_words(clause_text)

    q_stems = {stem_word(w) for w in q_words}
    c_stems = {stem_word(w) for w in c_words}

    overlap = q_stems & c_stems
    clause_lower = clause_text.lower()
    for qs in q_stems:
        if qs in clause_lower:
            overlap.add(qs)

    return overlap


def retrieve(query: str, top_k: int = 5):
    """
    Retrieve and rerank the top_k most relevant policy clauses.
    """

    query_vector = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # Search a larger candidate pool from FAISS before hybrid reranking
    candidate_k = min(len(metadata), max(top_k * 4, 20))
    scores, indices = index.search(query_vector, candidate_k)

    results = []

    # Build initial candidate results
    for score, idx in zip(scores[0], indices[0]):
        clause = metadata[idx]

        results.append({
            "clause_id": clause["clause_id"],
            "text": clause["text"],
            "score": float(score),
            "raw_score": float(score)
        })

    # ---------------------------------------------------------
    # Hybrid reranking: Semantic similarity + Lexical overlap
    # ---------------------------------------------------------
    important_stems = {stem_word(w) for w in IMPORTANT_CONCEPTS}

    for item in results:
        overlap = compute_lexical_overlap(query, item["text"])
        overlap_important = important_stems & overlap

        bonus = len(overlap) * 0.08 + len(overlap_important) * 0.05
        item["score"] = item["raw_score"] + bonus
        item["final_score"] = item["score"]

    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return results[:top_k]


if __name__ == "__main__":

    question = input("Ask a policy question: ")

    results = retrieve(question)

    print("\nTop Matches\n")

    for r in results:
        print(f"{r['clause_id']}  Score: {r['score']:.3f}")
        print(r["text"])
        print("-" * 50)