"""
Document Loader (PRODUCTION READY)
- Fast (cached FAISS)
- Incremental updates (only new files processed)
- OCR support (Tesseract + Poppler)
"""

import os
import glob
import json
import tempfile
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

# OCR
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Folder path
DOCUMENTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "files")


class DocumentLoader:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", "?", "!", " "],
        )

    # ───────────────────────────────────────────────
    # MAIN FUNCTION
    # ───────────────────────────────────────────────
    def load_from_folder(self, folder_path: str = DOCUMENTS_FOLDER, progress_bar=None) -> Tuple[FAISS, int, int]:

        os.makedirs(folder_path, exist_ok=True)

        file_paths = list(set(
            glob.glob(os.path.join(folder_path, "**", "*.pdf"), recursive=True) +
            glob.glob(os.path.join(folder_path, "**", "*.docx"), recursive=True)
        ))

        if not file_paths:
            raise FileNotFoundError("No PDF/DOCX files found in files/ folder")

        # Embedding model (FAST)
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )

        faiss_path = "faiss_index"
        metadata_path = "file_metadata.json"

        # ---- Load old metadata ----
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                old_files = set(json.load(f))
        else:
            old_files = set()

        current_files = set(file_paths)
        new_files = current_files - old_files

        print(f"📂 Total files: {len(current_files)}")
        print(f"🆕 New files: {len(new_files)}")

        # ---- Load existing FAISS ----
        if os.path.exists(faiss_path):
            print("⚡ Loading existing FAISS...")
            vectorstore = FAISS.load_local(
                faiss_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            print("🧠 First-time processing...")
            vectorstore = None

        new_docs: List[Document] = []

        # ---- Process ONLY new files ----
        for fp in new_files:
            fname = os.path.basename(fp)

            try:
                if fp.endswith(".pdf"):
                    text = self._extract_pdf(fp)
                else:
                    text = self._extract_docx(fp)

                # OCR fallback
                if fp.endswith(".pdf") and (not text or len(text.strip()) < 200):
                    print(f"[OCR] 🔍 {fname}")
                    text = self._extract_pdf_ocr(fp)

                if not text or len(text.strip()) < 50:
                    print(f"[Loader] ⚠️ {fname} → skipped")
                    continue

                chunks = [
                    Document(page_content=chunk, metadata={"source": fname})
                    for chunk in self.text_splitter.split_text(text)
                ]

                new_docs.extend(chunks)

                print(f"[Loader] ✅ {fname} → {len(chunks)} chunks")

            except Exception as e:
                print(f"[Loader] ❌ {fname}: {e}")

        # ---- Update FAISS ----
        if vectorstore is None:
            vectorstore = FAISS.from_documents(new_docs, embeddings)
        elif new_docs:
            print("➕ Adding new documents...")
            vectorstore.add_documents(new_docs)

        # ---- Save ----
        vectorstore.save_local(faiss_path)

        with open(metadata_path, "w") as f:
            json.dump(list(current_files), f)

        print("✅ Knowledge base ready!")

        return vectorstore, len(current_files), len(new_docs)

    # ───────────────────────────────────────────────
    # PDF extraction (FAST)
    # ───────────────────────────────────────────────
    def _extract_pdf(self, file_path: str) -> str:
        try:
            import fitz
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        except:
            return ""

    # ───────────────────────────────────────────────
    # OCR fallback
    # ───────────────────────────────────────────────
    def _extract_pdf_ocr(self, file_path: str) -> str:
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(
                file_path,
                poppler_path=r"C:\poppler-25.12.0\Library\bin"
            )

            text = ""
            for img in images:
                text += pytesseract.image_to_string(img)

            return text
        except Exception as e:
            print(f"[OCR] ❌ {e}")
            return ""

    # ───────────────────────────────────────────────
    # DOCX extraction
    # ───────────────────────────────────────────────
    def _extract_docx(self, file_path: str) -> str:
        from docx import Document as DocxDoc

        doc = DocxDoc(file_path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
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
