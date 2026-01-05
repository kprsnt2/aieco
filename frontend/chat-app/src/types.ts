export interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
    toolCalls?: ToolCall[];
}

export interface ToolCall {
    id: string;
    name: string;
    arguments: Record<string, any>;
    result?: string;
}

export interface Conversation {
    id: string;
    title: string;
    messages: Message[];
    createdAt: Date;
    model?: string;
}

export interface Model {
    id: string;
    name: string;
    provider: string;
    contextLength: number;
}

export interface User {
    id: string;
    email: string;
    name: string;
    role: 'user' | 'admin';
}
