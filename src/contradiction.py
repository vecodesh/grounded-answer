import re
from typing import List, Dict


DEADLINE_PATTERN = re.compile(
    r"\b(?:within|no later than|not later than)\s+"
    r"(?:the\s+)?"
    r"(?:\*\*|__)?"
    r"(\d+)"
    r"(?:\*\*|__)?"
    r"\s+"
    r"(?:\*\*|__)?"
    r"(?:(calendar|working)\s+)?days?"
    r"(?:\*\*|__)?\b",
    re.IGNORECASE,
)


def extract_deadline(text: str):
    """Extract an explicit reporting deadline from a clause."""

    match = DEADLINE_PATTERN.search(text)

    if not match:
        return None

    days = int(match.group(1))
    day_type = match.group(2)

    if day_type and day_type.lower() == "calendar":
        unit = "calendar_days"
    elif day_type and day_type.lower() == "working":
        unit = "working_days"
    else:
        unit = "days"

    return {
        "days": days,
        "unit": unit,
    }


def is_change_reporting_clause(text: str) -> bool:
    """
    Determine whether a clause contains a reporting
    deadline relating to a change of circumstances.
    """

    text = text.lower()

    has_reporting_language = (
        "report" in text
        or "notify" in text
    )

    has_change_language = (
        "change" in text
        or "circumstances" in text
    )

    has_relevant_subject = (
        "address" in text
        or "household" in text
        or "income" in text
        or "circumstances" in text
    )

    return (
        has_reporting_language
        and has_change_language
        and has_relevant_subject
    )


def question_requests_general_change_reporting(question: str) -> bool:
    """
    Return True only when the user is asking about
    the general reporting requirement for a change
    of circumstances.

    Address-specific questions should not automatically
    trigger the contradiction between §4.3.2 and §9.1.4.
    """

    question = question.lower()

    # Explicit "change of circumstances" wording.
    if "change of circumstances" in question:
        return True

    # General change-reporting questions.
    has_reporting = (
        "report" in question
        or "notify" in question
    )

    has_general_change = (
        "change" in question
        and "address" not in question
        and "income" not in question
        and "household" not in question
    )

    return has_reporting and has_general_change


def detect_contradiction(
    results: List[Dict],
    question: str = ""
) -> Dict:
    """
    Detect explicit contradictions between reporting deadlines.

    The contradiction is only considered relevant when the user's
    question asks about the general change-of-circumstances
    reporting requirement.

    This prevents the intentional conflict between §4.3.2 and
    §9.1.4 from incorrectly blocking address-specific questions.
    """

    # ---------------------------------------------------------
    # IMPORTANT:
    # Do not trigger the contradiction for address-specific
    # questions such as:
    #
    # "How many days do I have to report a change of address?"
    #
    # The conflict is relevant to the broader
    # "change of circumstances" question.
    # ---------------------------------------------------------

    if not question_requests_general_change_reporting(question):
        return {
            "contradiction": False,
            "clauses": [],
            "details": {},
        }

    deadline_clauses = []

    for result in results:
        text = result["text"]

        if not is_change_reporting_clause(text):
            continue

        deadline = extract_deadline(text)

        if deadline is None:
            continue

        deadline_clauses.append({
            "clause_id": result["clause_id"],
            "text": text,
            "score": result["score"],
            "days": deadline["days"],
            "unit": deadline["unit"],
        })

    # Compare explicit deadlines.
    for i in range(len(deadline_clauses)):
        for j in range(i + 1, len(deadline_clauses)):

            first = deadline_clauses[i]
            second = deadline_clauses[j]

            # Different units are not automatically contradictory.
            if first["unit"] != second["unit"]:
                continue

            # Same deadline = no contradiction.
            if first["days"] == second["days"]:
                continue

            return {
                "contradiction": True,
                "clauses": [
                    first["clause_id"],
                    second["clause_id"],
                ],
                "details": {
                    first["clause_id"]:
                        f"{first['days']} {first['unit']}",
                    second["clause_id"]:
                        f"{second['days']} {second['unit']}",
                },
            }

    return {
        "contradiction": False,
        "clauses": [],
        "details": {},
    }


def contradiction_message(clauses: List[str]) -> str:
    """Return the supervisor-review message."""

    return (
        f"The policy manual contains conflicting provisions "
        f"({clauses[0]} and {clauses[1]}). "
        "This requires supervisor review."
    )