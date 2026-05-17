import time
from typing import List
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from backend.app.config import settings

class VectorDBService:
    def __init__(self):
        # 1. Connect to Pinecone Cloud
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # 2. Load the open-source embedding model locally
        print("Loading local embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model loaded successfully.")
        
    def create_index_if_not_exists(self, index_name: str, dimension: int = 384):
        """Creates a secure vector index in the cloud if it doesn't exist."""
        existing_indexes = [idx['name'] for idx in self.pc.list_indexes()]
        
        if index_name not in existing_indexes:
            print(f"Index '{index_name}' not found. Creating it on Pinecone Cloud...")
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            while not self.pc.describe_index(index_name).status['ready']:
                time.sleep(1)
            print(f"[SUCCESS] Index '{index_name}' is fully deployed.")
        else:
            print(f"Index '{index_name}' already exists and is active.")

    def upsert_chunks(self, index_name: str, chunks: list, namespace: str = "default"):
        """
        Converts text chunks into numerical vectors and uploads them along with
        their raw text metadata to a targeted isolated namespace partition in Pinecone.
        """
        index = self.pc.Index(index_name)
        vectors_to_upload = []
        
        print(f"Converting {len(chunks)} text chunks into mathematical vectors...")
        
        for idx, text_chunk in enumerate(chunks):
            # Check if text_chunk is a dictionary (from our ingestor update) or raw string
            # This makes sure your code is completely safe from crashing regardless of layout
            content = text_chunk["text"] if isinstance(text_chunk, dict) else text_chunk
            
            # Convert text string into a list of 384 numbers
            embedding = self.model.encode(content).tolist()
            
            # Format according to corporate production data structures
            vector_data = {
                "id": f"chunk_id_{idx}",
                "values": embedding,
                "metadata": {"text": content} # Storing raw text alongside vectors
            }
            vectors_to_upload.append(vector_data)
            
        print(f"Uploading vectors to Pinecone Cloud data nodes inside namespace: '{namespace}'...")
        
        # CRUCIAL FIX: Passing the namespace explicitly to the cloud cluster engine 🎯
        index.upsert(vectors=vectors_to_upload, namespace=namespace)
        
        print(f"[SUCCESS] Upload complete. {len(chunks)} document blocks indexed safely.")