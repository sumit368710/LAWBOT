# import os
# from groq import Groq
# # import os
# import streamlit as st
# # from groq import Groq
# from langchain_core.prompts import PromptTemplate
# from langchain_community.vectorstores import FAISS

# api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

# client = Groq(api_key=api_key)

# # 🔥 Fast + free model
# MODEL = "llama-3.1-8b-instant"


# RAG_PROMPT = PromptTemplate.from_template(
#     """You are LexBot, an expert Indian Legal AI Assistant with deep knowledge of the Indian Constitution, IPC, CrPC, CPC, and all major Indian statutes.

# Guidelines:
# - Give clear, accurate, well-structured answers
# - Cite relevant sections / articles where applicable
# - Use bullet points for step-by-step processes
# - Always remind users to consult a qualified lawyer for specific legal advice
# - If unsure, say so rather than speculating

# Context from legal documents:
# {context}

# Question: {question}

# Answer (be thorough but concise):"""
# )

# GENERAL_PROMPT = PromptTemplate.from_template(
#     """You are LexBot, an expert Indian Legal AI Assistant with deep knowledge of the Indian Constitution, IPC, CrPC, CPC, and all major Indian statutes.

# Guidelines:
# - Give clear, accurate, well-structured answers
# - Cite relevant sections / articles where applicable
# - Always remind users to consult a qualified lawyer for specific matters

# Question: {question}

# Answer:"""
# )


# class LLMHandler:
#     def __init__(self):
#         self.vectorstore = None

#     def set_vectorstore(self, vectorstore: FAISS):
#         self.vectorstore = vectorstore

#     def _generate(self, prompt: str) -> str:
#         try:
#             response = client.chat.completions.create(
#                 model=MODEL,
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.3,
#                 max_tokens=512,
#             )
#             return response.choices[0].message.content

#         except Exception as e:
#             return f"⚠️ Groq Error: {str(e)}"

#     def answer_with_docs(self, question: str) -> str:
#         if not self.vectorstore:
#             return self.answer_general(question)

#         docs = self.vectorstore.similarity_search(question, k=2)
#         context = "\n\n".join([d.page_content for d in docs])

#         prompt = RAG_PROMPT.format(context=context, question=question)
#         return self._generate(prompt)

#     def answer_general(self, question: str) -> str:
#         prompt = GENERAL_PROMPT.format(question=question)
#         return self._generate(prompt)

"""
LLM Handler (PRODUCTION READY - GROQ VERSION)

✔ Works locally + Streamlit Cloud
✔ Uses Groq API (fast + stable)
✔ Safe API key handling
✔ RAG support with FAISS
"""

"""
LLM Handler (FINAL - GROQ VERSION)

✔ Works locally + Streamlit Cloud
✔ Safe API key handling (no crash)
✔ RAG support with FAISS
✔ Clean error handling
"""

import os
import streamlit as st
from groq import Groq
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS


# ── GET API KEY SAFELY ───────────────────────────────
def get_api_key():
    # Try environment variable first
    key = os.getenv("GROQ_API_KEY")

    # Fallback to Streamlit secrets
    if not key:
        try:
            key = st.secrets["GROQ_API_KEY"]
        except Exception:
            key = None

    return key


api_key = get_api_key()

# Create client only if key exists
client = Groq(api_key=api_key) if api_key else None


# ── MODEL (UPDATED GROQ MODEL) ───────────────────────
MODEL = "llama-3.1-8b-instant"
# Optional upgrade:
# MODEL = "llama-3.1-70b-versatile"


# ── PROMPTS ─────────────────────────────────────────
RAG_PROMPT = PromptTemplate.from_template(
    """You are LexBot, an expert Indian Legal AI Assistant.

Use the context to answer the question clearly.

Guidelines:
- Answer in your own words (do not copy directly)
- Use bullet points where helpful
- Cite relevant legal sections if available

Context:
{context}

Question:
{question}

Answer:"""
)

GENERAL_PROMPT = PromptTemplate.from_template(
    """You are a legal assistant.

Answer clearly and concisely.

Question:
{question}

Answer:"""
)


# ── LLM HANDLER ─────────────────────────────────────
class LLMHandler:
    def __init__(self):
        self.vectorstore = None

    def set_vectorstore(self, vectorstore: FAISS):
        self.vectorstore = vectorstore

    def _generate(self, prompt: str) -> str:
        # If API key missing → show message (no crash)
        if client is None:
            return "⚠️ GROQ_API_KEY not configured. Please add it in Streamlit Secrets."

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=512,
            )

            content = response.choices[0].message.content

            if not content or len(content.strip()) == 0:
                return "⚠️ Model returned empty response. Try again."

            return content

        except Exception as e:
            return f"⚠️ Groq Error: {str(e)}"

    def answer_with_docs(self, question: str) -> str:
        try:
            if not self.vectorstore:
                return self.answer_general(question)

            docs = self.vectorstore.similarity_search(question, k=2)

            if not docs:
                return self.answer_general(question)

            context = "\n\n".join([d.page_content for d in docs])

            prompt = RAG_PROMPT.format(
                context=context,
                question=question
            )

            return self._generate(prompt)

        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    def answer_general(self, question: str) -> str:
        try:
            prompt = GENERAL_PROMPT.format(question=question)
            return self._generate(prompt)
        except Exception as e:
            return f"⚠️ Error: {str(e)}"