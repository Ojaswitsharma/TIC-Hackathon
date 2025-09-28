#!/usr/bin/env python3
"""
Simplified vector store builder using LangChain and HuggingFace embeddings.

Usage:
  - Place JSONL files in ./cc_daaset/
  - Run: python vector_daabase_handler.py
Outputs:
  - vector_data/<dataset_stem>/  (FAISS index + metadata.json)
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("vector_daabase_handler")

DATA_DIR = Path("cc_daaset")
VECTOR_DIR = Path("vector_data")
VECTOR_DIR.mkdir(exist_ok=True)

# HuggingFace embeddings model
HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Text splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", "!", "?", ",", " "],
)

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file into list of dicts."""
    data = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    logger.info("Loaded %d records from %s", len(data), file_path.name)
    return data

def records_to_documents(records: List[Dict[str, Any]], source_name: str) -> List[Document]:
    """Convert records into LangChain Documents with minimal metadata."""
    docs = []
    for i, rec in enumerate(records):
        text_parts = []
        if rec.get("customer_query"):
            text_parts.append(f"Customer Query: {rec['customer_query']}")
        if rec.get("resolution_steps"):
            text_parts.append(f"Resolution Steps: {rec['resolution_steps']}")
        if rec.get("category"):
            text_parts.append(f"Category: {rec['category']}")

        content = "\n\n".join(text_parts).strip()
        if content:
            docs.append(Document(page_content=content, metadata={"source": source_name, "id": i}))
    return docs

def build_vectorstore_for_file(file_path: Path, embeddings):
    """Build FAISS vectorstore for a single JSONL file."""
    records = load_jsonl(file_path)
    if not records:
        logger.warning("No records found in %s", file_path.name)
        return

    docs = records_to_documents(records, file_path.name)
    if not docs:
        logger.warning("No documents created for %s", file_path.name)
        return

    # Split into chunks
    chunks = splitter.split_documents(docs)

    # Build FAISS index
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # Save vectorstore
    out_dir = VECTOR_DIR / file_path.stem
    out_dir.mkdir(exist_ok=True)
    vectorstore.save_local(str(out_dir))
    logger.info("Saved vectorstore to %s", out_dir)

    # Save metadata
    metadata = {
        "source_file": file_path.name,
        "num_records": len(records),
        "num_documents": len(docs),
        "num_chunks": len(chunks),
        "embedding_model": HF_MODEL,
    }
    with (out_dir / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

def main():
    # Initialize embeddings here to handle import errors gracefully
    try:
        logger.info("Initializing HuggingFace embeddings...")
        embeddings = HuggingFaceEmbeddings(model_name=HF_MODEL)
        logger.info("Successfully initialized embeddings with model: %s", HF_MODEL)
    except ImportError as e:
        logger.error("Failed to import required packages: %s", e)
        logger.error("Please install missing packages with: pip install sentence-transformers torch")
        return
    except Exception as e:
        logger.error("Failed to initialize embeddings: %s", e)
        return
    
    files = list(DATA_DIR.glob("*.jsonl"))
    if not files:
        logger.warning("No JSONL files found in %s", DATA_DIR)
        return

    for f in files:
        build_vectorstore_for_file(f, embeddings)

    logger.info("All vectorstores created in %s", VECTOR_DIR)

if __name__ == "__main__":
    main()
