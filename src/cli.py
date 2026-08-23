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
    help="Calder County Household Support CLI"
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
):
    """Ask a policy question to the assistant."""

    # ---------------------------------------------------------
    # Import modules
    # ---------------------------------------------------------
    from retrieve import retrieve

    from refusal import (
        evaluate_retrieval,
        refusal_message
    )

    from answer import generate_answer

    from contradiction import (
        detect_contradiction,
        contradiction_message
    )

    from evidence import validate_evidence


    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------
    print("\nCalder County Household Support Assistant\n")


    # ---------------------------------------------------------
    # Get question
    # ---------------------------------------------------------
    if not question:
        question = input(
            "Ask your policy question:\n> "
        )


    # ---------------------------------------------------------
    # STEP 1: RETRIEVE
    # ---------------------------------------------------------
    results = retrieve(
        question,
        top_k=top_k
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
    #
    # This must happen before generating an answer.
    # ---------------------------------------------------------
    contradiction = detect_contradiction(results, question)


    if contradiction["contradiction"]:

        print("\nDECISION: CONTRADICTION\n")

        print(
            contradiction_message(
                contradiction["clauses"]
            )
        )

        return


    # ---------------------------------------------------------
    # STEP 5: EVIDENCE VALIDATION
    #
    # Retrieval similarity alone does not guarantee that
    # the retrieved clauses actually answer the question.
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
    #
    # Only reach this when retrieval itself is ambiguous
    # and there is no contradiction.
    # ---------------------------------------------------------
    if decision["decision"] == "ambiguous":

        print("\nDECISION: AMBIGUOUS\n")

        print(decision["reason"])

        print("\nRelevant clauses:")

        for result in results[:3]:

            print(
                f"{result['clause_id']} "
                f"(score {result['score']:.3f})"
            )

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

        print(
            f"{result['clause_id']}  "
            f"(score {result['score']:.3f})"
        )


@app.command()
def ingest():
    """Extract policy clauses from markdown."""

    from ingest import main as ingest_main

    ingest_main()


@app.command()
def index():
    """Build FAISS index from extracted clauses."""

    from indexer import main as index_main

    index_main()


if __name__ == "__main__":
    app()