"""
LLM Handler – LLaMA 3.1 via Ollama with RAG support (UPDATED - no RetrievalQA)
"""
import os
from typing import Optional

# from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS


# ------------------ PROMPTS ------------------

RAG_PROMPT = PromptTemplate.from_template(
    """You are LexBot, an expert Indian Legal AI Assistant with deep knowledge of
the Indian Constitution, IPC, CrPC, CPC, and all major Indian statutes.

Guidelines:
- Give clear, accurate, well-structured answers
- Cite relevant sections / articles where applicable
- Use bullet points for step-by-step processes
- Always remind users to consult a qualified lawyer for specific legal advice
- If unsure, say so rather than speculating

Context from legal documents:
{context}

Question: {question}

Answer (be thorough but concise):"""
)

GENERAL_PROMPT = PromptTemplate.from_template(
    """You are LexBot, an expert Indian Legal AI Assistant with deep knowledge of
the Indian Constitution, IPC, CrPC, CPC, and all major Indian statutes.

Guidelines:
- Give clear, accurate, well-structured answers
- Cite relevant sections / articles where applicable
- Always remind users to consult a qualified lawyer for specific matters

Question: {question}

Answer:"""
)


# ------------------ HANDLER ------------------

class LLMHandler:
    def __init__(self):
        self.llm = OllamaLLM(
            model="llama3.1:8b",
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            temperature=0.1,
            num_ctx=2048,
        )

        self.chain = None
        self.vectorstore = None

    # 🔥 NEW RAG PIPELINE (no RetrievalQA)
    def set_vectorstore(self, vectorstore: FAISS):
        self.vectorstore = vectorstore
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 2},
        )

        def format_docs(docs):
            return "\n\n".join([doc.page_content for doc in docs])

        self.chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough(),
            }
            | RAG_PROMPT
            | self.llm
            | StrOutputParser()
        )

    # ------------------ RAG ANSWER ------------------

    def answer_with_docs(self, question: str) -> str:
        if not self.chain:
            return self.answer_general(question)

        try:
            return self.chain.invoke(question)

        except Exception as e:
            return f"⚠️ Error: {e}\n\nEnsure Ollama is running with LLaMA 3.1."

    # ------------------ GENERAL ANSWER ------------------

    def answer_general(self, question: str) -> str:
        try:
            chain = GENERAL_PROMPT | self.llm | StrOutputParser()
            return chain.invoke({"question": question})

        except Exception as e:
            return (
                f"⚠️ Cannot connect to Ollama.\n\n"
                f"Please ensure:\n"
                f"1. Ollama is running → `ollama serve`\n"
                f"2. Model is pulled   → `ollama pull llama3.1`\n"
                f"3. Host is correct   → check Configuration in sidebar\n\n"
                f"Error: {e}"
            )