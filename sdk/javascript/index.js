/**
 * AIEco JavaScript SDK
 * Simple, intuitive SDK for the AIEco API
 */

export class AIEcoClient {
    constructor(options = {}) {
        this.apiKey = options.apiKey || '';
        this.baseUrl = (options.baseUrl || 'http://localhost:8080').replace(/\/$/, '');
        this.model = options.model || 'glm-4.7';
    }

    _getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.apiKey) {
            headers['Authorization'] = `Bearer ${this.apiKey}`;
        }
        return headers;
    }

    async _fetch(path, options = {}) {
        const response = await fetch(`${this.baseUrl}${path}`, {
            ...options,
            headers: { ...this._getHeaders(), ...options.headers }
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        return response;
    }

    // ===== Chat =====

    /**
     * Send a chat message
     * @param {string} message - User message
     * @param {Object} options - Optional settings
     * @returns {Promise<string>} - AI response
     */
    async chat(message, options = {}) {
        const messages = [];

        if (options.system) {
            messages.push({ role: 'system', content: options.system });
        }

        if (options.history) {
            messages.push(...options.history);
        }

        messages.push({ role: 'user', content: message });

        const response = await this._fetch('/api/v1/chat/completions', {
            method: 'POST',
            body: JSON.stringify({
                model: this.model,
                messages,
                stream: false,
                ...options
            })
        });

        const data = await response.json();
        return data.choices[0].message.content;
    }

    /**
     * Stream a chat response
     * @param {string} message - User message
     * @param {Function} onChunk - Callback for each chunk
     * @param {Object} options - Optional settings
     */
    async chatStream(message, onChunk, options = {}) {
        const messages = [];

        if (options.system) {
            messages.push({ role: 'system', content: options.system });
        }

        messages.push({ role: 'user', content: message });

        const response = await this._fetch('/api/v1/chat/completions', {
            method: 'POST',
            body: JSON.stringify({
                model: this.model,
                messages,
                stream: true
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.startsWith('data: '));

            for (const line of lines) {
                const data = line.slice(6);
                if (data === '[DONE]') return;

                try {
                    const parsed = JSON.parse(data);
                    const content = parsed.choices?.[0]?.delta?.content;
                    if (content) onChunk(content);
                } catch { }
            }
        }
    }

    // ===== RAG =====

    /**
     * Query documents using RAG
     */
    async ragQuery(query, options = {}) {
        const response = await this._fetch('/api/v1/rag/query', {
            method: 'POST',
            body: JSON.stringify({
                query,
                collection: options.collection || 'default',
                top_k: options.topK || 5,
                generate_answer: options.generateAnswer !== false
            })
        });

        return response.json();
    }

    /**
     * Upload a document
     */
    async ragUpload(file, collection = 'default') {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(
            `${this.baseUrl}/api/v1/rag/documents/upload?collection=${collection}`,
            {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.apiKey}` },
                body: formData
            }
        );

        return response.json();
    }

    // ===== Agents =====

    /**
     * Run an AI agent
     */
    async runAgent(agent, task, options = {}) {
        const response = await this._fetch('/api/v1/agents/run', {
            method: 'POST',
            body: JSON.stringify({
                agent,
                task,
                context: options.context || {},
                max_iterations: options.maxIterations || 10,
                stream: false
            })
        });

        return response.json();
    }

    /**
     * List available agents
     */
    async listAgents() {
        const response = await this._fetch('/api/v1/agents/list');
        return response.json();
    }

    // ===== Skills =====

    async listSkills() {
        const response = await this._fetch('/api/v1/skills/list');
        return response.json();
    }

    async activateSkill(skillName) {
        const response = await this._fetch('/api/v1/skills/activate', {
            method: 'POST',
            body: JSON.stringify({ skill_name: skillName })
        });
        return response.json();
    }

    // ===== MCP Tools =====

    async executeTool(tool, parameters = {}) {
        const response = await this._fetch('/api/v1/mcp/execute', {
            method: 'POST',
            body: JSON.stringify({ tool, parameters })
        });
        return response.json();
    }

    async listTools() {
        const response = await this._fetch('/api/v1/mcp/tools');
        return response.json();
    }

    // ===== Models =====

    async listModels() {
        const response = await this._fetch('/api/v1/models');
        const data = await response.json();
        return data.data || [];
    }
}

/**
 * Create an AIEco client
 */
export function createClient(options = {}) {
    return new AIEcoClient(options);
}

export default AIEcoClient;
