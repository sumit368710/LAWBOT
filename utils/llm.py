## for groq

import os
import requests
from typing import Optional
from langchain_community.vectorstores import FAISS

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"


SYSTEM_PROMPT = """You are LexBot, an expert Indian Legal AI Assistant.

Capabilities:
- Answer from documents
- Answer general legal questions
- Respond conversationally

Rules:
- Prefer document context when relevant
- If not available, use legal knowledge
- Do NOT hallucinate legal facts

End with:
Consult a qualified lawyer for specific legal advice.
"""


# =========================
# LLM INTENT DETECTION
# =========================
def detect_intent_llm(question, headers):

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Classify user intent into: greeting, law, document, irrelevant. Return ONLY one word."
            },
            {"role": "user", "content": question},
        ],
        "temperature": 0,
        "max_tokens": 10,
    }

    try:
        r = requests.post(GROQ_API_URL, headers=headers, json=payload)
        return r.json()["choices"][0]["message"]["content"].strip().lower()
    except:
        return "document"


# =========================
# KEYWORD SEARCH (HYBRID)
# =========================
def keyword_match_score(query, text):
    query_words = set(query.lower().split())
    text_words = set(text.lower().split())
    return len(query_words & text_words)


# =========================
# LLM HANDLER
# =========================
class LLMHandler:

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.vectorstore: Optional[FAISS] = None

    def set_vectorstore(self, vs):
        self.vectorstore = vs


    # =========================
    # MAIN FUNCTION
    # =========================
    def answer(self, question: str):

        intent = detect_intent_llm(question, self.headers)
        print("🧠 Intent:", intent)

        # =====================
        # GREETING
        # =====================
        if "greeting" in intent:
            return (
                "👋 Hello! I am LexBot, your legal AI assistant.\n\n"
                "Ask me anything about law or your documents."
            )

        # =====================
        # IRRELEVANT
        # =====================
        if "irrelevant" in intent:
            return "⚠️ I can only help with legal-related questions."

        # =====================
        # GENERAL LAW
        # =====================
        if "law" in intent:
            return self._call_general(question)

        # =====================
        # DOCUMENT MODE
        # =====================
        if not self.vectorstore:
            return self._call_general(question)

        docs = self.vectorstore.similarity_search_with_score(question, k=10)

        # 🔥 HYBRID SCORING
        scored_docs = []
        for doc, score in docs:
            keyword_score = keyword_match_score(question, doc.page_content)
            final_score = score - (keyword_score * 0.1)
            scored_docs.append((doc, final_score))

        # 🔥 SORT
        scored_docs = sorted(scored_docs, key=lambda x: x[1])[:5]

        # =====================
        # LLM RERANK
        # =====================
        context_candidates = [d.page_content[:400] for d, _ in scored_docs]

        best_context = self._rerank(question, context_candidates)

        if not best_context:
            return self._call_general(question)

        # =====================
        # FINAL ANSWER
        # =====================
        user_msg = f"""
Answer using best context.

Context:
{best_context}

Question:
{question}
"""

        return self._call_rag(user_msg)


    # =========================
    # LLM RERANK
    # =========================
    def _rerank(self, question, contexts):

        joined = "\n\n---\n\n".join(contexts)

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Select the MOST relevant context for the question. Return ONLY that text."
                },
                {
                    "role": "user",
                    "content": f"Question:\n{question}\n\nContexts:\n{joined}"
                }
            ],
            "temperature": 0,
            "max_tokens": 800,
        }

        try:
            r = requests.post(GROQ_API_URL, headers=self.headers, json=payload)
            return r.json()["choices"][0]["message"]["content"]
        except:
            return None


    # =========================
    # GENERAL CALL
    # =========================
    def _call_general(self, question):

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            "temperature": 0.3,
            "max_tokens": 1500,
        }

        r = requests.post(GROQ_API_URL, headers=self.headers, json=payload)
        return r.json()["choices"][0]["message"]["content"]


    # =========================
    # RAG CALL
    # =========================
    def _call_rag(self, user_msg):

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "temperature": 0.0,
            "max_tokens": 1500,
        }

        r = requests.post(GROQ_API_URL, headers=self.headers, json=payload)
        return r.json()["choices"][0]["message"]["content"]