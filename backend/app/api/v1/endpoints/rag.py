"""
AIEco - RAG (Retrieval Augmented Generation) Endpoints
Document ingestion, vector search, and RAG queries
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
import structlog

from app.api.v1.deps import get_current_user, get_llm_client
from app.core.llm import LLMClient
from app.services.rag import RAGService, get_rag_service
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


# ===== Request/Response Models =====

class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="Search query")
    collection: str = Field(default="default", description="Document collection")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    include_sources: bool = Field(default=True, description="Include source citations")
    generate_answer: bool = Field(default=True, description="Generate AI answer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "How does the authentication system work?",
                "collection": "documentation",
                "top_k": 5
            }
        }


class DocumentChunk(BaseModel):
    id: str
    content: str
    source: str
    page: Optional[int] = None
    score: float
    metadata: dict = {}


class RAGQueryResponse(BaseModel):
    query: str
    answer: Optional[str] = None
    sources: List[DocumentChunk] = []
    model: str
    tokens_used: int = 0


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks: int
    collection: str
    status: str


class CollectionInfo(BaseModel):
    name: str
    document_count: int
    chunk_count: int
    created_at: str


# ===== Endpoints =====

@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
    llm_client: LLMClient = Depends(get_llm_client)
):
    """
    Query documents using RAG pipeline.
    
    1. Embeds the query
    2. Searches vector store for relevant chunks
    3. Optionally generates an answer using the LLM
    """
    logger.info(
        "📚 RAG query",
        user_id=current_user.id,
        query=request.query[:100],
        collection=request.collection
    )
    
    try:
        # Search for relevant documents
        chunks = await rag_service.search(
            query=request.query,
            collection=request.collection,
            top_k=request.top_k
        )
        
        # Format sources
        sources = [
            DocumentChunk(
                id=chunk["id"],
                content=chunk["content"],
                source=chunk["metadata"].get("source", "unknown"),
                page=chunk["metadata"].get("page"),
                score=chunk["score"],
                metadata=chunk["metadata"]
            )
            for chunk in chunks
        ]
        
        answer = None
        tokens_used = 0
        
        # Generate answer if requested
        if request.generate_answer and sources:
            context = "\n\n".join([
                f"[Source: {s.source}]\n{s.content}" 
                for s in sources
            ])
            
            system_prompt = """You are a helpful AI assistant. Answer the user's question based on the provided context. 
If the context doesn't contain enough information, say so. Always cite your sources."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.query}"}
            ]
            
            response = await llm_client.chat_completion(
                messages=messages,
                max_tokens=1024
            )
            
            answer = response["choices"][0]["message"]["content"]
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
        
        return RAGQueryResponse(
            query=request.query,
            answer=answer,
            sources=sources if request.include_sources else [],
            model=llm_client.default_model,
            tokens_used=tokens_used
        )
    
    except Exception as e:
        logger.error("❌ RAG query failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = "default",
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Upload a document for indexing.
    
    Supported formats: PDF, TXT, MD, DOCX
    """
    # Validate file type
    allowed_types = [".pdf", ".txt", ".md", ".docx", ".py", ".js", ".ts"]
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    logger.info(
        "📄 Document upload",
        user_id=current_user.id,
        filename=file.filename,
        collection=collection
    )
    
    try:
        # Read file content
        content = await file.read()
        
        # Process document
        result = await rag_service.ingest_document(
            content=content,
            filename=file.filename,
            collection=collection,
            user_id=str(current_user.id)
        )
        
        return DocumentUploadResponse(
            document_id=result["document_id"],
            filename=file.filename,
            chunks=result["chunk_count"],
            collection=collection,
            status="indexed"
        )
    
    except Exception as e:
        logger.error("❌ Document upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/collections", response_model=List[CollectionInfo])
async def list_collections(
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """List all document collections"""
    collections = await rag_service.list_collections()
    return collections


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Delete a document from the index"""
    await rag_service.delete_document(document_id)
    return {"status": "deleted", "document_id": document_id}
