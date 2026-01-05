# Python SDK Guide

> Official Python SDK for AIEco API

---

## Installation

```bash
pip install aieco
# or
pip install openai  # Also works!
```

---

## Quick Start

```python
from aieco import AIEcoClient

# Initialize client
client = AIEcoClient(
    api_key="sk-your-api-key",
    base_url="http://localhost:8000/v1"  # Your AIEco server
)

# Simple chat
response = client.chat("What is Python?")
print(response)
```

---

## Configuration

### Environment Variables

```bash
export AIECO_API_KEY="sk-your-api-key"
export AIECO_BASE_URL="http://localhost:8000/v1"
```

```python
from aieco import AIEcoClient

# Auto-loads from environment
client = AIEcoClient()
```

### Direct Configuration

```python
client = AIEcoClient(
    api_key="sk-your-api-key",
    base_url="http://localhost:8000/v1",
    timeout=300,  # seconds
    max_retries=3
)
```

---

## Chat Completions

### Basic Chat

```python
response = client.chat("Tell me a joke")
print(response)
# Output: "Why did the programmer quit? Because he didn't get arrays!"
```

### With System Prompt

```python
response = client.chat(
    message="Explain recursion",
    system_prompt="You are a computer science professor. Use simple examples."
)
```

### With Full Messages

```python
response = client.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Write a Python function to sort a list"},
        {"role": "assistant", "content": "Here's a simple implementation..."},
        {"role": "user", "content": "Now make it handle duplicates"}
    ],
    model="glm-4.7",
    temperature=0.7,
    max_tokens=1000
)

print(response.choices[0].message.content)
```

### Streaming

```python
# Stream tokens as they're generated
for chunk in client.chat_stream("Write a poem about coding"):
    print(chunk, end="", flush=True)
print()  # Newline at end
```

### Async Support

```python
import asyncio
from aieco import AsyncAIEcoClient

async def main():
    client = AsyncAIEcoClient(api_key="sk-your-key")
    
    # Async chat
    response = await client.chat("Hello!")
    print(response)
    
    # Async streaming
    async for chunk in client.chat_stream("Tell me a story"):
        print(chunk, end="")

asyncio.run(main())
```

---

## Function Calling (Tools)

### Define Tools

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g., 'Tokyo'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat_completion(
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto"
)

# Check for tool calls
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    print(f"Function: {tool_call.function.name}")
    print(f"Arguments: {tool_call.function.arguments}")
```

### Complete Tool Use Flow

```python
import json

def get_weather(location: str, unit: str = "celsius") -> str:
    # Your actual implementation
    return f"Weather in {location}: 22°C, sunny"

# Initial request
response = client.chat_completion(
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools
)

# Handle tool call
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    
    # Execute the function
    result = get_weather(**args)
    
    # Send result back
    final_response = client.chat_completion(
        messages=[
            {"role": "user", "content": "What's the weather in Paris?"},
            response.choices[0].message,  # Assistant message with tool_calls
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            }
        ],
        tools=tools
    )
    
    print(final_response.choices[0].message.content)
```

---

## RAG (Document Q&A)

### Upload Documents

```python
# Upload a single file
result = client.rag_upload(
    file_path="./docs/manual.pdf",
    collection_name="product-docs"
)
print(f"Uploaded: {result['file_id']}")

# Upload multiple files
for file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    client.rag_upload(file, collection_name="knowledge-base")
```

### Query Documents

```python
# Simple query
results = client.rag_query(
    query="How do I reset my password?",
    collection_name="product-docs",
    top_k=5
)

for result in results:
    print(f"Score: {result['score']:.2f}")
    print(f"Content: {result['content'][:200]}...")
    print(f"Source: {result['metadata']['source']}")
    print()
```

### Chat with Documents

```python
response = client.rag_chat(
    message="Summarize the key features",
    collection_name="product-docs",
    include_sources=True
)

print(response['answer'])
print("\nSources:")
for source in response['sources']:
    print(f"  - {source['file']}, page {source['page']}")
```

---

## Agents

### List Available Agents

```python
agents = client.list_agents()
for agent in agents:
    print(f"{agent['name']}: {agent['description']}")
```

### Run an Agent

```python
# Run the code agent
result = client.run_agent(
    agent_type="code",
    prompt="Create a FastAPI endpoint for user registration",
    tools=["file", "shell"]  # Allow file and shell access
)

print(result['output'])
```

### Custom Agent

```python
result = client.run_agent(
    agent_type="custom",
    prompt="Research and summarize the latest AI news",
    config={
        "model": "glm-4.7",
        "max_steps": 10,
        "tools": ["web_search", "read_url"]
    }
)
```

---

## Skills

### List Skills

```python
skills = client.list_skills()
for skill in skills:
    status = "✅" if skill['active'] else "❌"
    print(f"{status} {skill['name']}: {skill['description']}")
```

### Activate a Skill

```python
# Activate the Python developer skill
client.activate_skill("python-developer")

# Now the model will use Python best practices
response = client.chat("Write a function to parse JSON files")
```

### Get Skill Details

```python
skill = client.get_skill("mcp-builder")
print(f"Name: {skill['name']}")
print(f"Description: {skill['description']}")
print(f"Instructions: {skill['instructions'][:500]}...")
```

---

## MCP Tools

### List Tools

```python
tools = client.list_mcp_tools()
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")
```

### Execute a Tool

```python
# Read a file
result = client.execute_tool(
    tool_name="read_file",
    arguments={"path": "/path/to/file.py"}
)
print(result['content'])

# Run a shell command
result = client.execute_tool(
    tool_name="shell",
    arguments={"command": "ls -la"}
)
print(result['output'])
```

---

## Error Handling

```python
from aieco import AIEcoClient, AIEcoError, RateLimitError, AuthenticationError

client = AIEcoClient(api_key="sk-your-key")

try:
    response = client.chat("Hello!")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except AIEcoError as e:
    print(f"API error: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def chat_with_retry(message: str) -> str:
    return client.chat(message)

response = chat_with_retry("Hello!")
```

---

## Using with OpenAI SDK

AIEco is fully compatible with the OpenAI Python SDK:

```python
from openai import OpenAI

# Point OpenAI client to AIEco
client = OpenAI(
    api_key="sk-local",
    base_url="http://localhost:8000/v1"
)

# Use exactly like OpenAI
response = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7
)

print(response.choices[0].message.content)
```

---

## Best Practices

### 1. Use Connection Pooling

```python
import httpx

client = AIEcoClient(
    api_key="sk-your-key",
    http_client=httpx.Client(
        limits=httpx.Limits(max_connections=100),
        timeout=httpx.Timeout(300.0)
    )
)
```

### 2. Handle Long Contexts

```python
# For very long contexts, increase timeout
response = client.chat_completion(
    messages=[{"role": "user", "content": very_long_document}],
    model="glm-4.7",
    timeout=600  # 10 minutes for 1M+ tokens
)
```

### 3. Use Streaming for UX

```python
# Always stream for better user experience
for chunk in client.chat_stream(user_message):
    yield chunk  # In a web app, stream to frontend
```

### 4. Cache Responses

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_chat(message: str, system: str) -> str:
    return client.chat(message, system_prompt=system)
```

---

## Complete Example: Chatbot

```python
from aieco import AIEcoClient

client = AIEcoClient()

def chatbot():
    print("AIEco Chatbot (type 'quit' to exit)")
    print("-" * 40)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'quit':
            break
        
        messages.append({"role": "user", "content": user_input})
        
        print("\nAssistant: ", end="", flush=True)
        
        full_response = ""
        for chunk in client.chat_stream_messages(messages):
            print(chunk, end="", flush=True)
            full_response += chunk
        
        print()
        messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    chatbot()
```

---

*For more examples, see the [examples/](../examples/) directory.*
