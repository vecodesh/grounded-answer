
from typing import List

# Similarity thresholds
ANSWER_THRESHOLD = 0.60
AMBIGUOUS_THRESHOLD = 0.45


def evaluate_retrieval(results: List[dict]):
    """
    Decide whether to answer, refuse, or mark as ambiguous.
    """

    if not results:
        return {
            "decision": "refuse",
            "reason": "No relevant policy clauses were found."
        }

    top_score = results[0]["score"]

    # Strong evidence
    if top_score >= ANSWER_THRESHOLD:
        return {
            "decision": "answer",
            "reason": "Sufficient evidence found."
        }

    # Weak evidence
    if top_score >= AMBIGUOUS_THRESHOLD:
        return {
            "decision": "ambiguous",
            "reason": "The manual may contain relevant information, but the evidence is not strong enough."
        }

    # No evidence
    return {
        "decision": "refuse",
        "reason": "The manual does not clearly answer this question."
    }


def refusal_message():
    return (
        "The policy manual does not clearly answer this question.\n\n"
        "Next step: Refer the case to the Benefits Policy Supervisor."
    )