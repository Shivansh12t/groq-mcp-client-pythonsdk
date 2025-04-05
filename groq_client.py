from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import trio
import httpx
import os
import re
import ast

# ========== CONFIG ==========
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERVER_PATH = r"../docs-mcp-server-pythonsdk/main.py" #path to your mcp server
# ============================

# Start MCP tool server via stdio
server_parameters = StdioServerParameters(
    command="uv",  # use "uv" if needed, but python is safer for subprocess
    args=["run", SERVER_PATH]
)

# 1. Call Groq LLM
async def call_groq(messages, model="llama3-70b-8192"):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]

# 2. Parse tool call syntax like: Call get_docs("retriever", "langchain")
def parse_tool_call(response_text):
    pattern = r'Call\s+(\w+)\((.*?)\)'
    match = re.search(pattern, response_text)
    if not match:
        return None
    tool_name = match.group(1)
    args = ast.literal_eval(f"({match.group(2)})")
    return tool_name, args

# 3. Full agent logic
async def run():
    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to MCP Server")

            tools_response = await session.list_tools()
            tools = tools_response.tools
            tool_names = [tool.name for tool in tools]
            print("🔧 Tools available:", tool_names)

            # STEP 1: Get user input
            user_query = input("💬 You: ")

            # STEP 2: Compose prompt for Groq
            tool_instruction = (
                "You are an AI assistant with access to tools.\n"
                "You can call a tool named `get_docs(query, library)` to search docs about LangChain, OpenAI, or LlamaIndex.\n"
                "When needed, respond with:\n"
                "Call get_docs(\"<query>\", \"<library>\")\n"
                "If a tool is used, it will return results and you should use that result to answer the user query.\n"
                "Do not repeat the tool call in your final answer."
            )

            messages = [
                {"role": "system", "content": tool_instruction},
                {"role": "user", "content": user_query}
            ]

            # STEP 3: Get LLM response
            llm_response = await call_groq(messages)
            print("\n🧠 LLM Response:\n", llm_response)

            # STEP 4: Check if tool was called
            tool_call = parse_tool_call(llm_response)

            if tool_call:
                tool_name, args = tool_call
                print(f"\n🔧 Detected tool call: {tool_name}({args})")

                if tool_name == "get_docs":
                    query, library = args[0], args[1].lower()
                    result = await session.call_tool("get_docs", arguments={
                        "query": query,
                        "library": library
                    })
                    text_result = "".join([c.text for c in result.content if c.type == "text"])

                    print("\n📚 Tool Output (to feed into LLM):\n", text_result[:500])

                    # STEP 5: Inject tool response into message history
                    messages.append({"role": "assistant", "content": llm_response})
                    messages.append({
                        "role": "function",
                        "name": "get_docs",
                        "content": text_result[:4000]  # Optional: truncate
                    })

                    # STEP 6: Ask LLM to now generate final answer using tool result
                    final_response = await call_groq(messages)
                    print("\n🤖 Final Answer:\n", final_response)
                else:
                    print(f"⚠️ Unknown tool: {tool_name}")
            else:
                print("🤖 Answer (no tool used):", llm_response)


def main():
    try:
        trio.run(run)
    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    main()
