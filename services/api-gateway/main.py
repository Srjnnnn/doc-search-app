from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
import logging
from models import QueryRequest, QueryResponse, SearchResult
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Q&A and Web Search API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
DOCUMENT_SERVICE_URL = "http://document-service:8001"
LLM_SERVICE_URL = "http://llm-service:8002"
WEB_SEARCH_SERVICE_URL = "http://web-search-service:8003"

@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload documents to document service"""
    try:
        async with AsyncClient() as client:
            files_data = []
            for file in files:
                content = await file.read()
                files_data.append(("files", (file.filename, content, file.content_type)))
            
            response = await client.post(
                f"{DOCUMENT_SERVICE_URL}/upload-documents",
                files=files_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process user query using documents or web search"""
    try:
        context = ""
        sources = []
        method = ""
        
        # First, try document search if enabled
        if request.use_documents:
            try:
                doc_results = await search_documents(request.query)
                if doc_results and len(doc_results) > 0:
                    context = "\n\n".join([result["text"] for result in doc_results[:3]])
                    sources = [
                        SearchResult(
                            text=result["text"][:200] + "...",
                            score=result["score"],
                            source="document"
                        ) for result in doc_results
                    ]
                    method = "document"
            except Exception as e:
                logger.warning(f"Document search failed: {e}")
        
        # If no document results and web search is enabled, try web search
        if not context and request.use_web_search:
            try:
                web_results = await search_web(request.query)
                if web_results and len(web_results) > 0:
                    context = "\n\n".join([
                        f"Title: {result.get('title', '')}\nContent: {result.get('content', '')}"
                        for result in web_results[:3]
                    ])
                    sources = [
                        SearchResult(
                            text=result.get("content", "")[:200] + "...",
                            score=result.get("score", 0.5),
                            source="web"
                        ) for result in web_results
                    ]
                    method = "web_search"
            except Exception as e:
                logger.warning(f"Web search failed: {e}")
        
        # Generate response using LLM
        answer = await generate_llm_response(
            query=request.query,
            context=context,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Calculate confidence based on context availability
        confidence = 0.8 if context else 0.3
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            method=method or "direct",
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def search_documents(query: str):
    """Search documents using document service"""
    async with AsyncClient() as client:
        response = await client.post(
            f"{DOCUMENT_SERVICE_URL}/search",
            json={"query": query, "top_k": 5}
        )
        
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            return []

async def search_web(query: str):
    """Search web using web search service"""
    async with AsyncClient() as client:
        response = await client.post(
            f"{WEB_SEARCH_SERVICE_URL}/search",
            json={"query": query, "num_results": 5}
        )
        
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            return []

async def generate_llm_response(query: str, context: str = "", max_tokens: int = 512, temperature: float = 0.7):
    """Generate response using LLM service"""
    async with AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{LLM_SERVICE_URL}/generate",
            json={
                "query": query,
                "context": context,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", "I couldn't generate a response.")
        else:
            return "I encountered an error while generating the response."

@app.get("/health")
async def health_check():
    """Check health of all services"""
    health_status = {"gateway": "healthy"}
    
    services = [
        ("document-service", DOCUMENT_SERVICE_URL),
        ("llm-service", LLM_SERVICE_URL),
        ("web-search-service", WEB_SEARCH_SERVICE_URL)
    ]
    
    async with AsyncClient() as client:
        for service_name, service_url in services:
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                health_status[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception:
                health_status[service_name] = "unreachable"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)