import React, { useState, useRef, useEffect } from 'react';
import { Send, Terminal } from 'lucide-react';

interface ChatCommandProps {
    onSubmit: (prompt: string) => void;
    isProcessing: boolean;
    history: { role: 'user' | 'ai', content: string }[];
}

export const ChatCommand: React.FC<ChatCommandProps> = ({ onSubmit, isProcessing, history }) => {
    const [input, setInput] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (input.trim() && !isProcessing) {
            onSubmit(input);
            setInput("");
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    useEffect(() => {
        // Auto-scroll
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [history]);

    return (
        <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-lg shadow-xl overflow-hidden">
            {/* Header */}
            <div className="bg-slate-900 p-4 border-b border-slate-800 flex items-center space-x-2">
                <Terminal className="w-5 h-5 text-indigo-400" />
                <span className="font-mono text-sm font-semibold text-slate-200">Transformation Agent</span>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {history.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[80%] rounded-lg p-3 text-sm ${msg.role === 'user'
                                    ? 'bg-indigo-600 text-white'
                                    : 'bg-slate-800 text-slate-300 font-mono whitespace-pre-wrap border border-slate-700'
                                }`}
                        >
                            {msg.content}
                        </div>
                    </div>
                ))}
                {isProcessing && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800 text-slate-400 text-xs px-3 py-2 rounded-lg animate-pulse">
                            Thinking...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-slate-900 border-t border-slate-800">
                <div className="relative">
                    <textarea
                        ref={textareaRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Describe your transformation (e.g. 'Drop duplicates and fill missing prices with 0')..."
                        className="w-full bg-slate-950 text-slate-200 text-sm rounded-lg pl-4 pr-12 py-3 focus:outline-none focus:ring-1 focus:ring-indigo-500 border border-slate-800 resize-none h-14"
                        disabled={isProcessing}
                    />
                    <button
                        onClick={handleSubmit}
                        disabled={!input.trim() || isProcessing}
                        className="absolute right-2 top-2 p-2 text-indigo-400 hover:text-indigo-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
};
