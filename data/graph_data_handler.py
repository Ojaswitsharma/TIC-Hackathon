import os
import json
from pathlib import Path
import time
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_community.vectorstores.neo4j_vector import Neo4jVector
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# 1. Neo4j Credentials from your text file
NEO4J_URI = ""
NEO4J_USERNAME = ""
NEO4J_PASSWORD = ""

# 2. Groq LLM API Key is now loaded from the .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 3. Data Directory
DATA_DIR = Path("cc_daaset")

# 4. Embeddings Model for In-Graph Vectors
HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# --- Main Script ---
# Check if the API Key was loaded successfully
if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY not found. Please create a .env file and add it.")
    exit()

# Initialize connections
try:
    print("Connecting to Neo4j...")
    graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    print("✅ Successfully connected to Neo4j.")
except Exception as e:
    print(f"❌ Failed to connect to Neo4j. Error: {e}")
    exit()

# --- 1. Prepare the Database (Indexes for Optimization) ---
try:
    graph.query("CREATE INDEX IF NOT EXISTS entity_id_index FOR (e:__Entity__) ON (e.id)")
    print("✅ Ensured standard property index exists for faster queries.")
except Exception as e:
    print(f"⚠️ Warning: Could not create standard index. Error: {e}")

embeddings = HuggingFaceEmbeddings(model_name=HF_MODEL)

try:
    neo4j_vector_store = Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        index_name="node_vectors",
        node_label="__Entity__",
        text_node_properties=['id'],
        embedding_node_property='embedding',
    )
    print("✅ Ensured in-graph vector index is ready for semantic search.")
except Exception as e:
    print(f"⚠️ Warning: Could not create vector index. Error: {e}")

# --- 2. Initialize AI Tools ---
llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="Gemma2-9b-It")
llm_transformer = LLMGraphTransformer(llm=llm)

# --- 3. Process Files and Populate the Graph ---
jsonl_files = list(DATA_DIR.glob("*.jsonl"))

if not jsonl_files:
    print(f"❌ No .jsonl files found in the '{DATA_DIR}' directory.")
else:
    for file_path in jsonl_files:
        print(f"\n--- Processing file: {file_path.name} ---")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                try:
                    record = json.loads(line)
                    content = (
                        f"A customer had a query about '{record.get('category', 'unknown category')}'. "
                        f"The query was: '{record.get('customer_query', '')}'. "
                        f"The resolution was: '{record.get('resolution_steps', '')}'."
                    )
                    doc = Document(page_content=content)
                    
                    graph_documents = llm_transformer.convert_to_graph_documents([doc])
                    graph.add_graph_documents(graph_documents)
                    
                    node_docs_for_embedding = [Document(page_content=node.id) for doc in graph_documents for node in doc.nodes]
                    if node_docs_for_embedding:
                        neo4j_vector_store.add_documents(node_docs_for_embedding)
                    
                    print(f"  > Processed record {i+1}: Added structure to graph and nodes to vector index.")

                except Exception as e:
                    print(f"  > ❌ Error processing record {i+1}: {e}")
                
                time.sleep(1)

print("\nKnowledge graph creation and optimization complete! 🚀")
