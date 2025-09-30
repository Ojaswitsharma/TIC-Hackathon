An intelligent, **voice-enabled customer service system** that combines **Hybrid RAG (Retrieval-Augmented Generation)**, **LangGraph workflows**, and **multi-modal AI** to provide automated customer support for multiple companies (Amazon, Facebook, Apple).

## 🏆 **Key Features**

- 🗣️ **Voice Interaction**: Speech-to-text (Whisper) + Text-to-speech (Google TTS/Murf)
- 🧠 **Hybrid RAG**: Combines semantic search (FAISS) + keyword search (BM25)
- 🔄 **LangGraph Workflows**: Sophisticated AI orchestration with state management
- 🏢 **Multi-Company Support**: Specialized agents for Amazon, Facebook, and Apple
- 📊 **Knowledge Graphs**: Optional Neo4j integration for advanced analytics
- ⚡ **Fast LLM**: Powered by Groq's lightning-fast Llama 3.3 70B model

## 🏗️ **System Architecture**

```
    A[🎤 Customer Voice Input] --> B[🔍 Listener Node]
    B --> C[📋 7-Question Interview]
    C --> D[🤖 LLM Data Extraction]
    D --> E{🔀 Company Routing}
    
    E --> F[🛒 Amazon Agent]
    E --> G[📘 Facebook Agent]
    E --> H[🍎 Apple Agent]
    
    F --> I[🔍 Hybrid RAG Retrieval]
    G --> I
    H --> I
    
    I --> J[📝 Protocol Generation]
    J --> K[🎯 Execution Node]
    K --> L[🔊 Voice Response]
    
    M[(📚 Vector Store<br/>FAISS + BM25)] --> I
    N[(🧠 Knowledge Graph<br/>Neo4j)] -.-> I
```

## 📁 **Project Structure**

```
TIC-Hackathon/
├── 🎯 workflow/                    # LangGraph orchestration system
│   ├── workflow.py                 # Main workflow controller
│   └── nodes.py                    # Individual workflow nodes
├── 🤖 agents/                      # RAG-powered customer agents
│   ├── agent.py                    # Standalone hybrid RAG agent
│   └── requirements.txt            # Agent-specific dependencies
├── 📊 data/                        # Knowledge base and processing
│   ├── cc_daaset/                  # Customer service datasets
│   │   ├── amazon_customer_service_augmented.jsonl    # 1,208 Amazon cases
│   │   └── facebook_customer_service_augmented.jsonl  # 1,008 Facebook cases
│   ├── vector_data/                # Pre-built FAISS indexes
│   │   ├── amazon_customer_service_augmented/
│   │   └── facebook_customer_service_augmented/
│   ├── vector_daabase_handler.py   # Vector store builder
│   ├── graph_data_handler.py       # Neo4j knowledge graph creator
│   └── analyze_neo4j.py            # Database analysis tools
├── 📚 reference/                   # Examples and documentation
│   └── krish_naik_graphdb.ipynb    # Neo4j tutorial notebook
├── requirements.txt                # Main dependencies
└── .env.template                   # Environment variables template
```
