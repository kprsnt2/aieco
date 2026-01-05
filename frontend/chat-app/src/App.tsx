import { useState, useRef, useEffect } from 'react';
import { Send, Plus, Settings, Moon, Sun, Cpu, MessageSquare, Trash2, Menu } from 'lucide-react';
import ChatMessage from './components/ChatMessage';
import Sidebar from './components/Sidebar';
import { Message, Conversation } from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

function App() {
    const [conversations, setConversations] = useState<Conversation[]>([
        { id: '1', title: 'New Chat', messages: [], createdAt: new Date() }
    ]);
    const [activeConversation, setActiveConversation] = useState<string>('1');
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isDarkMode, setIsDarkMode] = useState(true);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [streamingContent, setStreamingContent] = useState('');

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const currentConversation = conversations.find(c => c.id === activeConversation);
    const messages = currentConversation?.messages || [];

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamingContent]);

    useEffect(() => {
        inputRef.current?.focus();
    }, [activeConversation]);

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input.trim(),
            timestamp: new Date()
        };

        // Update conversation with user message
        setConversations(prev => prev.map(c =>
            c.id === activeConversation
                ? { ...c, messages: [...c.messages, userMessage], title: c.messages.length === 0 ? input.slice(0, 30) : c.title }
                : c
        ));

        setInput('');
        setIsLoading(true);
        setStreamingContent('');

        try {
            const response = await fetch(`${API_URL}/api/v1/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token') || 'demo'}`
                },
                body: JSON.stringify({
                    model: 'glm-4.7',
                    messages: [...messages, userMessage].map(m => ({
                        role: m.role,
                        content: m.content
                    })),
                    stream: true
                })
            });

            if (!response.ok) throw new Error('API request failed');

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let fullContent = '';

            while (reader) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n').filter(line => line.startsWith('data: '));

                for (const line of lines) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;

                    try {
                        const parsed = JSON.parse(data);
                        const content = parsed.choices?.[0]?.delta?.content || '';
                        fullContent += content;
                        setStreamingContent(fullContent);
                    } catch {
                        // Skip invalid JSON
                    }
                }
            }

            // Add assistant message
            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: fullContent,
                timestamp: new Date()
            };

            setConversations(prev => prev.map(c =>
                c.id === activeConversation
                    ? { ...c, messages: [...c.messages, assistantMessage] }
                    : c
            ));

        } catch (error) {
            console.error('Error:', error);
            // Add error message
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: '⚠️ Sorry, I encountered an error. Please make sure the API server is running.',
                timestamp: new Date()
            };
            setConversations(prev => prev.map(c =>
                c.id === activeConversation
                    ? { ...c, messages: [...c.messages, errorMessage] }
                    : c
            ));
        } finally {
            setIsLoading(false);
            setStreamingContent('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const createNewChat = () => {
        const newConversation: Conversation = {
            id: Date.now().toString(),
            title: 'New Chat',
            messages: [],
            createdAt: new Date()
        };
        setConversations(prev => [newConversation, ...prev]);
        setActiveConversation(newConversation.id);
    };

    const deleteConversation = (id: string) => {
        setConversations(prev => prev.filter(c => c.id !== id));
        if (activeConversation === id) {
            const remaining = conversations.filter(c => c.id !== id);
            setActiveConversation(remaining[0]?.id || '');
        }
    };

    return (
        <div className="flex h-screen overflow-hidden">
            {/* Sidebar */}
            <Sidebar
                isOpen={isSidebarOpen}
                conversations={conversations}
                activeConversation={activeConversation}
                onSelectConversation={setActiveConversation}
                onNewChat={createNewChat}
                onDeleteConversation={deleteConversation}
            />

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <header className="glass-dark px-4 py-3 flex items-center justify-between border-b border-white/5">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                        >
                            <Menu size={20} />
                        </button>
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                                <Cpu size={18} />
                            </div>
                            <div>
                                <h1 className="font-semibold gradient-text">AIEco Chat</h1>
                                <p className="text-xs text-zinc-500">GLM-4.7 358B</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setIsDarkMode(!isDarkMode)}
                            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                        >
                            {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
                        </button>
                        <button className="p-2 rounded-lg hover:bg-white/10 transition-colors">
                            <Settings size={18} />
                        </button>
                    </div>
                </header>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.length === 0 && !streamingContent ? (
                        <div className="h-full flex items-center justify-center">
                            <div className="text-center max-w-md">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                                    <MessageSquare size={32} />
                                </div>
                                <h2 className="text-2xl font-bold gradient-text mb-2">Welcome to AIEco</h2>
                                <p className="text-zinc-400 mb-6">
                                    Your private AI assistant powered by GLM-4.7 358B with 1M context window
                                </p>
                                <div className="grid grid-cols-2 gap-3 text-sm">
                                    {[
                                        '💻 Write & debug code',
                                        '📚 Analyze documents',
                                        '🤖 Run AI agents',
                                        '🔧 Execute tools'
                                    ].map((feature, i) => (
                                        <div key={i} className="glass rounded-lg px-3 py-2 text-left">
                                            {feature}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <>
                            {messages.map((message) => (
                                <ChatMessage key={message.id} message={message} />
                            ))}
                            {streamingContent && (
                                <ChatMessage
                                    message={{
                                        id: 'streaming',
                                        role: 'assistant',
                                        content: streamingContent,
                                        timestamp: new Date()
                                    }}
                                    isStreaming
                                />
                            )}
                            {isLoading && !streamingContent && (
                                <div className="flex items-center gap-2 p-4 message-assistant rounded-lg w-fit">
                                    <div className="flex gap-1">
                                        <div className="typing-dot" />
                                        <div className="typing-dot" />
                                        <div className="typing-dot" />
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-white/5">
                    <div className="glass rounded-xl p-3 flex items-end gap-3 max-w-4xl mx-auto">
                        <button className="p-2 rounded-lg hover:bg-white/10 transition-colors text-zinc-400 hover:text-white">
                            <Plus size={20} />
                        </button>
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Message AIEco..."
                            rows={1}
                            className="flex-1 bg-transparent border-none outline-none resize-none text-white placeholder-zinc-500 min-h-[24px] max-h-[200px]"
                            style={{ height: 'auto' }}
                            onInput={(e) => {
                                const target = e.target as HTMLTextAreaElement;
                                target.style.height = 'auto';
                                target.style.height = Math.min(target.scrollHeight, 200) + 'px';
                            }}
                        />
                        <button
                            onClick={sendMessage}
                            disabled={!input.trim() || isLoading}
                            className={`p-2 rounded-lg transition-all ${input.trim() && !isLoading
                                    ? 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:opacity-90'
                                    : 'bg-white/10 text-zinc-500 cursor-not-allowed'
                                }`}
                        >
                            <Send size={18} />
                        </button>
                    </div>
                    <p className="text-center text-xs text-zinc-500 mt-2">
                        AIEco uses GLM-4.7 358B • Your data stays private
                    </p>
                </div>
            </div>
        </div>
    );
}

export default App;
