'use client';

import React, { useState } from 'react';
import { Send, Hash } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (msg: string) => void;
  isLoading: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  return (
    <div className="p-8 border-t border-slate-100 bg-white/80 backdrop-blur-md">
      <form 
        onSubmit={handleSubmit}
        className="max-w-4xl mx-auto relative flex items-center gap-4"
      >
        <div className="flex-1 relative group">
          <div className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-sbi-navy transition-colors">
            <Hash size={16} />
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Ask about Exit Load, Lock-in, or Expense Ratios..."
            className="w-full pl-14 pr-16 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-semibold text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-sbi-navy/5 focus:border-sbi-navy transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={`absolute right-3 top-2 bottom-2 aspect-square rounded-xl flex items-center justify-center transition-all ${
              input.trim() && !isLoading
                ? 'bg-sbi-red text-white hover:bg-red-700 shadow-md active:scale-90'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            <Send size={18} />
          </button>
        </div>
      </form>
      <div className="mt-4 text-center">
        <span className="text-[9px] text-slate-400 font-extrabold uppercase tracking-[0.2em]">
          Powered by Verified RAG Retreival & Guardrail Engine
        </span>
      </div>
    </div>
  );
};

export default ChatInput;
