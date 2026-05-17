# DocuMind AI - Corporate Multi-Tenant RAG Engine

A production-grade, decoupled Retrieval-Augmented Generation (RAG) architecture that allows cross-platform users to stream PDF documents over the network and interact with them in completely isolated cloud sessions.

## 🛠️ Tech Stack & Architecture
- **Frontend:** Streamlit (Python-based cross-platform UI handling multipart form-data network streaming)
- **Backend:** FastAPI (Asynchronous microservices REST API architecture)
- **Vector Database:** AWS Pinecone Cloud Cluster Nodes
- **LLM Brain Layer:** Groq Cloud Nodes (Llama 3.1 Inference Engine)
- **Embeddings:** HuggingFace `all-MiniLM-L6-v2` (Local pipeline execution)

## 🧠 Advanced Features Engineered
1. **Multi-Tenant Partitioning:** Leverages Pinecone Namespaces to segment distinct document vector spaces dynamically, preventing context bleeding.
2. **Query Optimization Layer:** Utilizes an LLM rewriter to process raw, conversational user strings into hyper-focused keyword targets before executing vector math.
3. **Rolling Conversational Memory:** Implements full multi-turn dialogue context matrices to resolve subject tracking and ambiguous pronouns across continuous chat streams.
4. **Network Streaming Engine:** Architected to handle raw binary byte buffers in-memory, allowing direct document uploads from both Mobile and PC devices.
