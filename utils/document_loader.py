"""
Document Loader (PRODUCTION - HF API EMBEDDINGS)

✔ Real embeddings (HuggingFace API)
✔ No torch / no heavy install
✔ Works on Streamlit Cloud
✔ Incremental FAISS updates
✔ Handles PDF + DOCX
"""

import os
import glob
import json
import requests
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS


# ── PATH ─────────────────────────────────────────────
DOCUMENTS_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "files"
)


# ── CUSTOM HF EMBEDDINGS (LIGHTWEIGHT API) ───────────
class HFAPIEmbeddings:
    def __init__(self):
        self.api_key = os.getenv("HF_TOKEN")
        self.model = "sentence-transformers/all-MiniLM-L6-v2"
        self.url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model}"

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    # ✅ ADD THIS (FIX)
    def __call__(self, text):
        return self.embed_query(text)

    def _embed(self, text):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.post(self.url, headers=headers, json={"inputs": text})

        if response.status_code != 200:
            raise Exception(f"HF API Error: {response.text}")

        data = response.json()

        if isinstance(data[0], list):
            return data[0]

        return data


# ── DOCUMENT LOADER ──────────────────────────────────
class DocumentLoader:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
        )

        # ✅ Use HF API embeddings (lightweight)
        self.embeddings = HFAPIEmbeddings()

    # ────────────────────────────────────────────────
    def load_from_folder(
        self, folder_path: str = DOCUMENTS_FOLDER
    ) -> Tuple[FAISS, int, int]:

        os.makedirs(folder_path, exist_ok=True)

        file_paths = list(set(
            glob.glob(os.path.join(folder_path, "**", "*.pdf"), recursive=True) +
            glob.glob(os.path.join(folder_path, "**", "*.docx"), recursive=True)
        ))

        if not file_paths:
            raise FileNotFoundError("❌ No PDF/DOCX files found.")

        faiss_path = "faiss_index"
        metadata_path = "file_metadata.json"

        # ── Load metadata ─────────────────────────────
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                old_files = set(json.load(f))
        else:
            old_files = set()

        current_files = set(file_paths)
        new_files = current_files - old_files

        print(f"📂 Total files: {len(current_files)}")
        print(f"🆕 New files: {len(new_files)}")

        # ── Load FAISS safely ─────────────────────────
        vectorstore = None

        if os.path.exists(faiss_path):
            try:
                vectorstore = FAISS.load_local(
                    faiss_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("⚡ Loaded existing FAISS")
            except Exception as e:
                print("⚠️ FAISS load failed:", e)
                vectorstore = None

        new_docs: List[Document] = []

        # ── Process new files only ───────────────────
        for fp in new_files:
            fname = os.path.basename(fp)

            try:
                text = self._extract_text(fp)

                if not text or len(text.strip()) < 50:
                    print(f"[Loader] ⚠️ {fname} skipped")
                    continue

                chunks = self.splitter.split_text(text)

                docs = [
                    Document(page_content=chunk, metadata={"source": fname})
                    for chunk in chunks
                ]

                new_docs.extend(docs)
                print(f"[Loader] ✅ {fname} → {len(docs)} chunks")

            except Exception as e:
                print(f"[Loader] ❌ {fname}: {e}")

        # ── Create / update FAISS ────────────────────
        if vectorstore is None:
            if not new_docs:
                raise ValueError("❌ No documents to create index.")

            print("🧠 Creating FAISS index...")
            vectorstore = FAISS.from_documents(new_docs, self.embeddings)

        elif new_docs:
            print("➕ Adding new documents...")
            vectorstore.add_documents(new_docs)

        else:
            print("✅ No new documents.")

        # ── Save FAISS ───────────────────────────────
        vectorstore.save_local(faiss_path)

        # ── Save metadata ────────────────────────────
        with open(metadata_path, "w") as f:
            json.dump(list(current_files), f)

        print("✅ Knowledge base ready!")

        return vectorstore, len(current_files), len(new_docs)

    # ────────────────────────────────────────────────
    def _extract_text(self, path: str) -> str:

        # ── PDF ─────────────────────────────────────
        if path.lower().endswith(".pdf"):
            try:
                import fitz
                text = ""
                with fitz.open(path) as doc:
                    for page in doc:
                        text += page.get_text()
                return text
            except Exception:
                return ""

        # ── DOCX ────────────────────────────────────
        elif path.lower().endswith(".docx"):
            try:
                from docx import Document as DocxDoc
                doc = DocxDoc(path)
                return "\n\n".join(
                    p.text for p in doc.paragraphs if p.text.strip()
                )
            except Exception:
                return ""

        return ""
# 
# 
# """
# Document Loader
# Auto-loads all PDF and DOCX files from the  files/  folder at startup.
# """
# import io
# import os
# import glob
# import tempfile
# from typing import List, Tuple

# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import OllamaEmbeddings
# from langchain_core.documents import Document

# # ── Folder where you place your legal documents ───────────────────────────────
# DOCUMENTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "files")


# class DocumentLoader:
#     def __init__(self):
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=800,
#             chunk_overlap=100,
#             separators=["\n\n", "\n", ".", "?", "!", " "],
#         )

#     # ── Load all docs from backend folder ────────────────────────────────────
#     def load_from_folder(self, folder_path: str = DOCUMENTS_FOLDER, progress_bar=None) -> Tuple[FAISS, int, int]:
#         """
#         Scans folder_path (and its subfolders) for PDF / DOCX files,
#         extracts text, chunks it, and returns a FAISS vectorstore.
#         """
#         os.makedirs(folder_path, exist_ok=True)

#         file_paths = list(set(
#             glob.glob(os.path.join(folder_path, "**", "*.pdf"),  recursive=True) +
#             glob.glob(os.path.join(folder_path, "**", "*.docx"), recursive=True) +
#             glob.glob(os.path.join(folder_path, "**", "*.doc"),  recursive=True)
#         ))

#         if not file_paths:
#             raise FileNotFoundError(
#                 f"No PDF or DOCX files found in: {folder_path}\n"
#                 f"Please add your legal documents to that folder."
#             )

#         all_docs: List[Document] = []
#         total = len(file_paths)

#         for idx, fp in enumerate(file_paths):
#             fname = os.path.basename(fp)
#             try:
#                 with open(fp, "rb") as f:
#                     raw = f.read()
#                 if fp.lower().endswith(".pdf"):
#                     text = self._extract_pdf(raw)
#                 else:
#                     text = self._extract_docx(raw)

#                 split_texts = self.text_splitter.split_text(text)
#                 chunks = self.text_splitter.create_documents(
#                     [text],
#                     metadatas=[{"source": fname}] * len(split_texts),
#                 )
#                 all_docs.extend(chunks)
#                 print(f"[Loader] ✅ {fname}  →  {len(chunks)} chunks")
#             except Exception as e:
#                 print(f"[Loader] ❌ {fname}: {e}")

#             if progress_bar:
#                 progress_bar.progress(int((idx + 1) / total * 85), text=f"Processing {fname}…")

#         if not all_docs:
#             raise ValueError("No text could be extracted from any document.")

#         embeddings  = OllamaEmbeddings(
#             model="llama3.1:8b",
#             base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
#         )
#         vectorstore = FAISS.from_documents(all_docs, embeddings)

#         if progress_bar:
#             progress_bar.progress(100, text="Knowledge base ready!")

#         return vectorstore, total, len(all_docs)

#     # ── PDF extractor ─────────────────────────────────────────────────────────
#     def _extract_pdf(self, raw: bytes) -> str:
#         try:
#             import pdfplumber
#             parts = []
#             with pdfplumber.open(io.BytesIO(raw)) as pdf:
#                 for page in pdf.pages:
#                     t = page.extract_text()
#                     if t:
#                         parts.append(t)
#             return "\n\n".join(parts)
#         except Exception:
#             from pypdf import PdfReader
#             reader = PdfReader(io.BytesIO(raw))
#             return "\n\n".join(p.extract_text() or "" for p in reader.pages)

#     # ── DOCX extractor ────────────────────────────────────────────────────────
#     def _extract_docx(self, raw: bytes) -> str:
#         from docx import Document as DocxDoc
#         with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
#             tmp.write(raw)
#             tmp_path = tmp.name
#         doc  = DocxDoc(tmp_path)
#         text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
#         os.unlink(tmp_path)
#         return text
