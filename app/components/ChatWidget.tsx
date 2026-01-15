'use client';

import { useState, useEffect, useRef } from 'react';

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    isSql?: boolean;  // If true, render code block
    sql?: string;
    data?: any[];
}

export default function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Initial greeting
    useEffect(() => {
        if (messages.length === 0) {
            setMessages([
                {
                    id: '1',
                    role: 'assistant',
                    content: 'Pozdravljeni! Sem vaš AI asistent za GNEP. Vprašajte me karkoli o parcelah, cenah ali poplavni varnosti. 🤖'
                }
            ]);
        }
    }, [messages.length]);

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg: ChatMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: input
        };

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/agent/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: userMsg.content })
            });

            if (!res.ok) throw new Error('Failed to fetch response');

            const data = await res.json();

            // Format format the response
            let aiContent = "Tukaj so rezultati:";
            if (data.result.length === 0) aiContent = "Nisem našel nobenih podatkov za vaše vprašanje.";
            else aiContent = `Našel sem ${data.result.length} zapisov.`;

            const aiMsg: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: aiContent,
                isSql: true,
                sql: data.sql,
                data: data.result
            };

            setMessages(prev => [...prev, aiMsg]);
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: 'Oprostite, prišlo je do napake pri obdelavi vašega vprašanja.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
            {/* Chat Window */}
            {isOpen && (
                <div className="bg-white w-96 h-[500px] mb-4 rounded-xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-10 fade-in duration-200">
                    {/* Header */}
                    <div className="bg-blue-600 p-4 text-white flex justify-between items-center">
                        <div className="flex items-center gap-2">
                            <span className="text-xl">🤖</span>
                            <h3 className="font-bold">GNEP AI Agent</h3>
                        </div>
                        <button onClick={() => setIsOpen(false)} className="hover:bg-blue-700 p-1 rounded">✕</button>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                        {messages.map((msg) => (
                            <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                <div className={`max-w-[85%] p-3 rounded-lg text-sm ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-br-none'
                                        : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
                                    }`}>
                                    <div>{msg.content}</div>

                                    {/* SQL & Data Display for Assistant */}
                                    {msg.role === 'assistant' && msg.isSql && (
                                        <div className="mt-3 space-y-2">
                                            {/* SQL Code */}
                                            <div className="bg-gray-900 text-gray-300 p-2 rounded text-xs font-mono overflow-x-auto">
                                                {msg.sql}
                                            </div>

                                            {/* Data Table Preview (Max 3 rows) */}
                                            {msg.data && msg.data.length > 0 && (
                                                <div className="bg-gray-100 rounded border border-gray-200 overflow-hidden text-xs">
                                                    <table className="w-full">
                                                        <thead className="bg-gray-200">
                                                            <tr>
                                                                {Object.keys(msg.data[0]).slice(0, 3).map(k => (
                                                                    <th key={k} className="p-1 text-left font-bold">{k}</th>
                                                                ))}
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {msg.data.slice(0, 3).map((row: any, i: number) => (
                                                                <tr key={i} className="border-t border-gray-200">
                                                                    {Object.values(row).slice(0, 3).map((val: any, j) => (
                                                                        <td key={j} className="p-1 truncate max-w-[100px]">{String(val)}</td>
                                                                    ))}
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                    {msg.data.length > 3 && (
                                                        <div className="p-1 text-center text-gray-500 italic bg-gray-50 border-t border-gray-200">
                                                            + {msg.data.length - 3} more rows
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex items-start">
                                <div className="bg-white border border-gray-200 p-3 rounded-lg rounded-bl-none shadow-sm flex gap-1">
                                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75"></span>
                                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input */}
                    <div className="p-3 bg-white border-t border-gray-200 flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="Vprašajte o cenah, parcelah..."
                            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        />
                        <button
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full w-10 h-10 flex items-center justify-center transition-colors disabled:opacity-50"
                        >
                            ➤
                        </button>
                    </div>
                </div>
            )}

            {/* Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-transform hover:scale-110 flex items-center justify-center w-14 h-14"
            >
                {isOpen ? <span className="text-xl">✕</span> : <span className="text-2xl">💬</span>}
            </button>
        </div>
    );
}
