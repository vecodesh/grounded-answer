import re
import json
from pathlib import Path

# Paths
DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "policy-manual.md"
AMENDMENT_FILE = DATA_DIR / "amendment-2026-01.md"
OUTPUT_FILE = DATA_DIR / "clauses.json"

AMENDED_BASE_CLAUSES = {
    "§6.4.1": "2026-02-28",
    "§4.3.2": "2026-02-28",
    "§9.1.4": "2026-02-28",
    "§6.6.1": "2026-02-28",
    "§10.5.2": "2026-02-28",
}


def parse_markdown():
    """
    Extracts every numbered clause from the base policy manual.
    Example:
        **4.3.2** A recipient must report...
    """
    if not INPUT_FILE.exists():
        return []

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
                c_id = f"§{current_clause}"
                eff_end = AMENDED_BASE_CLAUSES.get(c_id, None)
                clauses.append({
                    "clause_id": c_id,
                    "part": current_part,
                    "section": current_section,
                    "text": " ".join(current_text).strip(),
                    "source": "manual",
                    "effective_start": "2025-12-31",
                    "effective_end": eff_end
                })

            current_clause = clause_match.group(1)
            current_text = [clause_match.group(2)]
            continue

        # Continue clause text
        if current_clause and line:
            current_text.append(line)

    # Save last clause
    if current_clause:
        c_id = f"§{current_clause}"
        eff_end = AMENDED_BASE_CLAUSES.get(c_id, None)
        clauses.append({
            "clause_id": c_id,
            "part": current_part,
            "section": current_section,
            "text": " ".join(current_text).strip(),
            "source": "manual",
            "effective_start": "2025-12-31",
            "effective_end": eff_end
        })

    return clauses


def parse_amendment_2026_01():
    """
    Extracts amended provisions from Amendment No. 2026-01.
    """
    if not AMENDMENT_FILE.exists():
        return []

    return [
        {
            "clause_id": "§6.4.1 (as amended by Amdt 2026-01 ¶1.1)",
            "base_clause_id": "§6.4.1",
            "part": "6",
            "section": "6.4",
            "text": "Under Amendment No. 2026-01 ¶1.1 (effective 1 March 2026), in §6.4.1(a) for '$120 per month' substitute '$175 per month'. The monthly earnings disregard is $175 per month for determinations made on or after 1 March 2026.",
            "source": "amendment-2026-01",
            "effective_start": "2026-03-01",
            "effective_end": None,
            "transitional_rule": "determination_date"
        },
        {
            "clause_id": "§4.3.2 (as amended by Amdt 2026-01 ¶2.1)",
            "base_clause_id": "§4.3.2",
            "part": "4",
            "section": "4.3",
            "text": "Under Amendment No. 2026-01 ¶2.1 (effective 1 March 2026), in §4.3.2 for '10 calendar days' substitute '14 calendar days'. A recipient must report a change of address or change of circumstances within 14 calendar days of the change occurring (or within 14 calendar days of becoming aware of the change, whichever is later) for changes occurring on or after 1 March 2026.",
            "source": "amendment-2026-01",
            "effective_start": "2026-03-01",
            "effective_end": None,
            "transitional_rule": "event_date"
        },
        {
            "clause_id": "§9.1.4 (as amended by Amdt 2026-01 ¶2.2)",
            "base_clause_id": "§9.1.4",
            "part": "9",
            "section": "9.1",
            "text": "Under Amendment No. 2026-01 ¶2.2 (effective 1 March 2026), in §9.1.4 for '30 calendar days' substitute '14 calendar days'. A recipient must notify the Department of any change of circumstances within 14 calendar days for changes occurring on or after 1 March 2026.",
            "source": "amendment-2026-01",
            "effective_start": "2026-03-01",
            "effective_end": None,
            "transitional_rule": "event_date"
        },
        {
            "clause_id": "§6.6.1 (as amended by Amdt 2026-01 ¶3.1)",
            "base_clause_id": "§6.6.1",
            "part": "6",
            "section": "6.6",
            "text": "Under Amendment No. 2026-01 ¶3.1 (effective 1 March 2026), in the table at §6.6.1, the monthly income thresholds are: Household size 1: $1,225; size 2: $1,650; size 3: $2,075; size 4: $2,500; size 5: $2,925; each additional member: + $425. Applies to determinations made on or after 1 March 2026.",
            "source": "amendment-2026-01",
            "effective_start": "2026-03-01",
            "effective_end": None,
            "transitional_rule": "determination_date"
        },
        {
            "clause_id": "§10.5.2 (as amended by Amdt 2026-01 ¶4.1)",
            "base_clause_id": "§10.5.2",
            "part": "10",
            "section": "10.5",
            "text": "Under Amendment No. 2026-01 ¶4.1 (effective 1 March 2026), in §10.5.2 for '20 per cent' substitute '15 per cent'. The reduction in monthly award as a sanction for failure to report is 15 per cent for determinations made on or after 1 March 2026.",
            "source": "amendment-2026-01",
            "effective_start": "2026-03-01",
            "effective_end": None,
            "transitional_rule": "determination_date"
        },
        {
            "clause_id": "§10.5.3A (inserted by Amdt 2026-01 ¶4.2)",
            "base_clause_id": "§10.5.3A",
            "part": "10",
            "section": "10.5",
            "text": "Under Amendment No. 2026-01 ¶4.2 (effective 1 March 2026), after §10.5.3 insert §10.5.3A: A sanction must not be imposed in respect of a failure to report where the change of circumstances in question would have increased the award. Applies on or after 1 March 2026.",
            "source": "amendment-2026-01",
            "effective_start": "2026-03-01",
            "effective_end": None,
            "transitional_rule": "determination_date"
        },
        {
            "clause_id": "Amendment 2026-01 ¶5 (Transitional Provisions)",
            "base_clause_id": "¶5",
            "part": "Transitional",
            "section": "5",
            "text": "Transitional general rules under Amendment No. 2026-01 ¶5: Amendments to paragraphs 1, 3 and 4 apply to determinations made on or after 1 March 2026. Paragraph 2 applies to changes of circumstances occurring on or after 1 March 2026.",
            "source": "amendment-2026-01",
            "effective_start": "2026-03-01",
            "effective_end": None,
            "transitional_rule": "transitional"
        }
    ]


def main():
    base_clauses = parse_markdown()
    amendment_clauses = parse_amendment_2026_01()

    all_clauses = base_clauses + amendment_clauses

    OUTPUT_FILE.write_text(
        json.dumps(all_clauses, indent=2),
        encoding="utf-8"
    )

    print(f"Extracted {len(base_clauses)} base clauses + {len(amendment_clauses)} amendment clauses = {len(all_clauses)} total")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()