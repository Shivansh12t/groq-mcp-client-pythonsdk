from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import trio
import sys

# defining how to start the server
server_parameters = StdioServerParameters(
    command="uv",
    args=["run",r"../intro-mcp-with-python-sdk/main.py"]
)

# define async client function
async def run():
    # MCP server via STDIO
    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:

            # init connection
            await session.initialize()
            print("[+] Connected to MCP Server")

            tools_response = await session.list_tools()
            tools = tools_response.tools
            print("[+] Available Tools :", tools)

            # call a tool
            tool_names = [tool.name for tool in tools]
            print(tool_names)
            if "get_docs" in tool_names:
                # result = await session.call_tool("get_docs", arguments={
                #     "query": "retriever",
                #     "library": "langchain"
                # })
                # result_string = "".join([c.text for c in result.content if c.type == "text"])
                # print("📚 Tool result:\n", result_string[:1000]) # first thousand characters
                pass
            else:
                print("⚠️ Tool 'get_docs' not found!")

def main():
    try:
        trio.run(run)
    except ValueError as e:
        if "I/O operation on closed pipe" in str(e):
            print("Communication error: I/O operation on closed pipe")
        else:
            raise
        sys.exit(0)

if __name__ == "__main__":
    main()