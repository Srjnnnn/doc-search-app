import asyncio
import os
import logging
from typing import Any, Sequence
import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bing-search-mcp")

class BingSearchMCP:
    def __init__(self):
        self.api_key = os.getenv("BING_API_KEY")
        self.api_url = os.getenv("BING_API_URL", "https://api.bing.microsoft.com/")
        
        if not self.api_key:
            raise ValueError("BING_API_KEY environment variable is required")
        
        self.server = Server("bing-search-mcp")
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="bing_web_search",
                    description="Search the web using Bing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of results to return (max 50)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50
                            },
                            "offset": {
                                "type": "integer", 
                                "description": "Number of results to skip",
                                "default": 0,
                                "minimum": 0
                            },
                            "market": {
                                "type": "string",
                                "description": "Market for the search",
                                "default": "en-US"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="bing_news_search",
                    description="Search for news using Bing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "News search query"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of results to return (max 100)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100
                            },
                            "market": {
                                "type": "string",
                                "description": "Market for the search",
                                "default": "en-US"
                            },
                            "freshness": {
                                "type": "string",
                                "description": "How fresh the news should be",
                                "enum": ["Day", "Week", "Month"],
                                "default": "Day"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="bing_image_search",
                    description="Search for images using Bing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Image search query"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of results to return (max 150)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 150
                            },
                            "market": {
                                "type": "string",
                                "description": "Market for the search",
                                "default": "en-US"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls"""
            try:
                if name == "bing_web_search":
                    return await self._web_search(**arguments)
                elif name == "bing_news_search":
                    return await self._news_search(**arguments)
                elif name == "bing_image_search":
                    return await self._image_search(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _web_search(self, query: str, count: int = 10, offset: int = 0, market: str = "en-US") -> list[TextContent]:
        """Perform web search"""
        url = f"{self.api_url}v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json"
        }
        params = {
            "q": query,
            "count": min(count, 50),
            "offset": offset,
            "mkt": market,
            "textFormat": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            web_pages = data.get("webPages", {}).get("value", [])
            
            for page in web_pages:
                result = f"**{page.get('name', 'No title')}**\n"
                result += f"URL: {page.get('url', 'No URL')}\n"
                result += f"Snippet: {page.get('snippet', 'No snippet')}\n"
                result += f"Display URL: {page.get('displayUrl', 'No display URL')}\n\n"
                results.append(result)
            
            if not results:
                return [TextContent(type="text", text="No web search results found.")]
            
            return [TextContent(type="text", text="".join(results))]
    
    async def _news_search(self, query: str, count: int = 10, market: str = "en-US", freshness: str = "Day") -> list[TextContent]:
        """Perform news search"""
        url = f"{self.api_url}v7.0/news/search"
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json"
        }
        params = {
            "q": query,
            "count": min(count, 100),
            "mkt": market,
            "freshness": freshness,
            "textFormat": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            articles = data.get("value", [])
            
            for article in articles:
                result = f"**{article.get('name', 'No title')}**\n"
                result += f"URL: {article.get('url', 'No URL')}\n"
                result += f"Description: {article.get('description', 'No description')}\n"
                result += f"Provider: {article.get('provider', [{}])[0].get('name', 'Unknown')}\n"
                result += f"Published: {article.get('datePublished', 'Unknown date')}\n\n"
                results.append(result)
            
            if not results:
                return [TextContent(type="text", text="No news results found.")]
            
            return [TextContent(type="text", text="".join(results))]
    
    async def _image_search(self, query: str, count: int = 10, market: str = "en-US") -> list[TextContent]:
        """Perform image search"""
        url = f"{self.api_url}v7.0/images/search"
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json"
        }
        params = {
            "q": query,
            "count": min(count, 150),
            "mkt": market
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            images = data.get("value", [])
            
            for image in images:
                result = f"**{image.get('name', 'No title')}**\n"
                result += f"URL: {image.get('contentUrl', 'No URL')}\n"
                result += f"Thumbnail: {image.get('thumbnailUrl', 'No thumbnail')}\n"
                result += f"Size: {image.get('width', 'Unknown')}x{image.get('height', 'Unknown')}\n"
                result += f"Host: {image.get('hostPageDisplayUrl', 'Unknown host')}\n\n"
                results.append(result)
            
            if not results:
                return [TextContent(type="text", text="No image results found.")]
            
            return [TextContent(type="text", text="".join(results))]