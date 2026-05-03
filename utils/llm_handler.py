import os
import requests
from typing import Optional
from langchain_community.vectorstores import FAISS

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.1-8b-instant"


SYSTEM_PROMPT = """You are LexBot, an expert Indian Legal AI Assistant with deep knowledge of
the Indian Constitution, IPC, CrPC, CPC, and all major Indian statutes.

Guidelines:

1. CONTEXT USAGE (VERY IMPORTANT)

- If context is provided, first return the answer EXACTLY as it appears in the document/context.
- Do NOT change wording, grammar, spelling, punctuation, formatting, or line breaks.
- Do NOT summarize, paraphrase, or translate inside this section.
- If answer is incomplete, search entire context and include ALL relevant points.
- Do not stop at partial answer.
- Print this heading exactly:

📄 From Study Material

- On the very next line, print only the exact copied answer from the document.
- Do not place any explanation on the same line as the heading.

✅ IMPORTANT UPDATE:
- If the answer is spread across multiple context chunks, you MUST combine them.
- You are allowed to include multiple exact chunks one after another.
- Do NOT skip relevant parts just because they are in different chunks.
- Completeness is more important than returning a single chunk.


Example Format:

📄 From Study Material
[Exact text from chunk 1]

[Exact text from chunk 2]

2. EXPLANATION
- After the context, explain the answer in simple and clear language.
- Use a heading: "🧠 Explanation"
- Make it easy to understand for students.

3. STRUCTURE
- Use bullet points wherever helpful
- Break down concepts step-by-step

4. EXAMPLES
- Provide a simple real-life example under: "💡 Example"

5. CASE LAW (if applicable)
- If relevant case law exists, include:
  - Case name
  - Key issue
  - Outcome / principle
- Use heading: "⚖️ Case Law"

6. ACCURACY RULE (STRICT)
- Do NOT hallucinate or invent legal provisions or case laws
- If information is not in context, clearly say:
  "This information is not available in the provided material."

7. DOMAIN RESTRICTION
- Only answer questions related to:
  - Law
  - Legal studies
  - Exams (LLB, judiciary, etc.)
- If user asks anything else, respond:
  "I am a legal exam assistant and can only help with law-related questions."

8. BEHAVIOR
- Act like a professional legal study assistant
- Keep answers exam-oriented, structured, and precise

9. DISCLAIMER
- Always end with:
  "Consult a qualified lawyer for specific legal advice."""


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

    # 🔥 MAIN RAG FUNCTION (FIXED)
#     def answer_with_docs(self, question: str):

#         # 🔥 STEP 1: retrieve with score
#         # docs = self.vectorstore.similarity_search_with_score(question, k=6)
#         retriever = self.vectorstore.as_retriever(
#             search_type="mmr",
#             search_kwargs={"k": 6, "fetch_k": 12}
#         )

#         docs = retriever.get_relevant_documents(question)

#         # 🔥 STEP 2: filter context
#         # filtered_chunks = []
#         filtered_chunks = [doc.page_content for doc in docs]

#         for doc, score in docs:

#             text = doc.page_content.strip()

#             # ❌ remove weak matches
#             if score > 1.2:
#                 continue

#             # ❌ remove garbage
#             if any(x in text.lower() for x in [
#                 "api", "error", "http", "bearer", "traceback"
#             ]):
#                 continue

#             # ❌ remove tiny chunks
#             if len(text) < 80:
#                 continue

#             filtered_chunks.append(text)

#         # 🔥 STEP 3: build context
#         context = "\n\n".join(filtered_chunks)

#         print("\n==== FINAL CONTEXT ====\n", context)

#         # 🔥 STEP 4: HARD STOP (NO CONTEXT = NO ANSWER)
#         if not context:
#             return "No direct context found. Answer carefully."

#         # 🔥 STEP 5: STRICT USER MESSAGE
#         user_msg = f"""
# STRICT MODE:

# You MUST answer ONLY using the given context.

# If answer is not clearly present → return:
# "This information is not available in the provided material."

# Context:
# {context}

# Question:
# {question}
# """

#         return self._call_groq(user_msg)

    def answer_with_docs(self, question: str):

        # 🔥 STEP 1: MMR Retriever
        retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 8, "fetch_k": 16}
        )

        docs = retriever.invoke(question)

        def is_relevant(text):
            text_lower = text.lower()

            important_words = [
                w for w in question.lower().split()
                if len(w) > 4
            ]

            match_count = sum(1 for w in important_words if w in text_lower)

            return match_count >= 1


        def is_clean_text(text):
            non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / len(text)
            return non_ascii_ratio < 0.2


        filtered_chunks = []

        for doc in docs:
            text = doc.page_content

            if not is_clean_text(text):
                continue

            if is_relevant(text):
                filtered_chunks.append(text)


        # LIMIT CONTEXT
        filtered_chunks = filtered_chunks[:5]

        context = "\n\n".join(filtered_chunks)

        print("\n==== FINAL CONTEXT ====\n", context)

        # 🔥 STEP 4: fallback
        if not context:
            context = "No relevant context found. Answer carefully."

        # 🔥 STEP 5: PROMPT
        user_msg = f"""
STRICT LEGAL QA MODE:

You MUST answer ONLY from the given context.

RULES:
- Do NOT include any extra topic
- Do NOT mix multiple answers
- Do NOT include unrelated concepts
- If multiple topics appear → IGNORE unrelated parts

If answer is incomplete → say:
"Answer not fully available in provided material."

Context:
{context}

Question:
{question}
"""

        return self._call_groq(user_msg)

    # ─────────────────────────────
    # GROQ CALL
    # ─────────────────────────────
    def _call_groq(self, user_msg):

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            "temperature": 0.0,   # 🔥 critical
            "max_tokens": 2000,
        }

        try:
            resp = requests.post(
                GROQ_API_URL,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            if resp.status_code != 200:
                print("❌ GROQ ERROR:", resp.text)
                return "⚠️ LLM error"

            return resp.json()["choices"][0]["message"]["content"]

        except Exception as e:
            print("❌ LLM ERROR:", e)
            return "⚠️ LLM failure"





# """
# LLM Handler
# - LLM      : Groq API  (llama3-8b-8192  — fast, free tier, cloud safe)
# - RAG      : similarity search on FAISS vectorstore
# - Cloud    : 100% HTTP — no local server needed
# """

# import os
# import requests
# from typing import Optional
# from langchain_community.vectorstores import FAISS

# GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# GROQ_MODEL   = "llama-3.1-8b-instant"   # fast + free tier on Groq

# SYSTEM_PROMPT = """You are LexBot, an expert Indian Legal AI Assistant with deep knowledge of
# the Indian Constitution, IPC, CrPC, CPC, and all major Indian statutes.

# Guidelines:

# 1. CONTEXT USAGE (VERY IMPORTANT)
# - If context is provided, first present the answer EXACTLY as it appears in the context (verbatim).
# - Do NOT modify, summarize, or rephrase this part.
# - Clearly separate this section using a heading: "📄 From Study Material"

# 2. EXPLANATION
# - After the context, explain the answer in simple and clear language.
# - Use a heading: "🧠 Explanation"
# - Make it easy to understand for students.

# 3. STRUCTURE
# - Use bullet points wherever helpful
# - Break down concepts step-by-step

# 4. EXAMPLES
# - Provide a simple real-life example under: "💡 Example"

# 5. CASE LAW (if applicable)
# - If relevant case law exists, include:
#   - Case name
#   - Key issue
#   - Outcome / principle
# - Use heading: "⚖️ Case Law"

# 6. ACCURACY RULE (STRICT)
# - Do NOT hallucinate or invent legal provisions or case laws
# - If information is not in context, clearly say:
#   "This information is not available in the provided material."

# 7. DOMAIN RESTRICTION
# - Only answer questions related to:
#   - Law
#   - Legal studies
#   - Exams (LLB, judiciary, etc.)
# - If user asks anything else, respond:
#   "I am a legal exam assistant and can only help with law-related questions."

# 8. BEHAVIOR
# - Act like a professional legal study assistant
# - Keep answers exam-oriented, structured, and precise

# 9. DISCLAIMER
# - Always end with:
#   "Consult a qualified lawyer for specific legal advice."
# """


# class LLMHandler:
#     def __init__(self):
#         self.api_key = os.getenv("GROQ_API_KEY", "")
#         if not self.api_key:
#             raise ValueError(
#                 "GROQ_API_KEY not found.\n"
#                 "Add it to Streamlit Secrets:  GROQ_API_KEY = \"gsk_xxxx\"\n"
#                 "Get a free key at: https://console.groq.com"
#             )
#         self.headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type":  "application/json",
#         }
#         self.vectorstore: Optional[FAISS] = None

#     def set_vectorstore(self, vectorstore: FAISS):
#         self.vectorstore = vectorstore

#     # ── RAG answer ────────────────────────────────────────────────────────────
#     def answer_with_docs(self, question: str) -> str:
#         if not self.vectorstore:
#             return self.answer_general(question)
#         try:
#             docs    = self.vectorstore.similarity_search(question, k=4)
#             context = "\n\n".join(d.page_content for d in docs)
#             sources = list({d.metadata.get("source", "Document") for d in docs})

#             user_msg = f"""Use the following context from legal documents to answer the question.

# Context:
# {context}

# Question: {question}

# Answer (be thorough but concise):"""

#             answer = self._call_groq(user_msg)

#             if sources:
#                 src = ", ".join(f"📄 {s}" for s in sources)
#                 answer += f"\n\n---\n*Sources: {src}*"

#             return answer

#         except Exception as e:
#             return f"⚠️ Error generating answer: {e}"

#     # ── General answer (no docs) ──────────────────────────────────────────────
#     def answer_general(self, question: str) -> str:
#         return self._call_groq(question)

#     # ── Groq API call ─────────────────────────────────────────────────────────
#     def _call_groq(self, user_message: str) -> str:
#         payload = {
#             "model": GROQ_MODEL,
#             "messages": [
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user",   "content": user_message},
#             ],
#             "temperature": 0.1,
#             "max_tokens":  1024,
#         }
#         try:
#             resp = requests.post(
#                 GROQ_API_URL,
#                 headers=self.headers,
#                 json=payload,
#                 timeout=60,
#             )
#             if resp.status_code == 429:
#                 return "⚠️ Groq rate limit hit. Please wait a moment and try again."
#             if resp.status_code != 200:
#                 return f"⚠️ Groq API error ({resp.status_code}): {resp.text[:300]}"

#             return resp.json()["choices"][0]["message"]["content"]

#         except requests.exceptions.Timeout:
#             return "⚠️ Request timed out. Please try again."
#         except Exception as e:
#             return f"⚠️ LLM error: {e}"
