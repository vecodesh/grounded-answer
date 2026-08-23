
import re
import json
from pathlib import Path

# Paths
DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "policy-manual.md"
OUTPUT_FILE = DATA_DIR / "clauses.json"


def parse_markdown():
    """
    Extracts every numbered clause from the policy manual.
    Example:
        **4.3.2** A recipient must report...
    """

    text = INPUT_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()

    clauses = []

    current_part = ""
    current_section = ""
    current_clause = None
    current_text = []

    part_pattern = re.compile(r"^# Part (\d+)")
    section_pattern = re.compile(r"^## (\d+\.\d+)")
    clause_pattern = re.compile(r"^\*\*(\d+\.\d+\.\d+)\*\*\s*(.*)")

    for line in lines:

        line = line.strip()

        # Detect Part
        part_match = part_pattern.match(line)
        if part_match:
            current_part = part_match.group(1)
            continue

        # Detect Section
        section_match = section_pattern.match(line)
        if section_match:
            current_section = section_match.group(1)
            continue

        # Detect New Clause
        clause_match = clause_pattern.match(line)
        if clause_match:

            # Save previous clause
            if current_clause:
                clauses.append({
                    "clause_id": f"§{current_clause}",
                    "part": current_part,
                    "section": current_section,
                    "text": " ".join(current_text).strip()
                })

            current_clause = clause_match.group(1)
            current_text = [clause_match.group(2)]
            continue

        # Continue clause text
        if current_clause and line:
            current_text.append(line)

    # Save last clause
    if current_clause:
        clauses.append({
            "clause_id": f"§{current_clause}",
            "part": current_part,
            "section": current_section,
            "text": " ".join(current_text).strip()
        })

    return clauses


def main():
    clauses = parse_markdown()

    OUTPUT_FILE.write_text(
        json.dumps(clauses, indent=2),
        encoding="utf-8"
    )

    print(f"Extracted {len(clauses)} clauses")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()