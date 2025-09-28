#!/usr/bin/env python3
"""
Simple Hybrid RAG Amazon Agent - Semantic + Keyword Search (Corrected)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# LangChain Imports
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
# Updated import for HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def main():
    """
    Main function to run the Hybrid RAG agent.
    """
    # Load environment variables from .env file
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")

    # --- 1. SETUP PATHS ---
    # The script is in the 'agents' directory, so we go up one level for the project root.
    project_root = Path(__file__).parent.parent
    # Path where the FAISS index is stored (for semantic retriever)
    vector_store_path = project_root / "data" / "vector_data" / "amazon_customer_service_augmented"
    
    # --- 2. LOAD DOCUMENTS AND CREATE VECTOR STORE (IF NEEDED) ---
    # Initialize embeddings model
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    if not vector_store_path.exists():
        print(f"No FAISS index found at {vector_store_path}. Please run a script to create it first.")
        print("For this script to work, a FAISS index must already exist.")
        return # Exit if index doesn't exist

    # Load the existing FAISS index
    print(f"Loading existing FAISS index from {vector_store_path}...")
    vectorstore = FAISS.load_local(str(vector_store_path), embeddings, allow_dangerous_deserialization=True)
    print("Index loaded successfully.")

    # --- 3. CREATE HYBRID RETRIEVER ---
    
    # Create semantic retriever from the vector store
    semantic_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # CRITICAL FIX: Get documents from the vectorstore for the BM25 retriever
    print("Loading documents from vectorstore for keyword retriever...")
    # Get all documents from the vectorstore for BM25
    raw_documents = vectorstore.similarity_search("customer service", k=1000)  # Get many docs
    print(f"Loaded {len(raw_documents)} documents for BM25 retriever.")
    
    # Create the BM25 (keyword) retriever from the raw documents
    bm25_retriever = BM25Retriever.from_documents(raw_documents)
    bm25_retriever.k = 5

    # Create the hybrid ensemble retriever
    hybrid_retriever = EnsembleRetriever(
        retrievers=[semantic_retriever, bm25_retriever],
        weights=[0.7, 0.3]  # 70% semantic, 30% keyword
    )
    print("Hybrid retriever created.")

    # --- 4. INITIALIZE LLM ---
    llm = ChatGroq(
        groq_api_key=groq_api_key,
        # CORRECTED MODEL: Switched to a current, powerful production model
        model_name="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=1024 # Increased tokens slightly for longer protocols
    )

    # --- 5. CREATE THE RAG CHAIN using LCEL ---
    prompt_template = """
You are an expert Amazon customer service agent. Your task is to synthesize a protocol for a text-based AI agent to follow.

CONTEXT of potential resolution steps:
{context}

CUSTOMER QUERY:
{question}

INSTRUCTIONS:
- Review all the potential protocols in the context and create a single, clear, step-by-step resolution plan that best addresses the customer's query.
- The final protocol MUST be something a text-based AI agent can perform.
- EXCLUDE any steps that require human actions like making phone calls, video calls, or physical actions.
- If the context contains relevant steps, synthesize them into a final protocol.
- If the information is NOT in the context, you MUST respond with: "The protocol for this query is not available in the provided documents."
- Do NOT make up any information. Your response must be strictly based on the context provided.

AI-COMPATIBLE AMAZON CUSTOMER SERVICE PROTOCOL:"""

    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    # Helper function to format documents by extracting ONLY resolution steps
    def format_docs(docs):
        """
        Extracts only the resolution steps from each document to create a cleaner,
        more focused context for the LLM.
        """
        formatted_steps = []
        for i, doc in enumerate(docs):
            content = doc.page_content
            # Find the "Resolution Steps:" marker and extract everything after it
            if "Resolution Steps:" in content:
                steps = content.split("Resolution Steps:", 1)[1].strip()
                formatted_steps.append(f"--- Potential Protocol Option {i+1} ---\n{steps}")
        
        # If no documents with resolution steps were found, return a clear message
        if not formatted_steps:
            return "No specific resolution steps were found in the retrieved documents."
            
        return "\n\n".join(formatted_steps)

    # Define the final part of the chain that generates the response
    generation_chain = (
        prompt
        | llm
        | StrOutputParser()
    )
    print("RAG chain created. Ready for queries.")
    
    # --- 6. GET USER QUERY AND INVOKE CHAIN ---
    try:
        while True:
            query = input("\nEnter customer query (or type 'exit' to quit): ").strip()
            if query.lower() == 'exit':
                break
            if not query:
                continue

            print("\n...Searching for protocol...")
            
            # --- DEBUGGING: Print retrieved docs from each retriever ---
            
            # 1. Get and print semantic results (using .invoke())
            semantic_docs = semantic_retriever.invoke(query)
            print("\n--- SEMANTIC SEARCH RESULTS (Top 5) ---")
            for i, doc in enumerate(semantic_docs):
                print(f"[{i+1}] {doc.page_content[:180].strip()}...")
            print("---------------------------------------\n")

            # 2. Get and print keyword results (using .invoke())
            bm25_docs = bm25_retriever.invoke(query)
            print("\n--- KEYWORD SEARCH RESULTS (Top 5) ---")
            for i, doc in enumerate(bm25_docs):
                print(f"[{i+1}] {doc.page_content[:180].strip()}...")
            print("------------------------------------\n")

            # 3. Get the final hybrid results (using .invoke())
            hybrid_docs = hybrid_retriever.invoke(query)
            print("\n--- HYBRID RETRIEVER FINAL RESULTS (used for context) ---")
            for i, doc in enumerate(hybrid_docs):
                print(f"[{i+1}] {doc.page_content[:180].strip()}...")
            print("---------------------------------------------------------\n")
            
            # Format the final context from the hybrid results using our new function
            final_context = format_docs(hybrid_docs)
            
            # Get response from the generation part of the chain
            response = generation_chain.invoke({"context": final_context, "question": query})
            
            # Print protocol
            print("\n--- RECOMMENDED PROTOCOL ---")
            print(response)
            print("--------------------------\n")

    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()

