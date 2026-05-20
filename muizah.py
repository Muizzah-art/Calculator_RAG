# =========================================================
# 1. IMPORTS
# =========================================================

import json  
from openai import OpenAI  
from duckduckgo_search import DDGS  

# =========================================================
# 2. API KEY + CLIENT SETUP
# =========================================================

API_KEY = "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"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# =========================================================
# 3. MODEL SELECTION
# =========================================================

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# =========================================================
# 4. TOOL 1 — CALCULATOR
# =========================================================

def calculator(expression: str) -> str:
    
    allowed = set("0123456789+-*/(). ")

    if not all(c in allowed for c in expression):
        return "Error: invalid characters in expression"

    try:
        result = eval(expression)
        return str(result)

    except Exception as e:
        return f"Math error: {str(e)}"

# =========================================================
# 5. TOOL 2 — WEB SEARCH
# =========================================================

def web_search(query: str) -> str:

    try:
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=1))

        if results:
            return results[0]["body"] 

        return "No results found"

    except Exception as e:
        return f"Search error: {str(e)}"

# =========================================================
# 6. TOOL REGISTRY 
# =========================================================

TOOLS_MAP = {
    "calculator": calculator,
    "web_search": web_search
}

# =========================================================
# 7. TOOL SCHEMAS 
# =========================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Use this tool for all math calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Use this tool to search the internet for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# =========================================================
# 8. SAFE TOOL EXECUTION 
# =========================================================

def run_tool(name: str, args: dict) -> str:
   
    try:
        if name not in TOOLS_MAP:
            return f"Unknown tool: {name}"

        tool_function = TOOLS_MAP[name]

        return tool_function(**args)

    except Exception as e:
        
        return f"Tool execution error: {str(e)}"

# =========================================================
# 9. MAIN AGENT FUNCTION (CORE LOGIC)
# =========================================================

def run_agent(user_input: str) -> str:
 
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. "
                "Use tools when needed for math or web search."
            )
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    for _ in range(5):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        msg = response.choices[0].message

        # =====================================================
        # CASE 1 — MODEL RETURNS FINAL ANSWER (NO TOOL)
        # =====================================================
        if not msg.tool_calls:
            return msg.content

        # =====================================================
        # CASE 2 — MODEL WANTS TO USE TOOLS
        # =====================================================

        messages.append(msg)

        for tool_call in msg.tool_calls:

            name = tool_call.function.name

            args = json.loads(tool_call.function.arguments)

            result = run_tool(name, args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    return "Max steps reached"

# =========================================================
# 10. CLI INTERFACE (USER INPUT LOOP)
# =========================================================

while True:
    user_input = input("\nYou: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break

    response = run_agent(user_input)

    print("\nAssistant:", response)
