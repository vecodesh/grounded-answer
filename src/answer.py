from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
You are a Calder County policy assistant.

Rules:
- Answer ONLY using the supplied policy clauses.
- Never use outside knowledge.
- Every factual statement must reference its clause ID.
- If the clauses conflict or do not answer the question, refuse politely.
"""

def generate_answer(question: str, retrieved_clauses: list):

    context = ""

    for clause in retrieved_clauses:
        context += f"{clause['clause_id']}: {clause['text']}\n\n"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"Question:\n{question}\n\nPolicy Clauses:\n{context}"
            }
        ]
    )

    return response.choices[0].message.content