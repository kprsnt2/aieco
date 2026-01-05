import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, User, Bot } from 'lucide-react';
import { useState } from 'react';
import { Message } from '../types';

interface ChatMessageProps {
    message: Message;
    isStreaming?: boolean;
}

const ChatMessage = memo(({ message, isStreaming }: ChatMessageProps) => {
    const [copiedCode, setCopiedCode] = useState<string | null>(null);
    const isUser = message.role === 'user';

    const copyCode = async (code: string) => {
        await navigator.clipboard.writeText(code);
        setCopiedCode(code);
        setTimeout(() => setCopiedCode(null), 2000);
    };

    return (
        <div className={`animate-fade-in flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${isUser
                    ? 'bg-gradient-to-br from-indigo-500 to-purple-600'
                    : 'bg-gradient-to-br from-emerald-500 to-teal-600'
                }`}>
                {isUser ? <User size={16} /> : <Bot size={16} />}
            </div>

            {/* Message Content */}
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${isUser ? 'message-user' : 'message-assistant'
                }`}>
                <ReactMarkdown
                    className="prose prose-invert prose-sm max-w-none"
                    components={{
                        code({ node, inline, className, children, ...props }: any) {
                            const match = /language-(\w+)/.exec(className || '');
                            const code = String(children).replace(/\n$/, '');

                            if (!inline && match) {
                                return (
                                    <div className="code-block my-3 not-prose">
                                        <div className="code-header">
                                            <span>{match[1]}</span>
                                            <button
                                                onClick={() => copyCode(code)}
                                                className="flex items-center gap-1 hover:text-white transition-colors"
                                            >
                                                {copiedCode === code ? (
                                                    <>
                                                        <Check size={14} />
                                                        <span>Copied!</span>
                                                    </>
                                                ) : (
                                                    <>
                                                        <Copy size={14} />
                                                        <span>Copy</span>
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                        <SyntaxHighlighter
                                            style={oneDark}
                                            language={match[1]}
                                            PreTag="div"
                                            customStyle={{
                                                margin: 0,
                                                background: 'transparent',
                                                padding: '1rem'
                                            }}
                                            {...props}
                                        >
                                            {code}
                                        </SyntaxHighlighter>
                                    </div>
                                );
                            }

                            return (
                                <code className="bg-white/10 px-1.5 py-0.5 rounded text-pink-400" {...props}>
                                    {children}
                                </code>
                            );
                        },
                        p({ children }) {
                            return <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>;
                        },
                        ul({ children }) {
                            return <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>;
                        },
                        ol({ children }) {
                            return <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>;
                        },
                        a({ href, children }) {
                            return (
                                <a
                                    href={href}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-indigo-400 hover:text-indigo-300 underline"
                                >
                                    {children}
                                </a>
                            );
                        },
                        blockquote({ children }) {
                            return (
                                <blockquote className="border-l-2 border-indigo-500 pl-4 italic text-zinc-400">
                                    {children}
                                </blockquote>
                            );
                        }
                    }}
                >
                    {message.content}
                </ReactMarkdown>

                {isStreaming && (
                    <span className="inline-block w-2 h-4 bg-indigo-400 animate-pulse ml-1" />
                )}
            </div>
        </div>
    );
});

ChatMessage.displayName = 'ChatMessage';

export default ChatMessage;
