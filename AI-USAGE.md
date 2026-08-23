# AI Usage & Disclosure: The Grounded Answer

## 1. Overview & Disclosure

In compliance with the Brite Spark 2026 AI Usage Policy and transparency requirements, this document discloses how Artificial Intelligence tools, embedding models, and Large Language Models (LLMs) were utilized in the development, runtime execution, and verification of this project.

---

## 2. Runtime AI Architecture

### 2.1 Embedding Model
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Role**: Computes dense 384-dimensional vector embeddings for all policy manual clauses (§1.1.1 through §12.3.3) and incoming user queries.
- **Execution**: Local inference via PyTorch and FAISS (`faiss-cpu`), requiring zero external network calls for vector indexing or similarity search.

### 2.2 LLM Answer Generation
- **Model**: `openai/gpt-oss-120b` (or configurable via `.env` / `GROQ_MODEL`) accessed via Groq / OpenAI compatible API endpoint.
- **Role**: Synthesizes natural language answers from strictly validated context clauses.
- **Guards**: The LLM is **never** relied upon as the sole arbiter of refusal or contradiction detection. Deterministic Python modules (`src/refusal.py`, `src/evidence.py`, `src/contradiction.py`) evaluate and gate all inputs before LLM invocation, preventing hallucinated answers or bypassed refusals.

---

## 3. Development-Time AI Assistance

During development, AI assistants (Antigravity coding assistant) were employed for:
1. **Scaffolding & Boilerplate**: Generating initial CLI skeletons using `typer` and vector pipeline helpers.
2. **Corpus Exploration**: Assisting in parsing Markdown headers and clause delimiters for `src/ingest.py`.
3. **Test Case Synthesis**: Formulating a balanced 10-question evaluation dataset (`test/test_questions.json`) designed to stress-test direct answers, boundary conditions, policy gaps, and internal contradictions.

---

## 4. Prompt Engineering & Grounding Controls

The system prompt for answer generation is deliberately constrained to eliminate external priors:

```text
You are a Calder County policy assistant.

Rules:
- Answer ONLY using the supplied policy clauses.
- Never use outside knowledge.
- Every factual statement must reference its clause ID.
- If the clauses conflict or do not answer the question, refuse politely.
```

Additionally:
- `temperature` is set to `0.1` to maximize determinism and factual adherence.
- Context injection is strictly formatted with explicit clause headers (`§X.Y.Z: <text>`).

---

## 5. Verification & Human Oversight

All automated components and test suites underwent rigorous manual validation:
- Every clause cited in the test suite was manually checked against `data/policy-manual.md`.
- Contradiction triggers between §4.3.2 (10 days) and §9.1.4 (14 days) were verified by inspecting the ground-truth manual.
- Refusal cases on unmentioned subjects ("childcare vouchers", "transport allowance") were validated to confirm that the system cleanly rejects queries lacking substantive evidence rather than returning adjacent benefit sections.
