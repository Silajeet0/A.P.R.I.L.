from groq import Groq
from dotenv import load_dotenv
import datetime
from tools.web import web_search
from tools.weather import weather_tool
import json

load_dotenv()
groq_client = Groq()

tools_schema = [{
        "type":"function",
        "function":{
            "name" : "web_search",
            "description" : "A web search tool that searches the web for the latest information about the query it is given.",
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
            "description" : "A tool to search for the weather of the city provided to it.",
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
- NEVER output bulleted lists, hyphens, URLs, or markdown. 
- NEVER read raw search results to the user. Synthesize the web data into a single, natural, spoken paragraph.
- If you need information, silently use your provided tool calling functions.
- ONLY state the system time if the user explicitly asks "what time is it" or "what is the date".
- When you use a tool to fetch data, ALWAYS recite the actual data to the user immediately in a natural sentence. Do not say "I have the data" without actually speaking it.
- Never use mathematical symbols like degree signs, percent signs, or ampersands. Always spell them out (e.g., "percent", "degrees")."""
persistent_mem = [{
    "role" : "system",
    "content" : system_directive
}]

def think(user_intent : str)->str:
    global persistent_mem

    #sliding window so that the model forgets older context cleanly
    if len(persistent_mem) > 51:
        persistent_mem = [persistent_mem[0]] + persistent_mem[-50:]

    #append current context to existing ones
    persistent_mem.append({"role" : "user", "content" : user_intent})

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages = persistent_mem,
        temperature = 0.7,
        tools = tools_schema,
        tool_choice = "auto"
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_called = message.tool_calls[0]
        func_name = tool_called.function.name
        func_args = json.loads(tool_called.function.arguments)
        persistent_mem.append(message)

        if func_name == "web_search":
            query = func_args.get("query")
            tool_result = web_search(query=query)

            
            persistent_mem.append({
                "role" : "tool",
                "tool_call_id" : tool_called.id,
                "content" : tool_result
            })
        elif func_name == "weather_tool":
            city = func_args.get("city")
            tool_result = weather_tool(city)

            persistent_mem.append({
                "role" : "tool",
                "tool_call_id" : tool_called.id,
                "content" : tool_result
            })

        final_response = groq_client.chat.completions.create(
            model = "llama-3.1-8b-instant",
            messages = persistent_mem,
            temperature = 0.7
        )

        model_answer = final_response.choices[0].message.content

    else:
        model_answer = message.content

    persistent_mem.append({"role" : "assistant", "content" : model_answer})
    return model_answer

if __name__ == "__main__":
    answer = think("Hello A.P.R.I.L. are your systems live ?")
    print(f"[A.P.R.I.L.] : {answer}")