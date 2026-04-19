"""
LLM Handler
- LLM      : Groq API  (llama3-8b-8192  — fast, free tier, cloud safe)
- RAG      : similarity search on FAISS vectorstore
- Cloud    : 100% HTTP — no local server needed
"""

import os
import requests
from typing import Optional
from langchain_community.vectorstores import FAISS

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"   # fast + free tier on Groq

SYSTEM_PROMPT = """You are LexBot, an expert Indian Legal AI Assistant with deep knowledge of
the Indian Constitution, IPC, CrPC, CPC, and all major Indian statutes.

Guidelines:
- Give clear, accurate, well-structured answers
- Cite relevant sections and articles where applicable
- Use bullet points for step-by-step processes
- Always remind users to consult a qualified lawyer for specific legal advice
- If unsure, say so — never make up law"""


class LLMHandler:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found.\n"
                "Add it to Streamlit Secrets:  GROQ_API_KEY = \"gsk_xxxx\"\n"
                "Get a free key at: https://console.groq.com"
            )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }
        self.vectorstore: Optional[FAISS] = None

    def set_vectorstore(self, vectorstore: FAISS):
        self.vectorstore = vectorstore

    # ── RAG answer ────────────────────────────────────────────────────────────
    def answer_with_docs(self, question: str) -> str:
        if not self.vectorstore:
            return self.answer_general(question)
        try:
            docs    = self.vectorstore.similarity_search(question, k=4)
            context = "\n\n".join(d.page_content for d in docs)
            sources = list({d.metadata.get("source", "Document") for d in docs})

            user_msg = f"""Use the following context from legal documents to answer the question.

Context:
{context}

Question: {question}

Answer (be thorough but concise):"""

            answer = self._call_groq(user_msg)

            if sources:
                src = ", ".join(f"📄 {s}" for s in sources)
                answer += f"\n\n---\n*Sources: {src}*"

            return answer

        except Exception as e:
            return f"⚠️ Error generating answer: {e}"

    # ── General answer (no docs) ──────────────────────────────────────────────
    def answer_general(self, question: str) -> str:
        return self._call_groq(question)

    # ── Groq API call ─────────────────────────────────────────────────────────
    def _call_groq(self, user_message: str) -> str:
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            "temperature": 0.1,
            "max_tokens":  1024,
        }
        try:
            resp = requests.post(
                GROQ_API_URL,
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code == 429:
                return "⚠️ Groq rate limit hit. Please wait a moment and try again."
            if resp.status_code != 200:
                return f"⚠️ Groq API error ({resp.status_code}): {resp.text[:300]}"

            return resp.json()["choices"][0]["message"]["content"]

        except requests.exceptions.Timeout:
            return "⚠️ Request timed out. Please try again."
        except Exception as e:
            return f"⚠️ LLM error: {e}"
