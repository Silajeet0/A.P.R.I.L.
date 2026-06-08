import asyncio
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.page_scraper import page_content
from tools.web import web_search
from tools.weather import get_weather

server = Server("april-web-intelligence")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    '''Exposes the custom web search tools to compatible MCP client'''

    return[
        types.Tool(
            name = "web_search",
            description = "This tool returns searches the web for the query provided and returns the result.",
            inputSchema = {
                "type" : "object",
                "properties" : {
                    "query" : {
                        "type" : "string",
                        "description" : "The query to be searched for."
                    },
                    "max_results" : {
                        "type" : "integer",
                        "description" : "The maximum number of results to consider and return",
                        "default" : 3
                    }
                },
                "required" : ["query"]
            }
        ),

        types.Tool(
            name = "page_content",
            description = "This tool scrapes the content of the page and returns the relevant text for the particular page it scrapes.",
            inputSchema = {
                "type" : "object",
                "properties" :{
                    "url" : {
                        "type" : "string",
                        "description" : "The url of the website that needs to be scraped."
                    }
                },
                "required" : ["url"]
            }
        ),

        types.Tool(
            name = "get_weather",
            description = "This tool fetches the weather of the city that the uesr wants to know of.",
            inputSchema = {
                "type" : "object",
                "properties" : {
                    "city" : {
                        "type" : "string",
                        "description" : "The name of the city whose weather you want to know of."
                    }
                },
                "required" : ["city"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name : str, arguments:dict | None)->list[types.TextContent]:
    '''resolves the tool call if it is a valid tool with a valid argument'''

    if not arguments:
        raise ValueError("Missing tool arguments.")
    if name == "web_search":
        query = arguments.get("query")
        max_results = arguments.get("max_results", 3)
        results = web_search(query=query, max_results=max_results)
        return [types.TextContent(type = "text", text = str(results))]
    elif name == "page_content":
        url = arguments.get("url")
        results = page_content(url=url)
        return [types.TextContent(type="text", text = str(results))]
    elif name == "get_weather":
        city = arguments.get("city")
        results = await get_weather(city=city)
        return [types.TextContent(type="text", text=str(results))]
    else:
        raise ValueError(f"Unknown tool : {name}")
    
async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name = "april-web-intelligence",
                server_version="1.0.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability(listChanged=False)
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())