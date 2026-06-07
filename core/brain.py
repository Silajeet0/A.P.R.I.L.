import datetime
import json
import os
import contextlib
from dotenv import load_dotenv
from groq import Groq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
groq_client = Groq()

# Register your servers inside a structured dictionary
ALL_SERVERS = {
    "memory": StdioServerParameters(
        command="python",
        args=["mcp_servers/mcp_memory_server.py"]
    ),
    "web": StdioServerParameters(
        command="python",
        args=["mcp_servers/mcp_web_server.py"]
    )
}

boot_time = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

system_directive = f"""You are A.P.R.I.L., a highly efficient, technical AI voice assistant.
You are running natively on an 8GB Linux system.
The current system date and time is: {boot_time}.
Your user is currently located in Howrah, West Bengal, India. 

Guidelines:
- Keep your answers brief, technical, and conversational.
- You are a VOICE assistant. Your output is fed directly into a TTS engine.
- NEVER output bulleted lists, hyphens, URLs, or markdown. Always write in plain conversational paragraphs.
- Never use mathematical symbols like degree signs or percent signs. Always spell them out (e.g., "percent", "degrees").
- ALWAYS synthesize and speak the results of EVERY tool you use. If you fetch the weather, you MUST read it to the user. Do not ignore data.
- STRICT TOOL CHAINING: If a user asks you to "read the article" or "summarize the page", you are FORBIDDEN from answering using only the web_search snippets. You MUST run web_search, extract the URL, and then use the page_content tool to read the full text before speaking.
- ONLY state the system time if the user explicitly asks "what time is it" or "what is the date".
- If you run the 'web_search' tool, DO NOT answer the user immediately. You MUST wait, look at the returned URLs, and execute the 'page_content' tool on the best link in the very next turn.
- CRITICAL: - ONLY if the user explicitly combines a question about the weather with another topic in a single turn, address the weather data briefly first. If the user does not ask about the weather, do not mention it.
=======================================================================
CRITICAL INSTRUCTION ON LONG-TERM MEMORY ROUTING:
- You have access to the 'update_long_term_memory' tool. You are MANDATED to call this tool the absolute millisecond the user shares a permanent fact, preference change, relational status, or lifestyle update.
- If the user says "Call me X", "Remember Y", "I am working on Z", or "My project is W", you are FORBIDDEN from answering via text first. You MUST execute 'update_long_term_memory' to commit the state change to the graph database.
- Do not merely agree to remember. Write it to the database using the tool.
=======================================================================
"""

class AprilBrain:
    def __init__(self):
        self.persistent_mem = []
        self.available_tools = []
        self.server_sessions = {}
        self.exit_stack = None
    
    async def initialize_cognitive_layers(self):
        """Runs once on application boot to hydrate state from MCP servers"""
        print("[Brain] Booting channels to all registered MCP servers...")
        self.available_tools = []
        self.exit_stack = contextlib.AsyncExitStack()
        
        for server_name, params in ALL_SERVERS.items():
            try:
                read_stream, write_stream = await self.exit_stack.enter_async_context(stdio_client(params))
                session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
                await session.initialize()
                
                self.server_sessions[server_name] = session
                print(f"[Brain] Connected successfully to '{server_name}' server.")

                if server_name == "memory":
                    context_response = await session.call_tool("get_user_context", arguments={"user": "Silajeet"})
                    long_term_context = context_response.content[0].text
                    hydrated_prompt = f"{system_directive}\n\nLONG-TERM RECALL:\n{long_term_context}"
                    self.persistent_mem = [{"role": "system", "content": hydrated_prompt}]
                
                tools_data = await session.list_tools()
                for tool in tools_data.tools:
                    self.available_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    })
            except Exception as e:
                print(f"[Brain Error] Failed connecting to server '{server_name}': {e}")
                raise e
                
        print(f"[Brain] Cognitive sync complete. Registered {len(self.available_tools)} tools universally.")

    async def think(self, user_input: str) -> str:
        """The core execution loop. Handles LLM evaluation and universal tool execution"""
        self.persistent_mem.append({"role": "user", "content": user_input})
        if len(self.persistent_mem) > 11:
            self.persistent_mem = [self.persistent_mem[0]] + self.persistent_mem[-10:]

        print("\n[A.P.R.I.L.] Thinking...")

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=self.persistent_mem,
            tools=self.available_tools if self.available_tools else None,
            temperature=0.7,
            tool_choice="auto"
        )
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            self.persistent_mem.append(response_message)
            for tool_call in response_message.tool_calls:
                print(f"[A.P.R.I.L.] Executing MCP Tool: {tool_call.name}")
                
                # Dynamic Session Routing Lookup
                target_session = None
                if tool_call.name in ["get_user_context", "update_long_term_memory"]:
                    target_session = self.server_sessions.get("memory")
                elif tool_call.name in ["web_search", "page_content"]:
                    target_session = self.server_sessions.get("web")
                
                if not target_session:
                    print(f"[Error] No active server session mapped for tool: {tool_call.name}")
                    continue
                
                try:
                    tool_result = await target_session.call_tool(tool_call.name, arguments=tool_call.arguments)
                    raw_result_text = tool_result.content[0].text
                    print(f"[Result] {raw_result_text}")

                    self.persistent_mem.append({
                        "role": "tool",
                        "name": tool_call.name,
                        "tool_call_id": tool_call.id,
                        "content": raw_result_text
                    })
                except Exception as tool_err:
                    print(f"[Execution Error] Failed calling tool '{tool_call.name}': {tool_err}")
            
            secondary_response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=self.persistent_mem
            )
            assistant_reply = secondary_response.choices[0].message.content
        else:
            assistant_reply = response_message.content

        self.persistent_mem.append({"role": "assistant", "content": assistant_reply})
        return assistant_reply