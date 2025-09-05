from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class QueryRequest(BaseModel):
    query: str
    use_documents: bool = True
    use_web_search: bool = False
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7

class SearchResult(BaseModel):
    text: str
    score: float
    source: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    method: str  # "document" or "web_search"
    confidence: float