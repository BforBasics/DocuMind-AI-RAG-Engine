from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
from backend.app.services.ingestor import DocumentIngestor
from backend.app.services.vector_db import VectorDBService
from backend.app.config import settings
from groq import Groq
import os

router = APIRouter(prefix="/api", tags=["Document Intelligence"])
db_service = VectorDBService()
ingestor = DocumentIngestor(chunk_size=500, chunk_overlap=50)
ai_brain = Groq(api_key=settings.GROQ_API_KEY)

TARGET_INDEX_NAME = "documind-index"

class ChatMessageSchema(BaseModel):
    role: str
    content: str

# Added file_id to target specific file namespaces
class ChatRequest(BaseModel):
    question: str
    file_id: str 
    history: List[ChatMessageSchema] = []

class ChatResponse(BaseModel):
    answer: str
    confidence_score: float

class IngestRequest(BaseModel):
    file_path: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_document(payload: ChatRequest):
    """
    RAG Chat endpoint with targeted namespace querying to prevent multi-document bleeding.
    """
    try:
        # Step 1: Optimize the user's raw question using Groq
        OPTIMIZATION_PROMPT = (
            "You are an expert search engine optimizer.\n"
            "Analyze the user's query and output ONLY 3 to 5 core technical keywords "
            "or phrases that would likely appear in a formal resume or project document to answer this query.\n"
            "Do not add any conversational text. Output only the search terms.\n\n"
            f"User Query: {payload.question}"
        )
        
        rewriter_completion = ai_brain.chat.completions.create(
            messages=[{"role": "user", "content": OPTIMIZATION_PROMPT}],
            model="llama-3.1-8b-instant",
            temperature=0.0
        )
        optimized_search_string = rewriter_completion.choices[0].message.content.strip()
        
        # Calculate embedding vector
        query_vector = db_service.model.encode(optimized_search_string).tolist()
        
        # Step 2: Target the specific document namespace folder in Pinecone
        index = db_service.pc.Index(TARGET_INDEX_NAME)
        search_results = index.query(
            vector=query_vector, 
            top_k=3, 
            include_metadata=True,
            namespace=payload.file_id # ISOLATION ACTIVATED HERE 🎯
        )
        
        if not search_results['matches']:
            return ChatResponse(answer="I couldn't find any relevant details inside this specific document.", confidence_score=0.0)
            
        compiled_context_chunks = [match['metadata']['text'] for match in search_results['matches']]
        context_text = "\n\n---\n\n".join(compiled_context_chunks)
        confidence = round(search_results['matches'][0]['score'] * 100, 2)
        
        # Step 3: Synthesis with LLM
        SYSTEM_PROMPT = (
            "You are an elite corporate recruitment assistant for DocuMind AI.\n"
            "Answer the user's question accurately using ONLY the provided facts below.\n"
            "Use the conversation history to track subject context and pronouns smoothly.\n"
            "If the answer cannot be found in the facts, say 'I cannot find that specific detail.'\n\n"
            f"--- SOURCE FACTS FROM FILE [{payload.file_id}] ---\n{context_text}\n--------------"
        )
        
        messages_for_llm = [{"role": "system", "content": SYSTEM_PROMPT}]
        for past_msg in payload.history:
            clean_content = past_msg.content.split("\n\n`📊 Match Confidence:")[0]
            messages_for_llm.append({"role": past_msg.role, "content": clean_content})
            
        messages_for_llm.append({"role": "user", "content": payload.question})
        
        chat_completion = ai_brain.chat.completions.create(
            messages=messages_for_llm,
            model="llama-3.1-8b-instant",
            temperature=0.2
        )
        
        return ChatResponse(
            answer=chat_completion.choices[0].message.content,
            confidence_score=confidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Accepts a raw binary file stream from any network device (PC/Mobile),
    extracts text chunks in-memory, and upserts them to an isolated Pinecone namespace.
    """
    try:
        # 1. Automatically extract the filename to use as our unique Namespace ID
        file_id = file.filename.lower().replace(" ", "_")
        
        # 2. Read the binary stream from the network request
        file_bytes = await file.read()
        
        # 3. Extract text from the binary stream directly in memory
        raw_text = ingestor.extract_text_from_pdf(file_bytes)
        if not raw_text.strip():
            # Premium Error Context Update 🎯
            raise HTTPException(
                status_code=400, 
                detail="The uploaded PDF cannot be read. The file might be scanned, image-only, or corrupted. Please upload a digitally selectable PDF."
            )
            
        chunks = ingestor.create_chunks(raw_text)
        
        # 4. Initialize index and push vectors to the isolated cloud namespace
        db_service.create_index_if_not_exists(index_name=TARGET_INDEX_NAME, dimension=384)
        db_service.upsert_chunks(index_name=TARGET_INDEX_NAME, chunks=chunks, namespace=file_id)
        
        return {
            "status": "success", 
            "message": f"Successfully loaded {len(chunks)} blocks into private namespace: '{file_id}'",
            "file_id": file_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))