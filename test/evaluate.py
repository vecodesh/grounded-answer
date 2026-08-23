import json
import sys
from pathlib import Path

# Allow importing modules from src/
SRC_DIR = Path(__file__).resolve().parents[1] / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# pyrefly: ignore [missing-import]
from retrieve import retrieve
# pyrefly: ignore [missing-import]
from refusal import evaluate_retrieval
# pyrefly: ignore [missing-import]
from contradiction import detect_contradiction
# pyrefly: ignore [missing-import]
from evidence import validate_evidence
# pyrefly: ignore [missing-import]
from temporal import extract_date_from_query

TEST_FILE = Path(__file__).resolve().parent / "test_questions.json"


def main():
    """
    Run the complete evaluation pipeline across 12 probe questions.

    Pipeline:
        Question (with temporal context)
            ↓
        Date Extraction
            ↓
        Temporal Hybrid Retrieval
            ↓
        Refusal Evaluation
            ↓
        Contradiction Detection (Date-aware)
            ↓
        Evidence Validation
            ↓
        Compare with Expected Result
    """

    tests = json.loads(TEST_FILE.read_text(encoding="utf-8"))

    passed = 0

    print("=" * 70)
    print("GROUNDED ANSWER - EVALUATION (DAY 2: TEMPORAL & AMENDMENT 2026-01)")
    print("=" * 70)

    for test in tests:
        question = test["question"]
        expected_type = test["expected_type"]
        expected_clause = test.get("expected_clause")

        target_date = extract_date_from_query(question)

        # ---------------------------------------------------------
        # STEP 1: RETRIEVE
        # ---------------------------------------------------------
        results = retrieve(question, top_k=5, claim_date=target_date)

        top_clause = results[0]["clause_id"] if results else None

        # ---------------------------------------------------------
        # STEP 2: INITIAL DECISION
        # ---------------------------------------------------------
        decision = evaluate_retrieval(results)
        actual_type = decision["decision"]

        # ---------------------------------------------------------
        # STEP 3: CONTRADICTION DETECTION
        # ---------------------------------------------------------
        contradiction = detect_contradiction(results, question, claim_date=target_date)

        if contradiction["contradiction"]:
            actual_type = "contradiction"
            contradiction_clauses = contradiction["clauses"]
        else:
            contradiction_clauses = []

        # ---------------------------------------------------------
        # STEP 4: EVIDENCE VALIDATION
        # Match the behaviour of cli.py
        # ---------------------------------------------------------
        evidence = validate_evidence(question, results)

        if actual_type in {"answer", "ambiguous"} and not evidence["supported"]:
            actual_type = "refuse"

        # ---------------------------------------------------------
        # STEP 5: EVALUATE RESULT
        # ---------------------------------------------------------
        ok = False

        if expected_type == "answer":
            if expected_clause:
                # Matches exact or prefix
                ok = (
                    actual_type == "answer"
                    and (
                        top_clause == expected_clause
                        or top_clause.startswith(expected_clause)
                        or expected_clause in top_clause
                    )
                )
            else:
                ok = actual_type == "answer"

        elif expected_type == "refuse":
            ok = actual_type == "refuse"

        elif expected_type == "ambiguous":
            retrieved = [r["clause_id"] for r in results]
            ok = (
                "§4.3.2" in retrieved
                and "§9.1.4" in retrieved
                and actual_type in {"ambiguous", "contradiction"}
            )

        elif expected_type == "contradiction":
            if expected_clause:
                expected = [
                    c.strip()
                    for c in expected_clause.split("&")
                ]

                ok = (
                    actual_type == "contradiction"
                    and all(
                        c in contradiction_clauses
                        for c in expected
                    )
                )
            else:
                ok = actual_type == "contradiction"

        # ---------------------------------------------------------
        # DISPLAY
        # ---------------------------------------------------------
        if ok:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"\nQ{test['id']}: {status}")
        print(f"Question     : {question}")
        print(f"Expected     : {expected_type} ({expected_clause or 'N/A'})")
        print(f"Actual       : {actual_type} ({top_clause or 'N/A'})")

        if contradiction_clauses:
            print(
                "Contradiction: "
                + " & ".join(contradiction_clauses)
            )

    # -------------------------------------------------------------
    # FINAL SCORE
    # -------------------------------------------------------------
    total = len(tests)
    accuracy = (passed / total) * 100 if total else 0

    print("\n" + "=" * 70)
    print(f"FINAL SCORE : {passed}/{total}")
    print(f"ACCURACY    : {accuracy:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()