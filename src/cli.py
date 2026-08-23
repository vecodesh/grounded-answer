import sys
from pathlib import Path
from typing import Optional

# pyrefly: ignore [missing-import]
import typer

# Ensure src directory is in sys.path regardless of execution context
SRC_DIR = Path(__file__).resolve().parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Ensure UTF-8 output in the terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = typer.Typer(
    help="Calder County Household Support CLI (Date-Aware Policy Assistant)"
)


@app.command()
def ask(
    question: Optional[str] = typer.Argument(
        None,
        help="The policy question to ask. If omitted, you will be prompted."
    ),
    top_k: int = typer.Option(
        5,
        "--top-k",
        "-k",
        help="Number of clauses to retrieve"
    ),
    claim_date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Claim or determination date (e.g. '2026-02-15', 'February 2026', 'April 2026'). If omitted, extracted from question."
    )
):
    """Ask a policy question to the assistant with date-aware policy resolution."""

    # ---------------------------------------------------------
    # Import modules
    # ---------------------------------------------------------
    from retrieve import retrieve
    from refusal import evaluate_retrieval, refusal_message
    from answer import generate_answer
    from contradiction import detect_contradiction, contradiction_message
    from evidence import validate_evidence
    from temporal import extract_date_from_query, parse_date, is_post_amendment

    # Header
    print("\nCalder County Household Support Assistant\n")

    # Get question
    if not question:
        question = input("Ask your policy question:\n> ")

    # Determine date context
    effective_date = parse_date(claim_date) if claim_date else extract_date_from_query(question)
    if effective_date:
        status_str = "Post-Amendment 2026-01 (effective 1 March 2026)" if is_post_amendment(effective_date) else "Base Manual (effective prior to 1 March 2026)"
        print(f"[Date Context: {effective_date.strftime('%B %Y')} — {status_str}]")

    # ---------------------------------------------------------
    # STEP 1: RETRIEVE
    # ---------------------------------------------------------
    results = retrieve(
        question,
        top_k=top_k,
        claim_date=effective_date
    )

    # ---------------------------------------------------------
    # STEP 2: RETRIEVAL DECISION
    # ---------------------------------------------------------
    decision = evaluate_retrieval(results)

    print("\n" + "=" * 60)

    # ---------------------------------------------------------
    # STEP 3: REFUSE
    # ---------------------------------------------------------
    if decision["decision"] == "refuse":
        print("\nDECISION: REFUSE\n")
        print(refusal_message())
        return

    # ---------------------------------------------------------
    # STEP 4: CONTRADICTION CHECK
    # ---------------------------------------------------------
    contradiction = detect_contradiction(
        results,
        question,
        claim_date=effective_date
    )

    if contradiction["contradiction"]:
        print("\nDECISION: CONTRADICTION\n")
        print(contradiction_message(contradiction["clauses"]))
        return

    # ---------------------------------------------------------
    # STEP 5: EVIDENCE VALIDATION
    # ---------------------------------------------------------
    evidence = validate_evidence(
        question,
        results
    )

    if not evidence["supported"]:
        print("\nDECISION: REFUSE\n")
        print(
            "The policy manual does not contain sufficient "
            "evidence to answer this question."
        )
        print(
            "\nNext step: Refer the case to the "
            "Benefits Policy Supervisor."
        )
        return

    # ---------------------------------------------------------
    # STEP 6: AMBIGUOUS
    # ---------------------------------------------------------
    if decision["decision"] == "ambiguous":
        print("\nDECISION: AMBIGUOUS\n")
        print(decision["reason"])
        print("\nRelevant clauses:")
        for result in results[:3]:
            print(f"{result['clause_id']} (score {result['score']:.3f})")
        return

    # ---------------------------------------------------------
    # STEP 7: GENERATE ANSWER
    # ---------------------------------------------------------
    answer = generate_answer(
        question,
        results
    )

    print("\nANSWER\n")
    print(answer)

    # ---------------------------------------------------------
    # STEP 8: CITATIONS
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("CITATIONS")

    for result in results:
        print(f"{result['clause_id']}  (score {result['score']:.3f})")


@app.command()
def ingest():
    """Extract policy clauses from markdown (base manual + amendments)."""
    from ingest import main as ingest_main
    ingest_main()


@app.command()
def index():
    """Build FAISS index from extracted clauses."""
    from indexer import main as index_main
    index_main()


if __name__ == "__main__":
    app()