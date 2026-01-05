# AIEco JavaScript SDK

Simple, intuitive SDK for the AIEco API.

## Installation

```bash
npm install @aieco/sdk
```

## Quick Start

```javascript
import { AIEcoClient } from '@aieco/sdk';

const client = new AIEcoClient({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:8080'
});

// Simple chat
const response = await client.chat('Hello!');
console.log(response);

// Chat with system prompt
const response = await client.chat('Explain quantum computing', {
  system: 'You are a physics professor.'
});

// Streaming
await client.chatStream('Tell me a story', (chunk) => {
  process.stdout.write(chunk);
});

// RAG Query
const results = await client.ragQuery('How does auth work?');
console.log(results.answer);

// Run Agent
const result = await client.runAgent('code', 'Create a sorting function');
console.log(result.result);

// Execute Tool
const result = await client.executeTool('filesystem.read_file', {
  path: '/path/to/file.txt'
});
```

## Available Methods

| Method | Description |
|--------|-------------|
| `chat(message, options)` | Send a chat message |
| `chatStream(message, onChunk)` | Stream a response |
| `ragQuery(query, options)` | Query documents |
| `ragUpload(file, collection)` | Upload a document |
| `runAgent(agent, task, options)` | Run an AI agent |
| `listAgents()` | List available agents |
| `listSkills()` | List available skills |
| `activateSkill(name)` | Activate a skill |
| `executeTool(tool, params)` | Execute an MCP tool |
| `listModels()` | List available models |

## License

MIT
