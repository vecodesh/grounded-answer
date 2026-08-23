# Design & Policy Decisions: The Grounded Answer

## 1. Executive Summary & Core Objective

The primary challenge of **Problem 1 (The Grounded Answer)** is not whether an LLM can generate fluent answers from a text corpus, but whether an automated assistant can **reliably recognize the boundaries of its knowledge**. 

In public benefit administration (such as the Calder County Household Support Program), the human cost of a false positive (a confident, plausible, yet incorrect answer) is catastrophic: a vulnerable family may be told they are eligible for an allowance or have 14 days to report a change, only to face benefit termination, overpayment recovery, or sanctions later.

Hence, the core design principle of this architecture is **defensive groundedness**:
1. **Answer** only when exact, unambiguous, substantive policy evidence exists.
2. **Refuse** visibly with clear escalation pathways whenever policy coverage is absent or insufficient.
3. **Surface Contradictions** explicitly when the manual contains conflicting clauses, rather than silently choosing one interpretation.

---

## 2. Where We Drew the Line: Answering vs. Refusing

### The Trade-off Dilemma
Setting the threshold for refusal is an engineering and ethical trade-off:
- **Overly Permissive (Low Threshold)**: Minimizes caseworker friction on standard questions, but admits false positives on edge cases, apparent gaps (e.g., childcare vouchers), and out-of-scope policies (e.g., transport allowances).
- **Overly Strict (Excessive Threshold)**: Eliminates hallucinations, but degrades user trust by refusing questions that are clearly answered in the manual.

### Our Multi-Stage Decision Pipeline
Rather than relying on a single heuristic or a raw cosine similarity cutoff, our system employs a **multi-stage decision gate**:

```
                  ┌──────────────────────┐
                  │    User Question     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Hybrid Retrieval   │
                  │  (Dense FAISS +      │
                  │   Lexical Overlap)   │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Retrieval Threshold  │
                  │ Evaluation           │
                  └──────┬────────┬──────┘
                         │        │
            Score < 0.45 │        │ Score >= 0.45
                         │        │
                         ▼        ▼
                   [ REFUSE ]  ┌──────────────────────┐
                               │ Contradiction Check  │
                               │ (Conflicting Rules)  │
                               └──────┬────────┬──────┘
                                      │        │
                          Conflict    │        │ No Conflict
                          Detected    │        │
                                      ▼        ▼
                         [ CONTRADICTION ]  ┌──────────────────────┐
                         (Supervisor Alert) │  Evidence Validation │
                                            │ (Substantive Match)  │
                                            └──────┬────────┬──────┘
                                                   │        │
                                         Supported │        │ Unsupported
                                                   │        │ (Gap/Noise)
                                                   ▼        ▼
                                              [ ANSWER ] [ REFUSE ]
                                            (Grounded   (With Referral)
                                             Generation)
```

### Quantitative Thresholds & Calibration
1. **Dense Vector Similarity (`all-MiniLM-L6-v2`)**:
   - `ANSWER_THRESHOLD = 0.50` (Normalized Inner Product / Cosine Similarity)
   - `AMBIGUOUS_THRESHOLD = 0.45`
   - Dense retrieval provides high recall across semantic paraphrases, while our hybrid reranking applies a weighted bonus (`+0.08` per stemmed lexical overlap, `+0.05` for domain-critical terms like `earnings`, `disregard`, `resource`, `absence`).

2. **Lexical Substantive Validation (`src/evidence.py`)**:
   - Dense vector embeddings can suffer from "topic attraction"—for instance, a query about *"childcare vouchers"* or *"transport allowance"* yields moderate vector similarity against general income exclusions (§7.3.2) or standard allowances (§5.3.1), because the language models cluster benefit-related jargon together.
   - To counteract this, `evidence.py` filters stop words and generic domain terms (`eligibility`, `benefit`, `allowance`, `program`, `increase`), isolating *specific informative concepts* (e.g., `childcare`, `voucher`, `transport`).
   - If the query contains specific informative concepts, at least one must explicitly exist in the retrieved clause. If no substantive match is found, the system **refuses**, preventing confident misdirection on policy gaps.

---

## 3. Explicit Contradiction Detection

### The Corpus Inconsistency
The Calder County Policy Manual contains a genuine internal contradiction:
- **§4.3.2**: Requires recipients to report changes of address or circumstance within **10 calendar days**.
- **§9.1.4**: Mandates reporting of changes in circumstances within **14 calendar days**.

### Why Naive RAG Fails Here
A conventional RAG pipeline retrieves whichever clause happens to have a marginally higher vector score and answers with either "10 days" or "14 days", misleading the caseworker.

### Our Strategy (`src/contradiction.py`)
1. **Clause Feature Extraction**: Automatically extracts explicit numeric deadlines and time units (calendar days vs. working days) using structured regex matching.
2. **Conflict Resolution**: When a query asks about general change-of-circumstances reporting and multiple retrieved clauses offer conflicting deadlines for the same event category, the system flags a **CONTRADICTION**.
3. **Caseworker Action**: The system outputs an explicit alert identifying both conflicting clauses (§4.3.2 and §9.1.4) and instructs the caseworker to escalate to the Benefits Policy Supervisor.
4. **Specific vs. General Disambiguation**: For specific questions (e.g., change of address), §4.3.2 governs specifically, so the system provides the grounded answer with §4.3.2 without triggering false conflicts.

---

## 4. Verifiability & Grounded Output

### Strict Prompt Constraints
When evidence is verified and no contradictions exist, `src/answer.py` generates the final text using the following constraints:
- System prompt strictly forbids external knowledge or assumptions.
- Requires explicit clause attribution (e.g., `【§4.3.2】` or `§2.4.1`) for every factual assertion.
- Returns exact retrieved clause references alongside relevance scores in the terminal output.

---

## 5. Architectural Modularity (Day Two Readiness)

Per the competition specification, requirements may change on Day Two. The codebase is organized into cleanly decoupled, single-responsibility modules:

| Module | Responsibility | Independence Guarantee |
| :--- | :--- | :--- |
| `src/ingest.py` | Markdown parser extracting structured clauses | Can adapt to JSON, PDF, XML without affecting retrieval |
| `src/indexer.py` | Vector embedding generation & FAISS persistence | Index format can swap to Qdrant, Chroma, or BM25 |
| `src/retrieve.py` | Hybrid dense-lexical candidate retrieval | Independent of LLM or refusal thresholds |
| `src/refusal.py` | Quantitative threshold evaluation | Independent of retrieval backend and LLM client |
| `src/evidence.py` | Substantive concept overlap & gap prevention | Independent of contradiction logic |
| `src/contradiction.py` | Domain rule parsing & inconsistency detection | Can add new domain rules without altering ingest/LLM |
| `src/answer.py` | Prompt formatting & LLM generation | Can switch LLM providers (Groq, OpenAI, Ollama) cleanly |
| `src/cli.py` | Presentation layer & pipeline orchestration | Decoupled CLI interface |

If Day Two introduces a new corpus, altered time constraints, or new contradiction rules, only the relevant isolated module needs adjustment.
