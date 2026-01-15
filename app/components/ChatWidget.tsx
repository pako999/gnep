'use client';

import { useState, useRef, useEffect } from 'react';

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    isSql?: boolean;
    sql?: string;
    data?: any[];
}

export default function ChatWidget() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Initial greeting (only once)
    useEffect(() => {
        if (messages.length === 0) {
            setMessages([
                {
                    id: '1',
                    role: 'assistant',
                    content: 'Pozdravljeni! Sem vaš GNEP AI asistent. Kako vam lahko pomagam pri analizi nepremičnin danes? 🤖'
                }
            ]);
        }
    }, [messages.length]);

    // Auto-scroll
    useEffect(() => {
        if (showHistory) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, showHistory]);

    const handleSend = async (text: string = input) => {
        if (!text.trim()) return;

        // Show history when interaction starts
        setShowHistory(true);

        const userMsg: ChatMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: text
        };

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/agent/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: userMsg.content })
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(errorData.detail || `Server Error ${res.status}`);
            }

            const data = await res.json();

            let aiContent = "Tukaj so rezultati:";
            if (!data.result || data.result.length === 0) aiContent = "Nisem našel nobenih podatkov za vaše kriterije.";
            else aiContent = `Našel sem ${data.result.length} zapisov.`;

            const aiMsg: ChatMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: aiContent,
                isSql: true,
                sql: data.sql,
                data: data.result || []
            };

            setMessages(prev => [...prev, aiMsg]);
        } catch (err: any) {
            console.error(err);
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: typeof err.message === 'string' && err.message.length < 100
                    ? `Napaka: ${err.message}. (Preverite API ključ)`
                    : 'Oprostite, prišlo je do napake pri obdelavi vašega vprašanja. Prosim poskusite ponovno.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <>
            {/* Messages Area (Floats above bar) */}
            {showHistory && (
                <div className="fixed bottom-20 left-4 right-4 md:left-20 md:right-20 max-h-[60vh] overflow-y-auto bg-white/95 backdrop-blur shadow-2xl rounded-t-xl border border-gray-200 border-b-0 p-4 z-40 transition-all duration-300">
                    <div className="flex justify-between items-center mb-4 border-b pb-2">
                        <h3 className="font-bold text-gray-700">Pogovor z AI Asistentom</h3>
                        <button onClick={() => setShowHistory(false)} className="text-gray-500 hover:text-gray-800">
                            ✕ Zapri
                        </button>
                    </div>

                    <div className="space-y-4">
                        {messages.map((msg) => (
                            <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                                <div className={`max-w-[90%] p-3 rounded-xl text-sm ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-br-none'
                                    : 'bg-gray-100 border border-gray-200 text-gray-800 rounded-bl-none'
                                    }`}>
                                    <div>{msg.content}</div>

                                    {/* Data Table */}
                                    {msg.role === 'assistant' && msg.data && msg.data.length > 0 && (
                                        <div className="mt-3 overflow-x-auto bg-white rounded border border-gray-200">
                                            <table className="w-full text-xs text-left">
                                                <thead className="bg-gray-50 text-gray-600 font-medium border-b">
                                                    <tr>
                                                        {Object.keys(msg.data[0]).slice(0, 5).map(k => (
                                                            <th key={k} className="p-2 whitespace-nowrap">{k}</th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {msg.data.slice(0, 5).map((row: any, i: number) => (
                                                        <tr key={i} className="border-b last:border-0 hover:bg-blue-50">
                                                            {Object.values(row).slice(0, 5).map((val: any, j) => (
                                                                <td key={j} className="p-2 truncate max-w-[150px]">{String(val)}</td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                            {msg.data.length > 5 && (
                                                <div className="p-1 text-center text-gray-400 bg-gray-50 italic text-[10px]">
                                                    + {msg.data.length - 5} ostalih zapisov
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex items-start">
                                <div className="bg-gray-100 p-3 rounded-xl rounded-bl-none flex gap-1">
                                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>
            )}

            {/* Bottom Input Bar */}
            <div className="fixed bottom-0 left-0 right-0 z-50 bg-[#1a1f2e] border-t border-gray-800 p-3 shadow-lg">
                <div className="max-w-[1400px] mx-auto flex items-center gap-3">
                    {/* Icon */}
                    <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white shrink-0">
                        🤖
                    </div>

                    {/* Input */}
                    <div className="flex-1 relative">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Vprašajte AI asistenta o tem območju..."
                            className="w-full bg-[#0f111a] text-gray-200 border border-gray-700 rounded-lg pl-4 pr-12 py-2.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder-gray-500"
                        />
                        <button
                            onClick={() => handleSend()}
                            disabled={!input.trim()}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-blue-500 hover:text-blue-400 disabled:opacity-50 p-1"
                        >
                            ➤
                        </button>
                    </div>

                    {/* Quick Access Buttons (Hidden on mobile) */}
                    <div className="hidden md:flex items-center gap-2">
                        <button
                            onClick={() => handleSend("Analiziraj to območje za poplavno varnost")}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
                        >
                            Analiziraj Območje
                        </button>
                        <button
                            onClick={() => handleSend("Kaj se nahaja na tem območju?")}
                            className="bg-[#2a3042] hover:bg-[#353b50] text-gray-300 border border-gray-700 px-4 py-2 rounded-lg text-sm transition-colors whitespace-nowrap"
                        >
                            Identificiraj Objekte
                        </button>
                        <button
                            onClick={() => handleSend("Kakšne so cene nepremičnin v bližini?")}
                            className="bg-[#2a3042] hover:bg-[#353b50] text-gray-300 border border-gray-700 px-4 py-2 rounded-lg text-sm transition-colors whitespace-nowrap"
                        >
                            Cene Nepremičnin
                        </button>
                        <button
                            onClick={() => setShowHistory(!showHistory)}
                            className="text-gray-400 hover:text-white px-2 transition-colors"
                            title={showHistory ? "Skrij pogovor" : "Pokaži pogovor"}
                        >
                            {showHistory ? '⬇' : '⬆'}
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
}
