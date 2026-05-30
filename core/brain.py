from groq import Groq
from dotenv import load_dotenv
import datetime
from tools.web import web_search
from tools.weather import weather_tool
from tools.page_scraper import page_content
import json

load_dotenv()
groq_client = Groq()

tools_schema = [{
        "type":"function",
        "function":{
            "name" : "web_search",
            "description" : "A web search tool that returns ONLY a list of webpage titels and the URL of the corresponding pages for the query. It DOES NOT return the information in the pages linked by those URL. You must use 'page_content' tool in your next turn on a returned URL if you need to summarize or gather information from a page. CRITICAL: Never use this tool for weather data or city forecasts.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "query" : {
                        "type" : "string",
                        "description" : "The search query. Keep it short and use keywords."
                    },
                },
                "required" : ["query"],
            },
        },
    },

    {
        "type" : "function",
        "function" : {
            "name" : "weather_tool",
            "description" : "A tool to search for the weather of the city provided to it. Always choose this tool for weather queries. It is completely self-contained.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "city" : {
                        "type" : "string",
                        "description" : "The name of the city whose weather is to be searched for."
                    },
                },
                "required" : ["city"],
            },
        },
    },

    {
        "type" : "function",
        "function" : {
            "name" : "page_content",
            "description" : "A page scraping tool that scrapes and reads the plain text content from the URL it is handed. Use this tool after using the 'web_search' tool to gather the actual text needed to answer the user queries.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "url" : {
                        "type" : "string",
                        "description" : "The URL from which the information is to be extracted."
                    },
                },

                "required" : ["url"],
            },
        },
    }
]

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
- CRITICAL: If the user asks a compound question (e.g., weather AND a research topic), you MUST address the weather first in a short opening sentence before providing your research summary. Never omit the weather data. Structure your final response exactly like this: "The weather in [City] is [Data]. Now, regarding [Topic]..."
"""
persistent_mem = [{
    "role" : "system",
    "content" : system_directive
}]

def think(user_intent : str)->str:
    global persistent_mem

    #sliding window so that the model forgets older context cleanly
    if len(persistent_mem) > 11:
        persistent_mem = [persistent_mem[0]] + persistent_mem[-10:]

    #append current context to existing ones
    persistent_mem.append({"role" : "user", "content" : user_intent})

    for _ in range(5):

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages = persistent_mem,
            temperature = 0.7,
            tools = tools_schema,
            tool_choice = "auto"
        )

        message = response.choices[0].message

        if message.tool_calls:
            persistent_mem.append(message)
            
            # CRITICAL CHANGE: Only process the FIRST tool call requested this turn!
            tool_called = message.tool_calls[0]
            
            func_name = tool_called.function.name
            func_args = json.loads(tool_called.function.arguments)
            tool_result = ""

            if func_name == "web_search":
                query = func_args.get("query")
                tool_result = web_search(query=query)

            elif func_name == "weather_tool":
                city = func_args.get("city")
                tool_result = weather_tool(city=city)

            elif func_name == "page_content":
                    url = func_args.get("url")
                    print(f"\n[DEBUG] A.P.R.I.L. is reading: {url}\n")
                    raw_scraped = page_content(url=url)
                
                    if not raw_scraped or len(raw_scraped.strip()) < 100:
                        tool_result = f"Error: Webpage at {url} refused to load or returned no content. Try scraping a different URL from your search results."
                    else:
                        tool_result = raw_scraped

            persistent_mem.append({
                "role" : "tool",
                "tool_call_id" : tool_called.id,
                "content" : tool_result
            })
            
            # We break out immediately and let her think about this ONE piece of data 
            # before she moves on to the next tool!
            continue
        else:
            model_answer = message.content
            persistent_mem.append({"role": "assistant",
                                   "content" : model_answer})
            return model_answer


    return "I'm sorry, my core logic got caught in a loop while researching."

if __name__ == "__main__":
    answer = think("Hello A.P.R.I.L. are your systems live ?")
    print(f"[A.P.R.I.L.] : {answer}")