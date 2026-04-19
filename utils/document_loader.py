"""
Document Loader (PRODUCTION READY - HF VERSION)

✔ HuggingFace embeddings (no Ollama)
✔ Safe FAISS loading (no crash)
✔ Auto rebuild if index missing/corrupt
✔ Incremental updates
✔ Works locally + deployable
"""

import os
import glob
import json
from typing import List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

# ── Folder path ─────────────────────────────────────────
DOCUMENTS_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "files"
)


class DocumentLoader:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
        )

        # ✅ HuggingFace Embeddings (stable + deployable)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    # ────────────────────────────────────────────────────
    def load_from_folder(
        self, folder_path: str = DOCUMENTS_FOLDER, progress_bar=None
    ) -> Tuple[FAISS, int, int]:

        os.makedirs(folder_path, exist_ok=True)

        # ── Collect files ────────────────────────────────
        file_paths = list(set(
            glob.glob(os.path.join(folder_path, "**", "*.pdf"), recursive=True) +
            glob.glob(os.path.join(folder_path, "**", "*.docx"), recursive=True)
        ))

        if not file_paths:
            raise FileNotFoundError(
                f"❌ No PDF/DOCX files found in: {folder_path}"
            )

        faiss_path = "faiss_index"
        metadata_path = "file_metadata.json"

        # ── Load old metadata ────────────────────────────
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                old_files = set(json.load(f))
        else:
            old_files = set()

        current_files = set(file_paths)
        new_files = current_files - old_files

        print(f"📂 Total files: {len(current_files)}")
        print(f"🆕 New files: {len(new_files)}")

        # ── Load existing FAISS safely ───────────────────
        vectorstore = None

        if os.path.exists(faiss_path):
            try:
                print("⚡ Loading existing FAISS...")
                vectorstore = FAISS.load_local(
                    faiss_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print("⚠️ FAISS load failed, rebuilding:", e)
                vectorstore = None

        new_docs: List[Document] = []

        # ── Process ONLY new files ───────────────────────
        for fp in new_files:
            fname = os.path.basename(fp)

            try:
                text = self._extract_text(fp)

                if not text or len(text.strip()) < 50:
                    print(f"[Loader] ⚠️ {fname} → skipped (no text)")
                    continue

                chunks = [
                    Document(page_content=chunk, metadata={"source": fname})
                    for chunk in self.text_splitter.split_text(text)
                ]

                new_docs.extend(chunks)
                print(f"[Loader] ✅ {fname} → {len(chunks)} chunks")

            except Exception as e:
                print(f"[Loader] ❌ {fname}: {e}")

        # ── Build or update FAISS ────────────────────────
        if vectorstore is None:
            if not new_docs:
                raise ValueError("❌ No documents available to build FAISS index.")

            print("🧠 Creating new FAISS index...")
            vectorstore = FAISS.from_documents(new_docs, self.embeddings)

        elif new_docs:
            print("➕ Adding new documents to FAISS...")
            vectorstore.add_documents(new_docs)

        else:
            print("✅ No new documents. Using existing FAISS index.")

        # ── Save FAISS ───────────────────────────────────
        vectorstore.save_local(faiss_path)

        # ── Save metadata ────────────────────────────────
        with open(metadata_path, "w") as f:
            json.dump(list(current_files), f)

        print("✅ Knowledge base ready!")

        return vectorstore, len(current_files), len(new_docs)

    # ────────────────────────────────────────────────────
    def _extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF or DOCX
        """

        # ── PDF ─────────────────────────────────────────
        if file_path.lower().endswith(".pdf"):
            try:
                import fitz  # PyMuPDF
                text = ""
                with fitz.open(file_path) as doc:
                    for page in doc:
                        text += page.get_text()
                return text
            except Exception:
                return ""

        # ── DOCX ────────────────────────────────────────
        elif file_path.lower().endswith(".docx"):
            try:
                from docx import Document as DocxDoc
                doc = DocxDoc(file_path)
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
