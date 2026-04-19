import os
from groq import Groq
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 🔥 Fast + free model
MODEL = "llama-3.1-8b-instant"


RAG_PROMPT = PromptTemplate.from_template(
    """You are LexBot, an expert Indian Legal AI Assistant with deep knowledge of the Indian Constitution, IPC, CrPC, CPC, and all major Indian statutes.

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
    """You are LexBot, an expert Indian Legal AI Assistant with deep knowledge of the Indian Constitution, IPC, CrPC, CPC, and all major Indian statutes.

Guidelines:
- Give clear, accurate, well-structured answers
- Cite relevant sections / articles where applicable
- Always remind users to consult a qualified lawyer for specific matters

Question: {question}

Answer:"""
)


class LLMHandler:
    def __init__(self):
        self.vectorstore = None

    def set_vectorstore(self, vectorstore: FAISS):
        self.vectorstore = vectorstore

    def _generate(self, prompt: str) -> str:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=512,
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"⚠️ Groq Error: {str(e)}"

    def answer_with_docs(self, question: str) -> str:
        if not self.vectorstore:
            return self.answer_general(question)

        docs = self.vectorstore.similarity_search(question, k=2)
        context = "\n\n".join([d.page_content for d in docs])

        prompt = RAG_PROMPT.format(context=context, question=question)
        return self._generate(prompt)

    def answer_general(self, question: str) -> str:
        prompt = GENERAL_PROMPT.format(question=question)
        return self._generate(prompt)