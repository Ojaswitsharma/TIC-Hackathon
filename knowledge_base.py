"""
Company Knowledge Base for Decision Engine

This module handles loading, processing, and indexing company documents
for fast similarity search and retrieval in decision-making processes.

Goals:
- Load company-specific procedural documents, FAQs, policies
- Preprocess documents: text extraction, cleaning, chunking
- Generate embeddings using sentence transformers or LLM embeddings
- Store embeddings in a vector database for fast similarity search

Author: Assistant
Date: September 20, 2025
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Union
import warnings
warnings.filterwarnings('ignore')

# Document loading and processing
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# Embeddings - using sentence transformers as default (free alternative to OpenAI)
from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

# Optional: OpenAI embeddings (requires API key)
try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddings(Embeddings):
    """Wrapper for SentenceTransformer to work with LangChain"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        embedding = self.model.encode([text])
        return embedding[0].tolist()


class CompanyKnowledgeBase:
    """
    Company Knowledge Base processor for Decision Engine
    
    Handles document loading, processing, and vector indexing for
    fast similarity search during decision-making queries.
    """
    
    def __init__(self, 
                 embedding_model: str = "sentence-transformer",
                 model_name: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 auto_load: bool = True):
        """
        Initialize the Knowledge Base processor
        
        Args:
            embedding_model: "sentence-transformer" or "openai"
            model_name: Model name for embeddings
            chunk_size: Size of document chunks for processing
            chunk_overlap: Overlap between chunks
            auto_load: Whether to automatically load documents and vector store
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents = []
        self.vector_store = None
        
        # Initialize embeddings
        self.embeddings = self._initialize_embeddings(embedding_model, model_name)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Auto-load documents and vector store if requested
        if auto_load:
            self._auto_initialize()
    
    def _initialize_embeddings(self, embedding_model: str, model_name: str):
        """Initialize the embedding model"""
        if embedding_model == "openai":
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI not available, falling back to sentence-transformer")
                return SentenceTransformerEmbeddings(model_name)
            
            # Check for OpenAI API key
            if not os.getenv("OPENAI_API_KEY"):
                logger.warning("OPENAI_API_KEY not set, falling back to sentence-transformer")
                return SentenceTransformerEmbeddings(model_name)
            
            return OpenAIEmbeddings(model=model_name)
        
        else:  # sentence-transformer
            return SentenceTransformerEmbeddings(model_name)
    
    def _auto_initialize(self):
        """Automatically initialize the knowledge base with documents and vector store"""
        # Check for new or changed files
        documents_dir = Path("documents")
        current_files = set()
        
        if documents_dir.exists():
            # Find all supported document files
            for pattern in ["*.txt", "*.md", "*.pdf", "*.csv"]:
                current_files.update(documents_dir.glob(pattern))
        
        # Try to load existing vector store first
        index_path = "company_kb_index"
        should_rebuild = False
        
        if Path(index_path).exists():
            logger.info(f"Found existing vector index at {index_path}")
            
            # Check if we need to rebuild due to new files
            index_time = Path(index_path).stat().st_mtime
            for file_path in current_files:
                if file_path.stat().st_mtime > index_time:
                    logger.info(f"New or modified file detected: {file_path}")
                    should_rebuild = True
                    break
            
            if not should_rebuild and self.load_index(index_path):
                logger.info("Successfully loaded existing vector index")
                # Also load the original documents for reference
                self._load_original_documents()
                return
            else:
                logger.info("Rebuilding vector index due to new/modified files...")
        
        # If no existing index or rebuild needed, load documents and create new vector store
        if not should_rebuild:
            logger.info("No existing vector index found, creating new one...")
        
        if documents_dir.exists() and current_files:
            logger.info(f"Found {len(current_files)} document files")
            documents = self.load_documents(list(current_files))
            if documents:
                split_docs = self.split_documents(documents)
                if split_docs:
                    self.create_vector_index(split_docs)
                    self.save_index(index_path)
                    logger.info(f"Created and saved new vector index with {len(split_docs)} chunks")
                else:
                    logger.warning("No document chunks created")
            else:
                logger.warning("No documents loaded")
        else:
            logger.warning("No supported document files found in documents/ directory")
    
    def _load_original_documents(self):
        """Load the original documents for reference"""
        documents_dir = Path("documents")
        if documents_dir.exists():
            file_paths = []
            for pattern in ["*.txt", "*.md", "*.pdf", "*.csv"]:
                file_paths.extend(documents_dir.glob(pattern))
            
            if file_paths:
                logger.info(f"Loading {len(file_paths)} original documents for reference")
                self.load_documents(file_paths)
            else:
                logger.warning("No document files found for loading")
    
    def load_documents(self, file_paths: List[Union[str, Path]]) -> List:
        """
        Load and extract text from document files
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            List of loaded documents
        """
        documents = []
        
        for path in file_paths:
            path = Path(path)
            
            if not path.exists():
                logger.warning(f"File not found: {path}")
                continue
            
            # Check file size (warn about large files)
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > 50:  # Warn about files larger than 50MB
                logger.warning(f"Large file detected: {path} ({file_size_mb:.1f}MB). Processing may be slow.")
                # For very large CSV files, only process first part
                if path.suffix.lower() == ".csv" and file_size_mb > 20:
                    logger.info(f"Large CSV file detected. Processing first 1000 rows only.")
                    try:
                        # Read first 1000 rows of CSV
                        import csv
                        with open(path, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            header = next(reader, None)
                            rows = [header] if header else []
                            for i, row in enumerate(reader):
                                if i >= 999:  # 1000 rows total including header
                                    break
                                rows.append(row)
                        
                        # Convert to text format
                        text_content = "\\n".join([",".join(row) for row in rows])
                        
                        # Create a document object manually
                        from langchain.schema import Document
                        doc = Document(page_content=text_content, metadata={"source": str(path)})
                        documents.append(doc)
                        logger.info(f"Loaded 1000 rows from large CSV {path}")
                        continue
                        
                    except Exception as e:
                        logger.error(f"Error processing large CSV {path}: {e}")
                        continue
            
            try:
                if path.suffix.lower() == ".pdf":
                    loader = PyPDFLoader(str(path))
                elif path.suffix.lower() in [".txt", ".md"]:
                    loader = TextLoader(str(path), encoding='utf-8')
                elif path.suffix.lower() == ".csv":
                    # For normal-sized CSV files, use text loader
                    loader = TextLoader(str(path), encoding='utf-8')
                else:
                    logger.warning(f"Unsupported file type: {path.suffix}")
                    continue
                
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Loaded {len(docs)} documents from {path}")
                
            except Exception as e:
                logger.error(f"Error loading {path}: {e}")
                continue
        
        self.documents = documents
        return documents
    
    def split_documents(self, documents: Optional[List] = None) -> List:
        """
        Split documents into smaller chunks for embedding
        
        Args:
            documents: List of documents to split (uses self.documents if None)
            
        Returns:
            List of document chunks (limited to reasonable size)
        """
        if documents is None:
            documents = self.documents
        
        if not documents:
            logger.warning("No documents to split")
            return []
        
        all_split_docs = []
        max_chunks_per_file = 200  # Limit chunks per file
        
        for doc in documents:
            # Split individual document
            doc_chunks = self.text_splitter.split_documents([doc])
            
            # Limit chunks if too many
            if len(doc_chunks) > max_chunks_per_file:
                logger.warning(f"Document {doc.metadata.get('source', 'unknown')} has {len(doc_chunks)} chunks. Limiting to first {max_chunks_per_file}.")
                doc_chunks = doc_chunks[:max_chunks_per_file]
            
            all_split_docs.extend(doc_chunks)
        
        logger.info(f"Split {len(documents)} documents into {len(all_split_docs)} chunks")
        
        return all_split_docs
    
    def create_vector_index(self, split_docs: Optional[List] = None) -> FAISS:
        """
        Create a vector store with embeddings for retrieval
        
        Args:
            split_docs: List of document chunks (splits all documents if None)
            
        Returns:
            FAISS vector store
        """
        if split_docs is None:
            split_docs = self.split_documents()
        
        if not split_docs:
            logger.error("No documents to index")
            return None
        
        try:
            logger.info(f"Creating embeddings for {len(split_docs)} document chunks...")
            self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
            logger.info("Vector index created successfully")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector index: {e}")
            return None
    
    def save_index(self, index_path: str = "company_kb_index"):
        """
        Save the vector index to disk
        
        Args:
            index_path: Path to save the index
        """
        if self.vector_store is None:
            logger.error("No vector store to save")
            return False
        
        try:
            self.vector_store.save_local(index_path)
            logger.info(f"Vector index saved to {index_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False
    
    def load_index(self, index_path: str = "company_kb_index"):
        """
        Load a vector index from disk
        
        Args:
            index_path: Path to load the index from
        """
        try:
            self.vector_store = FAISS.load_local(
                index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"Vector index loaded from {index_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def search_similar(self, query: str, k: int = 5) -> List:
        """
        Search for similar documents
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        if self.vector_store is None:
            logger.error("No vector store available for search")
            return []
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"Found {len(results)} similar documents for query: '{query[:50]}...'")
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def search_with_scores(self, query: str, k: int = 5) -> List:
        """
        Search for similar documents with similarity scores
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        if self.vector_store is None:
            logger.error("No vector store available for search")
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.info(f"Found {len(results)} similar documents for query: '{query[:50]}...'")
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def process_documents(self, file_paths: List[Union[str, Path]], 
                         save_index: bool = True,
                         index_path: str = "company_kb_index") -> bool:
        """
        Complete pipeline: load, split, index, and optionally save documents
        
        Args:
            file_paths: List of document file paths
            save_index: Whether to save the index to disk
            index_path: Path to save the index
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load documents
            documents = self.load_documents(file_paths)
            if not documents:
                logger.error("No documents loaded")
                return False
            
            # Split documents
            split_docs = self.split_documents(documents)
            if not split_docs:
                logger.error("No document chunks created")
                return False
            
            # Create vector index
            vector_store = self.create_vector_index(split_docs)
            if vector_store is None:
                logger.error("Failed to create vector index")
                return False
            
            # Save index if requested
            if save_index:
                self.save_index(index_path)
            
            logger.info("Document processing completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in document processing pipeline: {e}")
            return False
    
    def get_document_count(self) -> int:
        """Get the number of loaded documents"""
        return len(self.documents) if self.documents else 0
    
    def get_chunk_count(self) -> int:
        """Get the number of document chunks in vector store"""
        if self.vector_store and hasattr(self.vector_store, 'index'):
            return self.vector_store.index.ntotal
        return 0


def main():
    """Example usage and testing"""
    logger.info("Starting Company Knowledge Base creation...")
    
    # Initialize knowledge base
    kb = CompanyKnowledgeBase(
        embedding_model="sentence-transformer",  # Free alternative to OpenAI
        model_name="all-MiniLM-L6-v2",  # Good balance of speed and quality
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # Example file paths (will be created in the next step)
    files = [
        "documents/company_guide.pdf",
        "documents/faqs.txt",
        "documents/policies.txt",
        "documents/procedures.md"
    ]
    
    # Process documents
    success = kb.process_documents(files, save_index=True, index_path="company_kb_index")
    
    if success:
        logger.info("Knowledge base created successfully!")
        
        # Example search
        query = "What are the company policies on remote work?"
        results = kb.search_similar(query, k=3)
        
        print(f"\nSearch results for: '{query}'")
        print("=" * 50)
        for i, doc in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"Content: {doc.page_content[:200]}...")
            print(f"Metadata: {doc.metadata}")
    
    else:
        logger.error("Failed to create knowledge base")


if __name__ == "__main__":
    main()
