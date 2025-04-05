# GROQ MCP Client using Python SDK

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quickstart](#quickstart)
    - [Folder Structure](#folder-structure)
    - [Clone the Repositories](#clone-the-repositories)
        - [Project Folder](#project-folder)
        - [MCP Client](#mcp-client)
        - [MCP Server (Optional but recommended)](#mcp-server-optional-but-recommended)
        - [Finally](#finally)
    - [Create `.env` according to `template.env`](#create-env-according-to-templateenv)
    - [Start Chatting](#start-chatting)
    - [Please Note](#please-note)
- [Interesting Observations](#interesting-observations)
- [Next Steps](#next-steps)
- [Bonus](#bonus)
    - [A Simple MCP Client Example for Beginners](#a-simple-mcp-client-example-for-beginners)
        - [How to Use](#how-to-use)

### Prerequisites
- `uv` package manager (optional but **recommended**)
- a local or hosted `MCP Server`, in this case i'll use `https://github.com/Shivansh12t/docs-mcp-pythonsdk`
- GROQ API Key (no credit card required) for client
- SERPER API Key (no credit card required) for server (required if using docs-mcp-server)

## Quickstart
### Folder Structure
```
project/
├── groq-mcp-client/       # Python client that connects to Groq and MCP server
│   ├── groq_client.py 
|   └── .env               # According to template.env provided    
├── docs-mcp-server/       # MCP tool server exposing documentation search tools
│   ├── main.py            # Registers `get_docs` tool and runs the MCP server
|   └── .env               # According to template.env provided
└── README.md              
```
### Clone the Respository(s)
#### Project Folder
```shell
mkdir project-name
cd project-name
```
#### MCP Client
```shell
git clone https://github.com/Shivansh12t/groq-mcp-client-pythonsdk groq-mcp-client
```
#### MCP Server (Optional but recommended)
```shell
git clone https://github.com/Shivansh12t/docs-mcp-server-pythonsdk docs-mcp-server
```
#### Finally
```shell
cd groq-mcp-client
```

### Create `.env` according to `template.env`
in both client and server

### Start Chatting
Ensure you are in the `groq-mcp-client` directory:
```shell
cd groq-mcp-client
```
Run the client, which leverages Groq's LLM and optionally connects to your MCP Server:
```shell
uv run groq_client
```

### Please Note
Change the `SERVER_PATH` in `groq-mcp-client/groq_client.py` as per your MCP server

## Interesting Observations
1. `asyncio` is unstable & is problematic in windows platform
**fix** using `trio` - a much stable asyncio alternative
2. GROQ's LLMs does not natively support MCPs yet
**fix** manually simulate MCP support

## Next Steps
- Trying to make a Client that is MCP Agnostic / Does not require us to simulate MCP support, essentially an MCP Adapter for LLMs which do not support it yet
- Trying to Server Tools, Resources, Prompts over http using SSE transport

## Bonus
### A Simple MCP Client Example for Beginners

Below is a basic implementation of an MCP client (`client.py`) to help new explorers get started with the MCP Python SDK. This example demonstrates how to connect to an MCP server and perform basic operations.

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import trio
import sys

SERVER_PATH = r"../docs-mcp-server-pythonsdk/main.py" #path to your mcp server

# defining how to start the server
server_parameters = StdioServerParameters(
    command="uv",
    args=["run",SERVER_PATH]
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
                result = await session.call_tool("get_docs", arguments={
                    "query": "retriever",
                    "library": "langchain"
                })
                result_string = "".join([c.text for c in result.content if c.type == "text"])
                print("📚 Tool result:\n", result_string[:1000]) # first thousand characters
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
```

### How to Use
1. You can Find this file at `groq-mcp-client/client.py`
2. Ensure your MCP server is running and accessible at the specified `SERVER_PATH`.
3. Run the script:
   ```shell
   uv run client.py
   ```
4. Enter a query when prompted, and the client will fetch relevant documentation results from the MCP server.

This example is a great starting point for understanding how to interact with an MCP server using Python.
