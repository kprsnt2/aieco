import { Plus, MessageSquare, Trash2, ChevronLeft } from 'lucide-react';
import { Conversation } from '../types';

interface SidebarProps {
    isOpen: boolean;
    conversations: Conversation[];
    activeConversation: string;
    onSelectConversation: (id: string) => void;
    onNewChat: () => void;
    onDeleteConversation: (id: string) => void;
}

export default function Sidebar({
    isOpen,
    conversations,
    activeConversation,
    onSelectConversation,
    onNewChat,
    onDeleteConversation
}: SidebarProps) {
    if (!isOpen) return null;

    return (
        <aside className="w-64 glass-dark flex flex-col border-r border-white/5">
            {/* Header */}
            <div className="p-4 border-b border-white/5">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 hover:opacity-90 transition-opacity font-medium"
                >
                    <Plus size={18} />
                    New Chat
                </button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {conversations.map((conversation) => (
                    <div
                        key={conversation.id}
                        className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${activeConversation === conversation.id
                                ? 'bg-white/10'
                                : 'hover:bg-white/5'
                            }`}
                        onClick={() => onSelectConversation(conversation.id)}
                    >
                        <MessageSquare size={16} className="flex-shrink-0 text-zinc-400" />
                        <span className="flex-1 truncate text-sm">
                            {conversation.title}
                        </span>
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onDeleteConversation(conversation.id);
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/10 rounded transition-all"
                        >
                            <Trash2 size={14} className="text-zinc-400 hover:text-red-400" />
                        </button>
                    </div>
                ))}

                {conversations.length === 0 && (
                    <div className="text-center text-zinc-500 text-sm py-8">
                        No conversations yet
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-white/5">
                <div className="text-xs text-zinc-500 text-center">
                    <span className="gradient-text font-medium">AIEco</span> • Private AI
                </div>
            </div>
        </aside>
    );
}
