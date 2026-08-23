# Calder County Policy Assistant: The Grounded Answer

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Evaluation](https://img.shields.io/badge/Evaluation-10%2F10%20(100%25)-brightgreen.svg)](test/evaluate.py)

An AI-powered, policy-grounded question answering assistant built for the **Calder County Household Support Program**. 

The assistant provides verifiable, clause-attributed answers to policy questions, explicitly identifies and surfaces internal contradictions in the manual, and reliably refuses to answer when a topic is absent or ambiguous—directing caseworkers to the appropriate supervisor.

---

## Key Features

1. **Strict Clause-Level Grounding**: Every factual claim is directly tied to an exact policy clause (e.g., `§4.3.2`, `§2.4.1`) with relevance scoring.
2. **Deterministic Visible Refusal**: Recognizes the boundary of policy coverage and refuses out-of-scope queries (e.g., childcare vouchers, transport allowances), providing clear escalation guidance.
3. **Explicit Contradiction Detection**: Automatically catches genuine internal inconsistencies (such as conflicting reporting deadlines in §4.3.2 vs. §9.1.4) and flags them for supervisor review rather than guessing or picking a side silently.
4. **Hybrid Dense + Lexical Retrieval**: Combines semantic embeddings (`all-MiniLM-L6-v2` + FAISS) with lexical concept matching to eliminate false-positive retrieval on apparent policy gaps.
5. **Day Two Modular Design**: Cleanly decoupled modules for ingestion, indexing, retrieval, contradiction detection, refusal evaluation, and answer generation.

---

## System Architecture

```
                    ┌─────────────────────────┐
                    │  User / Caseworker Query│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Hybrid Retrieval Engine│
                    │  (Dense FAISS + Lexical)│
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
                                  │ (Conflicting Deadlines) │
                                  └──────┬───────────┬──────┘
                                Conflict │           │ No Conflict
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
│   ├── policy-manual.md     # Full Calder County Policy Manual (137 clauses)
│   ├── clauses.json         # Extracted clause data with metadata
│   ├── faiss.index          # Dense vector FAISS index (384-d)
│   └── metadata.json        # Fast lookup clause metadata
├── src/
│   ├── answer.py            # LLM prompt construction & answer generation
│   ├── cli.py               # Typer-based CLI interface
│   ├── contradiction.py     # Deterministic inconsistency & conflict detection
│   ├── evidence.py          # Substantive lexical evidence validation
│   ├── indexer.py           # FAISS index builder using SentenceTransformer
│   ├── ingest.py            # Markdown clause parser & normalizer
│   ├── refusal.py           # Threshold-based refusal gating
│   └── retrieve.py          # Hybrid dense-lexical retrieval & reranking
├── test/
│   ├── evaluate.py          # Comprehensive 10-question automated evaluation testbed
│   └── test_questions.json  # 10 probe questions covering answers, refusals & conflicts
├── AI-USAGE.md              # AI model disclosure & methodology report
├── DECISIONS.md             # Policy trade-offs & threshold calibration rationale
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

# Create and activate a virtual environment
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
python -m venv venv
.\venv\Scripts\activate.bat
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
*(Note: Retrieval, contradiction detection, refusal evaluation, and test suite execution run completely offline without an API key. An API key is only required for synthesizing final text in `ask` commands).*

---

## Usage

### Ingesting & Indexing the Policy Manual
The repository includes pre-built indexes in `data/`, but you can rebuild them at any time:

```bash
# Extract clauses from markdown
python src/cli.py ingest

# Build the FAISS vector index
python src/cli.py index
```

### Asking Questions via the CLI

#### Example 1: Direct Grounded Answer
```bash
python src/cli.py ask "How many days do I have to report a change of address?"
```
**Output:**
```text
Calder County Household Support Assistant

============================================================
ANSWER

You must report a change of address within 10 calendar days of the change occurring (or within 10 calendar days of becoming aware of the change, whichever is later)【§4.3.2】.

------------------------------------------------------------
CITATIONS
§4.3.2  (score 1.067)
§9.1.4  (score 0.647)
```

#### Example 2: Out-of-Scope Policy Gap (Refusal)
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

#### Example 3: Internal Inconsistency (Contradiction Alert)
```bash
python src/cli.py ask "How many days do I have to report a change of circumstances?"
```
**Output:**
```text
Calder County Household Support Assistant

============================================================
DECISION: CONTRADICTION

The policy manual contains conflicting provisions (§4.3.2 and §9.1.4). This requires supervisor review.
```

---

## Automated Evaluation & Test Suite

Run the full 10-question evaluation suite covering direct grounded answers, policy coverage gaps (refusals), and internal contradictions:

```bash
python test/evaluate.py
```

### Test Suite Summary

| ID | Question | Type | Expected Clause | Result |
|---|---|---|---|---|
| **Q1** | *How many days do I have to report a change of address?* | Answer | `§4.3.2` | **PASS** |
| **Q2** | *What is the resource limit for eligibility?* | Answer | `§2.4.1` | **PASS** |
| **Q3** | *Can a 17-year-old apply for assistance?* | Answer | `§2.3.1` | **PASS** |
| **Q4** | *How long does the Department have to determine an application?* | Answer | `§8.3.1` | **PASS** |
| **Q5** | *When must requested evidence be supplied?* | Answer | `§8.2.3` | **PASS** |
| **Q6** | *How long can temporary medical absence continue?* | Answer | `§3.2.2` | **PASS** |
| **Q7** | *What is the monthly earnings disregard?* | Answer | `§6.4.1` | **PASS** |
| **Q8** | *Do childcare vouchers increase eligibility?* | Refuse | *None (Policy Gap)* | **PASS** |
| **Q9** | *Can I receive transport allowance under this program?* | Refuse | *None (Policy Gap)* | **PASS** |
| **Q10** | *How many days do I have to report a change of circumstances?* | Contradiction | `§4.3.2 & §9.1.4` | **PASS** |

**Score: 10/10 (100% Accuracy)**

---

## Submission Checklist & Compliance

- [x] **Grounded answers with clause-level citation**: Every substantive claim references the exact manual clause (e.g. `§4.3.2`).
- [x] **Visible refusal path**: Declines to answer unsupported queries and provides an actionable next step ("Refer the case to the Benefits Policy Supervisor").
- [x] **10-question test set**: Fully reproducible test bed in `test/evaluate.py` probing standard, gap, and contradictory questions.
- [x] **Runs from a clean clone**: Fully documented installation, requirements, and execution instructions.
- [x] **Explicit contradiction handling**: Automatically surfaces conflicting provisions (§4.3.2 and §9.1.4).
- [x] **Refusal calibration**: Detailed threshold analysis and reasoning documented in [DECISIONS.md](DECISIONS.md).
- [x] **AI disclosure**: Complete disclosure of development and runtime AI tools in [AI-USAGE.md](AI-USAGE.md).
