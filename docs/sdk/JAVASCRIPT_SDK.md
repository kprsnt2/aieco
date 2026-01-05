# JavaScript/TypeScript SDK Guide

> Official JavaScript SDK for AIEco API

---

## Installation

```bash
npm install @aieco/sdk
# or
yarn add @aieco/sdk
# or use OpenAI SDK
npm install openai
```

---

## Quick Start

```javascript
import { AIEcoClient } from '@aieco/sdk';

const client = new AIEcoClient({
  apiKey: 'sk-your-api-key',
  baseURL: 'http://localhost:8000/v1'
});

const response = await client.chat('What is JavaScript?');
console.log(response);
```

---

## Configuration

### Environment Variables

```bash
export AIECO_API_KEY="sk-your-api-key"
export AIECO_BASE_URL="http://localhost:8000/v1"
```

```javascript
// Auto-loads from environment
const client = new AIEcoClient();
```

### Direct Configuration

```javascript
const client = new AIEcoClient({
  apiKey: 'sk-your-api-key',
  baseURL: 'http://localhost:8000/v1',
  timeout: 300000,  // milliseconds
  maxRetries: 3
});
```

---

## Chat Completions

### Basic Chat

```javascript
const response = await client.chat('Tell me a joke');
console.log(response);
```

### With Options

```javascript
const response = await client.chatCompletion({
  messages: [
    { role: 'system', content: 'You are a helpful coding assistant.' },
    { role: 'user', content: 'Write a function to sort an array' }
  ],
  model: 'glm-4.7',
  temperature: 0.7,
  maxTokens: 1000
});

console.log(response.choices[0].message.content);
```

### Streaming

```javascript
// Callback-based streaming
await client.chatStream('Write a poem about coding', (chunk) => {
  process.stdout.write(chunk);
});

// Async iterator streaming
for await (const chunk of client.streamChat('Write a story')) {
  process.stdout.write(chunk);
}
```

### TypeScript Types

```typescript
import { AIEcoClient, ChatMessage, ChatCompletionResponse } from '@aieco/sdk';

const messages: ChatMessage[] = [
  { role: 'system', content: 'You are helpful.' },
  { role: 'user', content: 'Hello!' }
];

const response: ChatCompletionResponse = await client.chatCompletion({
  messages,
  model: 'glm-4.7'
});
```

---

## Function Calling (Tools)

```javascript
const tools = [
  {
    type: 'function',
    function: {
      name: 'get_weather',
      description: 'Get the current weather',
      parameters: {
        type: 'object',
        properties: {
          location: { type: 'string', description: 'City name' }
        },
        required: ['location']
      }
    }
  }
];

const response = await client.chatCompletion({
  messages: [{ role: 'user', content: "What's the weather in Tokyo?" }],
  tools,
  toolChoice: 'auto'
});

if (response.choices[0].message.tool_calls) {
  const toolCall = response.choices[0].message.tool_calls[0];
  console.log('Function:', toolCall.function.name);
  console.log('Arguments:', JSON.parse(toolCall.function.arguments));
}
```

---

## RAG (Document Q&A)

### Upload Documents

```javascript
// Upload a file
const result = await client.ragUpload({
  filePath: './docs/manual.pdf',
  collectionName: 'product-docs'
});
console.log('File ID:', result.fileId);

// Upload from buffer
const buffer = fs.readFileSync('document.pdf');
await client.ragUploadBuffer({
  buffer,
  filename: 'document.pdf',
  collectionName: 'product-docs'
});
```

### Query Documents

```javascript
const results = await client.ragQuery({
  query: 'How do I reset my password?',
  collectionName: 'product-docs',
  topK: 5
});

results.forEach(result => {
  console.log(`Score: ${result.score}`);
  console.log(`Content: ${result.content.slice(0, 200)}...`);
});
```

### Chat with Documents

```javascript
const response = await client.ragChat({
  message: 'Summarize the key features',
  collectionName: 'product-docs',
  includeSources: true
});

console.log(response.answer);
console.log('Sources:', response.sources);
```

---

## Agents

### Run an Agent

```javascript
const result = await client.runAgent({
  agentType: 'code',
  prompt: 'Create a REST API for user management',
  tools: ['file', 'shell']
});

console.log(result.output);
```

---

## Skills

### List and Activate Skills

```javascript
// List all skills
const skills = await client.listSkills();
skills.forEach(skill => {
  const status = skill.active ? '✅' : '❌';
  console.log(`${status} ${skill.name}: ${skill.description}`);
});

// Activate a skill
await client.activateSkill('python-developer');

// Chat with skill context
const response = await client.chat('Write a function to parse CSV');
```

---

## Error Handling

```javascript
import { 
  AIEcoClient, 
  AIEcoError, 
  RateLimitError, 
  AuthenticationError 
} from '@aieco/sdk';

try {
  const response = await client.chat('Hello!');
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Retry after ${error.retryAfter}s`);
  } else if (error instanceof AIEcoError) {
    console.error(`API error: ${error.message}`);
  } else {
    console.error('Unexpected error:', error);
  }
}
```

---

## Using with OpenAI SDK

AIEco is fully compatible with the OpenAI JavaScript SDK:

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-local',
  baseURL: 'http://localhost:8000/v1'
});

const response = await client.chat.completions.create({
  model: 'glm-4.7',
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(response.choices[0].message.content);
```

---

## React Integration

```jsx
import { useState, useCallback } from 'react';
import { AIEcoClient } from '@aieco/sdk';

const client = new AIEcoClient({ apiKey: 'sk-your-key' });

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(async () => {
    if (!input.trim()) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      let assistantContent = '';
      const assistantMessage = { role: 'assistant', content: '' };
      setMessages(prev => [...prev, assistantMessage]);
      
      await client.chatStream(input, (chunk) => {
        assistantContent += chunk;
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: 'assistant',
            content: assistantContent
          };
          return updated;
        });
      });
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  }, [input]);

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        disabled={isLoading}
      />
      <button onClick={sendMessage} disabled={isLoading}>
        Send
      </button>
    </div>
  );
}
```

---

## Node.js Server Example

```javascript
import express from 'express';
import { AIEcoClient } from '@aieco/sdk';

const app = express();
const client = new AIEcoClient();

app.use(express.json());

app.post('/api/chat', async (req, res) => {
  const { message } = req.body;
  
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  await client.chatStream(message, (chunk) => {
    res.write(`data: ${JSON.stringify({ content: chunk })}\n\n`);
  });
  
  res.write('data: [DONE]\n\n');
  res.end();
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

---

## Complete Example: CLI Chat

```javascript
import readline from 'readline';
import { AIEcoClient } from '@aieco/sdk';

const client = new AIEcoClient();

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const messages = [
  { role: 'system', content: 'You are a helpful assistant.' }
];

async function chat() {
  console.log('AIEco Chat (type "exit" to quit)\n');
  
  const prompt = () => {
    rl.question('You: ', async (input) => {
      if (input.toLowerCase() === 'exit') {
        rl.close();
        return;
      }
      
      messages.push({ role: 'user', content: input });
      
      process.stdout.write('\nAssistant: ');
      
      let fullResponse = '';
      await client.chatStream(input, (chunk) => {
        process.stdout.write(chunk);
        fullResponse += chunk;
      });
      
      console.log('\n');
      messages.push({ role: 'assistant', content: fullResponse });
      
      prompt();
    });
  };
  
  prompt();
}

chat();
```

---

*For more examples, see the [examples/](../examples/) directory.*
