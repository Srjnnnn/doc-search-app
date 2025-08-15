"""
FastAPI wrapper for the MCP server to make it accessible via HTTP
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import uuid
from typing import Dict, Any
from bing_search_server import BingSearchMCP
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bing Search MCP Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP server
try:
    mcp_server = BingSearchMCP()
    logger.info("Bing Search MCP Server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MCP server: {e}")
    mcp_server = None

# Store active sessions
sessions: Dict[str, Dict[str, Any]] = {}

@app.post("/initialize")
async def initialize_session():
    """Initialize a new MCP session"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "created_at": "2024-01-01T00:00:00Z",
        "last_activity": "2024-01-01T00:00:00Z",
        "search_count": 0
    }
    
    return {
        "session_id": session_id,
        "status": "initialized",
        "capabilities": {
            "search": True,
            "web_search": True,
            "news_search": True,
            "image_search": True,
            "max_results": 150
        }
    }

@app.post("/search")
async def search_endpoint(request: Request):
    """Handle search requests via MCP protocol"""
    if mcp_server is None:
        raise HTTPException(status_code=503, detail="MCP server not available")
    
    try:
        body = await request.json()
        method = body.get("method", "bing_web_search")
        params = body.get("params", {})
        session_id = body.get("session_id")
        
        # Default to web search if method not specified
        if method == "search":
            method = "bing_web_search"
        
        # Call the appropriate MCP tool
        if method in ["bing_web_search", "bing_news_search", "bing_image_search"]:
            # Get the tool handler
            handler = mcp_server.server._tool_handlers.get(method)
            if handler:
                result = await handler(**params)
                
                # Format result for our API
                if result and len(result) > 0:
                    content = result[0].text if hasattr(result[0], 'text') else str(result[0])
                    
                    # Parse the content to extract structured results
                    results = []
                    entries = content.split('\n\n')
                    for entry in entries:
                        if entry.strip():
                            lines = entry.strip().split('\n')
                            if len(lines) >= 2:
                                title = lines[0].replace('**', '').strip()
                                url = lines[1].replace('URL: ', '').strip() if lines[1].startswith('URL:') else ''
                                snippet = lines[2].replace('Snippet: ', '').strip() if len(lines) > 2 and lines[2].startswith('Snippet:') else ''
                                
                                results.append({
                                    "title": title,
                                    "url": url,
                                    "content": snippet,
                                    "score": 1.0
                                })
                    
                    return {
                        "id": str(uuid.uuid4()),
                        "result": {
                            "query": params.get("query", ""),
                            "results": results,
                            "searchResultsCount": len(results)
                        },
                        "session_id": session_id
                    }
                else:
                    return {
                        "id": str(uuid.uuid4()),
                        "result": {
                            "query": params.get("query", ""),
                            "results": [],
                            "searchResultsCount": 0
                        },
                        "session_id": session_id
                    }
            else:
                raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def simple_search(q: str, count: int = 10, offset: int = 0):
    """Simple GET endpoint for web search"""
    if mcp_server is None:
        raise HTTPException(status_code=503, detail="MCP server not available")
    
    try:
        # Call MCP web search tool
        handler = mcp_server.server._tool_handlers.get("bing_web_search")
        if handler:
            result = await handler(query=q, count=count, offset=offset)
            
            if result and len(result) > 0:
                content = result[0].text if hasattr(result[0], 'text') else str(result[0])
                
                # Parse results
                results = []
                entries = content.split('\n\n')
                for entry in entries:
                    if entry.strip():
                        lines = entry.strip().split('\n')
                        if len(lines) >= 2:
                            title = lines[0].replace('**', '').strip()
                            url = lines[1].replace('URL: ', '').strip() if lines[1].startswith('URL:') else ''
                            snippet = lines[2].replace('Snippet: ', '').strip() if len(lines) > 2 and lines[2].startswith('Snippet:') else ''
                            
                            results.append({
                                "title": title,
                                "url": url,
                                "content": snippet,
                                "score": 1.0
                            })
                
                return {
                    "query": q,
                    "results": results,
                    "searchResultsCount": len(results)
                }
            else:
                return {
                    "query": q,
                    "results": [],
                    "searchResultsCount": 0
                }
        else:
            raise HTTPException(status_code=500, detail="Web search handler not found")
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if mcp_server is not None else "unhealthy",
        "mcp_server_available": mcp_server is not None,
        "active_sessions": len(sessions)
    }

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    if mcp_server is None:
        raise HTTPException(status_code=503, detail="MCP server not available")
    
    try:
        # Get tools from MCP server
        tools_handler = mcp_server.server._list_tools_handler
        if tools_handler:
            tools = await tools_handler()
            return {"tools": [tool.dict() for tool in tools]}
        else:
            return {"tools": []}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)