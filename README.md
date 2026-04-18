# ⚖️ LexBot – AI Legal Assistant

## Setup

```bash
# 1. Create conda environment
conda create -n lexbot python=3.11 -y
conda activate lexbot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull and start LLaMA 3.1 via Ollama
ollama pull llama3.1
ollama serve

# 4. Add your legal documents
#    Copy all your PDF / DOCX files into the  files/  folder

# 5. Run the app
streamlit run app.py
```

Open browser at: **http://localhost:8501**

---

## Project Structure

```
law_chatbot/
├── app.py                    ← Main Streamlit app
├── requirements.txt
├── files/                    ← PUT YOUR PDFs AND DOCX FILES HERE
│   ├── constitution.pdf
│   ├── ipc.pdf
│   └── crpc.docx
└── utils/
    ├── __init__.py
    ├── document_loader.py    ← PDF/DOCX → FAISS vectorstore
    ├── llm_handler.py        ← LLaMA 3.1 RAG pipeline
    └── bhashini_handler.py   ← Bhashini Translation + TTS
```

---

## Features

- **Auto-loads** all documents from `files/` folder at startup (no upload needed)
- **RAG Q&A** powered by LLaMA 3.1 over your legal documents
- **Translation** into 11 Indian languages via Bhashini API
- **Text-to-Speech** with female/male voice via Bhashini API
- **Dark gold UI** with chat history and quick questions

---

## ⚠️ Disclaimer

LexBot provides general legal information only. Always consult a qualified legal professional.
