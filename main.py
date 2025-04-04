import httpx
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = httpx.Client(base_url=self.base_url, timeout=30)

    def create_context(self):
        context_id = str(uuid.uuid4())
        res = self.session.post("/contexts", json={"id": context_id})
        return res.json()
    
    def add_message(self, context_id: str, role: str, content: str):
        paylaod = {
            "role":role,
            "content":content
        }
        res = self.session.post(f"/contexts/{context_id}/messages", json = paylaod)
        return res.json()
    
    def get_message(self, context_id: str):
        res = self.session.get(f"/contexts/{context_id}/messages")
        return res.json()
    
    def delete_message(self, context_id: str, message_id: str):
        res = self.session.delete(f"/contexts/{context_id}/messages/{message_id}")
        return res.status_code == 204
    
    def run_completion(self, context_id: str, model="llama3-70b", temperature=0.7, max_tokens=1000):
        payload = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        res = self.session.post(f"/contexts/{context_id}/completion", json=payload)
        return res.json()

def call_groq_completion(messages, model="llama-3-70b-8192", temperature=0.7, max_tokens=1000):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    res = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]

def main():
    mcp = MCPClient("http://localhost:8000")  # Your MCP memory server

    context = mcp.create_context()
    context_id = context["id"]
    print("Created Context:", context_id)

    while True:
        query = input("\nYou: ")
        if query.lower() in ["exit", "quit"]:
            break

        mcp.add_message(context_id, "user", query)

        # Fetch message history from MCP
        history = mcp.get_message(context_id)["messages"]

        # Format for OpenAI/Groq-style LLMs
        formatted_history = [{"role": m["role"], "content": m["content"]} for m in history]

        # Call Groq for completion
        reply = call_groq_completion(formatted_history)
        print("🤖:", reply)

        # Store assistant response into MCP memory
        mcp.add_message(context_id, "assistant", reply)



if __name__ == "__main__":
    main()
