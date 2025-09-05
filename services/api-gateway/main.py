import logging
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient, ConnectError, ReadTimeout, HTTPStatusError

# The tenacity library is used to add automatic retries
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from models import QueryRequest, QueryResponse, SearchResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Q&A and Web Search API Gateway")

# Allow all origins for simplicity in a development environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from Docker Compose
DOCUMENT_SERVICE_URL = "http://document-service:8001"
LLM_SERVICE_URL = "http://llm-service:8002"
WEB_SEARCH_SERVICE_URL = "http://web-search-service:8003"


# --- Retry Logic Configuration ---
# Define which exceptions should trigger a retry. These are common during startup.
RETRYABLE_EXCEPTIONS = (ConnectError, ReadTimeout)

# Define the retry behavior: try 3 times, wait exponentially between attempts.
RETRY_SETTINGS = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=2, max=10),
    "reraise": True,  # Reraise the exception after the last attempt fails
}


@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload documents to document service"""
    logger.info(f"Received files for processing: {[file.filename for file in files]}")
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    try:
        # Set a long timeout for potentially large file uploads
        async with AsyncClient(timeout=380.0) as client:
            files_data = []
            for file in files:
                content = await file.read()
                files_data.append(("files", (file.filename, content, file.content_type)))
            
            response = await client.post(
                f"{DOCUMENT_SERVICE_URL}/upload-documents",
                files=files_data
            )
            
            # Raise an exception for HTTP errors, which will be caught below
            response.raise_for_status()
            return response.json()
                
    except HTTPStatusError as e:
        logger.error(f"HTTP error uploading documents: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process user query using documents or web search"""
    context = ""
    sources = []
    method = ""
    
    # First, try document search if enabled
    if request.use_documents:
        try:
            doc_results = await search_documents(request.query)
            if doc_results:
                context = "\n\n".join([result["text"] for result in doc_results[:3]])
                sources = [
                    SearchResult(
                        text=result["text"][:200] + "...",
                        score=result["score"],
                        source="document"
                    ) for result in doc_results
                ]
                method = "document"
        except RetryError as e:
            logger.warning(f"Document search failed after multiple retries: {e}")
            # Do not fail the whole request; proceed without document context
    
    # If no document results and web search is enabled, try web search
    if not context and request.use_web_search:
        try:
            web_results = await search_web(request.query)
            if web_results:
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
        except RetryError as e:
            logger.warning(f"Web search failed after multiple retries: {e}")
            # Proceed without web context
    
    # Generate response using LLM
    try:
        answer = await generate_llm_response(
            query=request.query,
            context=context,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
    except RetryError as e:
        logger.error(f"LLM generation failed after multiple retries: {e}")
        raise HTTPException(status_code=503, detail="The AI model is currently unavailable after multiple attempts. Please try again later.")

    confidence = 0.8 if context else 0.3
    
    return QueryResponse(
        answer=answer,
        sources=sources,
        method=method or "direct",
        confidence=confidence
    )

# The @retry decorator automatically retries the function if it fails with a specified exception
# CORRECTED: Changed 'retry_on_exception' to 'retry'
@retry(**RETRY_SETTINGS, retry=lambda e: isinstance(e, RETRYABLE_EXCEPTIONS))
async def search_documents(query: str):
    """Search documents using document service"""
    async with AsyncClient() as client:
        response = await client.post(
            f"{DOCUMENT_SERVICE_URL}/search",
            json={"query": query, "top_k": 12}
        )
        response.raise_for_status()  # This is crucial to trigger retries on 5xx errors
        return response.json().get("results", [])

# CORRECTED: Changed 'retry_on_exception' to 'retry'
@retry(**RETRY_SETTINGS, retry=lambda e: isinstance(e, RETRYABLE_EXCEPTIONS))
async def search_web(query: str):
    """Search web using web search service"""
    async with AsyncClient() as client:
        response = await client.post(
            f"{WEB_SEARCH_SERVICE_URL}/search",
            json={"query": query, "num_results": 5}
        )
        response.raise_for_status()
        return response.json().get("results", [])

# CORRECTED: Changed 'retry_on_exception' to 'retry'
@retry(**RETRY_SETTINGS, retry=lambda e: isinstance(e, RETRYABLE_EXCEPTIONS))
async def generate_llm_response(query: str, context: str = "", max_tokens: int = 1024, temperature: float = 0.7):
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
        response.raise_for_status()
        return response.json().get("response", "I couldn't generate a response.")


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
                # A health check should have a short timeout
                response = await client.get(f"{service_url}/health", timeout=5.0)
                if response.status_code == 200:
                    health_status[service_name] = "healthy"
                else:
                    health_status[service_name] = "unhealthy"
            except Exception:
                health_status[service_name] = "unreachable"
    
    return health_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)