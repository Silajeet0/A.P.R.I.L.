import asyncio
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import Notification, Server
import mcp.server.stdio
from core.memory import memory_db

server = Server("april-long-term-memory")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    '''Exposes the custom graph tools to any MCP-compliant client'''
    
    return[
        types.Tool(
            name = "update_long_term_memory",
            description = "MANDATED when the user shares a permanent fact, preference change, relational status, or lifestyle update. Commits the relationship to the graph database.",
            inputSchema = {
                "type" : "object",
                "properties" : {
                    "source_node" : {"type" : "string",
                                     "description" : "The starting node name (e.g., Silajeet)"},
                    "source_label" : {"type" : "string",
                                      "description" : "The category label of the source (e.g., User)"},
                    "relationship" : {"type" : "string",
                                      "description" : "The edge type connecting them (e.g., PREFERS_TITLE)"},
                    "target_node" : {"type" : "string",
                                     "description" : "The ending node name (e.g., Boss)"},
                    "target_label" : {"type" : "string",
                                      "description" : "The category label of the target (e.g., Title)"},
                },
                "required" : ["source_node", "source_label", "relationship", "target_node", "target_label"]
            },
        ),

        types.Tool(
            name = "get_user_context",
            description = "Fetches all known permanent profile data, projects and relationships for a specific user from the graph database.",
            inputSchema = {
                "type" : "object",
                "properties" : {
                    "user" : {"type" : "string",
                              "description" : "The username to look up.", "default" : "Silajeet"}
                },
                "required" : ["user"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name:str, arguments:dict | None)-> list[types.TextContent]:
    '''Executes the underlying Python logic when the model requests a tool.'''

    if not arguments:
        raise ValueError("Missing tool arguments")
    
    if name == "update_long_term_memory":
        result = memory_db.commit_relationship(
            source_node=arguments.get("source_node"),
            source_label=arguments.get("source_label"),
            relationship=arguments.get("relationship"),
            target_node = arguments.get("target_node"),
            target_label=arguments.get("target_label")
        )

        return [types.TextContent(type="text", text = str(result))]
    
    elif name == "get_user_context":
        result = memory_db.get_user_context(user=arguments.get("user", "Silajeet"))
        return [types.TextContent(type="text", text = str(result))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")
    
async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name = "apri-long-term-memory",
                server_version = "1.0.0",
                capabilities = server.get_capabilities(
                    notification_options = Notification(),
                    experimental_capabilities = {},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())