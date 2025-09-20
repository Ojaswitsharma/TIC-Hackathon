"""
Configuration file for Company Knowledge Base

Modify these settings to customize the knowledge base behavior.
"""

# Embedding Configuration
EMBEDDING_CONFIG = {
    # Options: "sentence-transformer" or "openai"
    "model_type": "sentence-transformer",
    
    # Model names for different embedding types
    "sentence_transformer_models": {
        "fast": "all-MiniLM-L6-v2",           # Fast and efficient
        "balanced": "all-mpnet-base-v2",      # Better quality, slower
        "quality": "all-distilroberta-v1"     # Good balance
    },
    
    "openai_models": {
        "standard": "text-embedding-ada-002",
        "small": "text-embedding-3-small",
        "large": "text-embedding-3-large"
    },
    
    # Default model selection
    "default_sentence_model": "fast",
    "default_openai_model": "standard"
}

# Document Processing Configuration
DOCUMENT_CONFIG = {
    # Text chunking parameters
    "chunk_size": 1000,
    "chunk_overlap": 200,
    
    # Supported file extensions
    "supported_extensions": [".pdf", ".txt", ".md", ".docx"],
    
    # Document directories
    "document_directories": [
        "documents/",
        "docs/",
        "knowledge/"
    ],
    
    # Text splitter configuration
    "separators": ["\n\n", "\n", " ", ""],
    "length_function": "len"
}

# Vector Store Configuration
VECTOR_CONFIG = {
    # Default index path
    "default_index_path": "company_kb_index",
    
    # Search parameters
    "default_search_results": 5,
    "similarity_threshold": 0.8,  # For filtering results
    
    # FAISS configuration
    "faiss_index_type": "IndexFlatIP",  # Inner Product similarity
    "normalize_embeddings": True
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "log_to_file": False,
    "log_file_path": "knowledge_base.log"
}

# Decision Engine Integration
DECISION_CONFIG = {
    # Context retrieval settings
    "max_context_documents": 5,
    "context_relevance_threshold": 0.7,
    
    # Query enhancement
    "expand_queries": True,
    "query_synonyms": {
        "policy": ["procedure", "rule", "guideline"],
        "remote work": ["work from home", "telecommute", "WFH"],
        "time off": ["vacation", "leave", "PTO", "holiday"],
        "training": ["learning", "development", "education"],
        "benefits": ["perks", "compensation", "package"]
    }
}

# Performance Settings
PERFORMANCE_CONFIG = {
    # Embedding batch size
    "embedding_batch_size": 32,
    
    # Memory management
    "max_documents_in_memory": 1000,
    "enable_gpu": False,  # Set to True if GPU available
    
    # Caching
    "cache_embeddings": True,
    "cache_directory": ".embeddings_cache"
}

# File type specific settings
FILE_TYPE_CONFIG = {
    "pdf": {
        "loader_class": "PyPDFLoader",
        "extract_images": False,
        "password": None
    },
    
    "txt": {
        "loader_class": "TextLoader",
        "encoding": "utf-8",
        "autodetect_encoding": True
    },
    
    "md": {
        "loader_class": "TextLoader", 
        "encoding": "utf-8",
        "preserve_formatting": True
    },
    
    "docx": {
        "loader_class": "Docx2txtLoader",
        "extract_tables": True
    }
}
