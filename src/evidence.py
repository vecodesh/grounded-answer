import re
from typing import List, Dict

STOP_WORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "from",
    "by", "is", "are", "be", "can", "could", "would", "should", "do", "does",
    "did", "what", "when", "where", "how", "why", "who", "which", "under",
    "this", "that", "it", "i", "me", "my", "you", "your", "have", "has", "had",
    "receive", "get", "program", "under", "with", "at", "may"
}

GENERIC_TERMS = {
    "eligibility", "eligible", "assistance", "allowance", "allowances",
    "benefit", "benefits", "increase", "increases", "receive", "apply",
    "household", "person"
}


def stem_word(w: str) -> str:
    w = w.lower().strip(".,()\"'?-:;*")
    for suffix in ["ings", "ing", "ed", "ly", "es", "s", "al", "ment", "able", "tion", "ance", "ence"]:
        if len(w) > len(suffix) + 3 and w.endswith(suffix):
            return w[:-len(suffix)]
    return w


def tokenize(text: str) -> set:
    words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    return {
        w for w in words
        if w not in STOP_WORDS and len(w) > 2
    }


def check_evidence(question: str, result: Dict) -> Dict:
    q_words = tokenize(question)
    q_stems = {stem_word(w) for w in q_words}

    generic_stems = {stem_word(w) for w in GENERIC_TERMS}
    specific_stems = q_stems - generic_stems

    c_words = tokenize(result["text"])
    c_stems = {stem_word(w) for w in c_words}

    clause_lower = result["text"].lower()

    overlap = set()
    for qs in q_stems:
        if qs in c_stems or qs in clause_lower:
            overlap.add(qs)

    # Require at least one substantive/specific concept to match if specific terms exist
    if specific_stems:
        specific_matches = {s for s in specific_stems if s in c_stems or s in clause_lower}
        if not specific_matches:
            return {"supported": False, "score": 0, "overlap": sorted(overlap)}

    if not overlap:
        return {"supported": False, "score": 0, "overlap": []}

    score = len(overlap)

    return {
        "supported": True,
        "score": score,
        "overlap": sorted(overlap)
    }


def validate_evidence(question: str, results: List[Dict]):

    if not results:
        return {
            "supported": False,
            "clause_id": None,
            "overlap": []
        }

    best = None

    for result in results:

        ev = check_evidence(question, result)

        if not ev["supported"]:
            continue

        if best is None or ev["score"] > best["score"]:
            best = {
                "supported": True,
                "clause_id": result["clause_id"],
                "overlap": ev["overlap"],
                "score": ev["score"]
            }

    if best:
        return best

    return {
        "supported": False,
        "clause_id": None,
        "overlap": []
    }