# Calder County Policy Assistant: The Grounded Answer

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Evaluation](https://img.shields.io/badge/Evaluation-12%2F12%20(100%25)-brightgreen.svg)](test/evaluate.py)

An AI-powered, policy-grounded question answering assistant built for the **Calder County Household Support Program**. 

The assistant provides verifiable, clause-attributed answers to policy questions, explicitly identifies and surfaces internal contradictions in the manual, accurately reasons over **claim dates and policy amendments** (including **Amendment No. 2026-01** effective 1 March 2026), and reliably refuses to answer when a topic is absent or ambiguous—directing caseworkers to the appropriate supervisor.

---

## Key Features

1. **Strict Clause-Level Grounding**: Every factual claim is directly tied to an exact policy clause (e.g., `§4.3.2`, `§2.4.1`, or `§6.4.1 (as amended by Amdt 2026-01 ¶1.1)`) with relevance scoring.
2. **Temporal & Amendment-Aware Reasoning (Day 2)**: Answers correctly for the specific **claim date or determination date** (e.g. February 2026 claims receive pre-amendment answers; April 2026 claims receive post-amendment answers).
3. **Deterministic Visible Refusal**: Recognizes the boundary of policy coverage and refuses out-of-scope queries (e.g., childcare vouchers, transport allowances), providing clear escalation guidance.
4. **Explicit Contradiction Detection & Harmonization**: 
   - For **pre-March 2026** claims: Catches genuine internal inconsistencies (conflicting reporting deadlines in §4.3.2 vs. §9.1.4) and flags them for supervisor review.
   - For **post-March 2026** claims: Recognizes that Amendment No. 2026-01 aligned both provisions to **14 calendar days**, returning the unified grounded answer.
5. **Hybrid Dense + Lexical Retrieval**: Combines semantic embeddings (`all-MiniLM-L6-v2` + FAISS) with lexical concept matching to eliminate false-positive retrieval on apparent policy gaps.
6. **Day Two Modular Design**: Cleanly decoupled modules for ingestion, indexing, retrieval, temporal scoring, contradiction detection, refusal evaluation, and answer generation.

---

## System Architecture

```
                    ┌─────────────────────────┐
                    │ User / Caseworker Query │
                    │ + Optional Claim Date   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Temporal Hybrid Search  │
                    │  (Dense FAISS + Lexical │
                    │   + Date Adjustment)    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Refusal Evaluator    │
                    │   (Score Thresholds)    │
                    └──────┬───────────┬──────┘
             Score < 0.45  │           │  Score >= 0.45
                           ▼           ▼
                      [ REFUSE ]  ┌─────────────────────────┐
                                  │ Contradiction Detector  │
                                  │ (Date-Aware Alignment)  │
                                  └──────┬───────────┬──────┘
                                Conflict │           │ Resolved / No Conflict
                                Detected ▼           ▼
                       [ CONTRADICTION ]  ┌─────────────────────────┐
                       (Supervisor Alert) │   Evidence Validator    │
                                          │ (Substantive Match)     │
                                          └──────┬───────────┬──────┘
                                       Supported │           │ Unsupported
                                                 ▼           ▼
                                            [ ANSWER ]   [ REFUSE ]
                                          (Grounded LLM) (Supervisor Referral)
```

---

## Directory Structure

```
grounded-answer/
├── data/
│   ├── policy-manual.md     # Base Calder County Policy Manual (137 clauses)
│   ├── amendment-2026-01.md # Amendment No. 2026-01 (effective 1 March 2026)
│   ├── clauses.json         # Extracted clause data with temporal metadata
│   ├── faiss.index          # Dense vector FAISS index (384-d)
│   └── metadata.json        # Fast lookup clause metadata
├── src/
│   ├── answer.py            # LLM prompt construction & answer generation
│   ├── cli.py               # Typer-based date-aware CLI interface
│   ├── contradiction.py     # Deterministic inconsistency & conflict detection
│   ├── evidence.py          # Substantive lexical evidence validation
│   ├── indexer.py           # FAISS index builder using SentenceTransformer
│   ├── ingest.py            # Markdown clause parser & temporal metadata normalizer
│   ├── refusal.py           # Threshold-based refusal gating
│   ├── retrieve.py          # Hybrid dense-lexical retrieval & temporal reranking
│   └── temporal.py          # Date extraction, parsing & temporal validity engine
├── test/
│   ├── evaluate.py          # Automated 12-question evaluation testbed
│   └── test_questions.json  # 12 probe questions covering answers, dates, refusals & conflicts
├── AI-USAGE.md              # AI model disclosure & methodology report
├── DECISIONS.md             # Policy trade-offs, calibration & Day 2 post-mortem
├── README.md                # Project documentation & execution guide
└── requirements.txt         # Project dependencies
```

---

## Quickstart: Running from a Clean Clone

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/vecodesh/grounded-answer.git
cd grounded-answer

# Create and activate a virtual environment:

# Option A: On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Option B: On Windows (PowerShell)
python -m venv venv
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .\venv\Scripts\Activate.ps1)

# Option C: On Windows (Command Prompt / CMD)
python -m venv venv
venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory (or copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:
```ini
GROQ_API_KEY=your_groq_api_key_here
```
*(Note: Retrieval, temporal routing, contradiction detection, refusal evaluation, and the full test suite run completely offline without an API key. An API key is only required for synthesizing final natural language text in `ask` commands).*

---

## Usage

### Ingesting & Indexing the Policy Manual
The repository includes pre-built indexes in `data/`, but you can rebuild them at any time:

```bash
# Extract clauses from base manual and Amendment No. 2026-01
python src/cli.py ingest

# Build the FAISS vector index
python src/cli.py index
```

### Asking Questions via the CLI

#### Example 1: Pre-Amendment Question (February 2026 Claim)
```bash
python src/cli.py ask "What is the monthly earnings disregard for a claim in February 2026?"
```
**Output:**
```text
Calder County Household Support Assistant

[Date Context: February 2026 — Base Manual (effective prior to 1 March 2026)]

============================================================
ANSWER

The monthly earnings disregard is $120 per month under §6.4.1(a).

------------------------------------------------------------
CITATIONS
§6.4.1  (score 0.812)
```

#### Example 2: Post-Amendment Question (April 2026 Claim)
```bash
python src/cli.py ask "What is the monthly earnings disregard for a claim in April 2026?"
```
**Output:**
```text
Calder County Household Support Assistant

[Date Context: April 2026 — Post-Amendment 2026-01 (effective 1 March 2026)]

============================================================
ANSWER

The monthly earnings disregard for a claim made in April 2026 is $175 per month【§6.4.1 (as amended by Amdt 2026-01 ¶1.1)】. This amount applies to all determinations on or after 1 March 2026.

------------------------------------------------------------
CITATIONS
§6.4.1 (as amended by Amdt 2026-01 ¶1.1)  (score 1.326)
```

#### Example 3: Pre-Amendment Contradiction Alert
```bash
python src/cli.py ask "How many days do I have to report a change of circumstances occurring in February 2026?"
```
**Output:**
```text
Calder County Household Support Assistant

[Date Context: February 2026 — Base Manual (effective prior to 1 March 2026)]

============================================================
DECISION: CONTRADICTION

The policy manual contains conflicting provisions (§4.3.2 and §9.1.4). This requires supervisor review.
```

#### Example 4: Post-Amendment Harmonized Answer
```bash
python src/cli.py ask "How many days do I have to report a change of circumstances occurring in April 2026?"
```
**Output:**
```text
Calder County Household Support Assistant

[Date Context: April 2026 — Post-Amendment 2026-01 (effective 1 March 2026)]

============================================================
ANSWER

You must report the change within 14 calendar days of the change occurring (or of becoming aware of it, whichever is later)【§4.3.2 (as amended by Amdt 2026-01 ¶2.1)】.

------------------------------------------------------------
CITATIONS
§4.3.2 (as amended by Amdt 2026-01 ¶2.1)  (score 1.549)
§9.1.4 (as amended by Amdt 2026-01 ¶2.2)  (score 1.469)
```

#### Example 5: Policy Gap (Refusal)
```bash
python src/cli.py ask "Do childcare vouchers increase eligibility?"
```
**Output:**
```text
Calder County Household Support Assistant

============================================================
DECISION: REFUSE

The policy manual does not contain sufficient evidence to answer this question.

Next step: Refer the case to the Benefits Policy Supervisor.
```

---

## Automated Evaluation & Test Suite

Run the full 12-question evaluation suite covering direct grounded answers, policy coverage gaps (refusals), temporal date queries, and pre/post amendment contradictions:

```bash
python test/evaluate.py
```

### Test Suite Summary

| ID | Question | Expected Type | Expected Clause | Result |
|---|---|---|---|---|
| **Q1** | *How many days do I have to report a change of address?* | Answer | `§4.3.2` | **PASS** |
| **Q2** | *What is the resource limit for eligibility?* | Answer | `§2.4.1` | **PASS** |
| **Q3** | *Can a 17-year-old apply for assistance?* | Answer | `§2.3.1` | **PASS** |
| **Q4** | *How long does the Department have to determine an application?* | Answer | `§8.3.1` | **PASS** |
| **Q5** | *When must requested evidence be supplied?* | Answer | `§8.2.3` | **PASS** |
| **Q6** | *How long can temporary medical absence continue?* | Answer | `§3.2.2` | **PASS** |
| **Q7** | *What is the monthly earnings disregard for a claim in February 2026?* | Answer | `§6.4.1` | **PASS** |
| **Q8** | *What is the monthly earnings disregard for a claim in April 2026?* | Answer | `§6.4.1 (Amdt 2026-01 ¶1.1)` | **PASS** |
| **Q9** | *Do childcare vouchers increase eligibility?* | Refuse | *None (Policy Gap)* | **PASS** |
| **Q10** | *Can I receive transport allowance under this program?* | Refuse | *None (Policy Gap)* | **PASS** |
| **Q11** | *How many days do I have to report a change in February 2026?* | Contradiction | `§4.3.2 & §9.1.4` | **PASS** |
| **Q12** | *How many days do I have to report a change in April 2026?* | Answer | `§4.3.2 (Amdt 2026-01 ¶2.1)` | **PASS** |

**Score: 12/12 (100% Accuracy)**

---

## Submission Checklist & Compliance

- [x] **Grounded answers with clause-level citation**: Every substantive claim references the exact manual/amendment clause (e.g. `§4.3.2`, `§6.4.1 (Amdt 2026-01 ¶1.1)`).
- [x] **Temporal Date-Awareness (Day 2)**: Dynamic routing based on claim/determination date (pre-March 2026 vs post-March 2026).
- [x] **Visible refusal path**: Declines to answer unsupported queries and provides an actionable next step ("Refer the case to the Benefits Policy Supervisor").
- [x] **12-question test set**: Fully reproducible test bed in `test/evaluate.py` probing standard, gap, temporal, and contradictory questions with 100% pass rate.
- [x] **Runs from a clean clone**: Fully documented installation, requirements, and execution instructions.
- [x] **Explicit contradiction handling**: Automatically surfaces conflicting provisions for pre-March 2026 claims and applies harmonized rules for post-March 2026 claims.
- [x] **Refusal calibration**: Detailed threshold analysis and reasoning documented in [DECISIONS.md](DECISIONS.md).
- [x] **AI disclosure**: Complete disclosure of development and runtime AI tools in [AI-USAGE.md](AI-USAGE.md).
