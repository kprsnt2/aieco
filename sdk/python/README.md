# AIEco Python SDK

Simple, intuitive SDK for the AIEco API.

## Installation

```bash
pip install aieco
# or from source
pip install -e sdk/python
```

## Quick Start

```python
from aieco import AIEcoClient

client = AIEcoClient(api_key="your-api-key")

# Simple chat
response = client.chat("Hello, how are you?")
print(response)

# Chat with system prompt
response = client.chat(
    "Explain quantum computing",
    system="You are a physics professor. Explain concepts simply."
)

# Streaming
for chunk in client.chat_stream("Tell me a long story"):
    print(chunk, end="", flush=True)

# RAG Query
results = client.rag_query("How does authentication work?")
print(results["answer"])
print(results["sources"])

# Run Agent
result = client.run_agent(
    agent="code",
    task="Create a Python function to calculate fibonacci numbers"
)
print(result["result"])

# Execute MCP Tool
result = client.execute_tool(
    tool="filesystem.read_file",
    parameters={"path": "/path/to/file.txt"}
)

# List skills
skills = client.list_skills()
client.activate_skill("python-developer")
```

## Available Methods

| Method | Description |
|--------|-------------|
| `chat(message)` | Send a chat message |
| `chat_stream(message)` | Stream a response |
| `rag_query(query)` | Query documents |
| `rag_upload(file_path)` | Upload a document |
| `run_agent(agent, task)` | Run an AI agent |
| `list_agents()` | List available agents |
| `list_skills()` | List available skills |
| `activate_skill(name)` | Activate a skill |
| `execute_tool(tool, params)` | Execute an MCP tool |
| `list_models()` | List available models |

## License

MIT
