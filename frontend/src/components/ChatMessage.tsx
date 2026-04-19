'use client';

import React from 'react';
import { FileText, ExternalLink, ShieldCheck } from 'lucide-react';
import { ChatMessage as ChatMessageType } from '../lib/api';

interface ChatMessageProps {
  message: ChatMessageType;
  isLast?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, isLast }) => {
  const isBot = message.role === 'assistant';
  const data = message.payload;
  const isRefusal = data?.is_refusal;
  const sourceUrl = data?.source_url;
  const lastUpdated = data?.last_updated;

  return (
    <div className={`flex flex-col gap-4 mb-8 ${isLast ? 'animate-in fade-in slide-in-from-bottom-2 duration-500' : ''}`}>
      <div className={`flex items-start gap-4 ${isBot ? 'flex-row' : 'flex-row-reverse'}`}>
        {/* Avatar */}
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-sm border ${
          isBot ? 'bg-sbi-navy text-white border-sbi-navy' : 'bg-white text-slate-400 border-slate-200'
        }`}>
          {isBot ? <ShieldCheck size={20} /> : <div className="font-bold text-xs uppercase">User</div>}
        </div>

        {/* Message Bubble */}
        <div className={`max-w-[75%] px-6 py-4 text-sm leading-relaxed shadow-sm ${
          isBot 
            ? 'chat-bubble-ai' 
            : 'chat-bubble-user'
        }`}>
          {isBot ? (data?.answer || message.content) : message.content}
        </div>
      </div>

      {/* Citations & Disclaimers */}
      {isBot && (
        <div className={`flex flex-col gap-3 ml-14 max-w-[70%]`}>
          {sourceUrl && sourceUrl !== 'N/A' && !isRefusal && (
            <div className="bg-white border-l-4 border-blue-500 rounded-lg p-3 shadow-sm flex items-center gap-4 group hover:bg-slate-50 transition-all border border-slate-100">
              <div className="bg-blue-50 p-2 rounded-lg text-blue-600 group-hover:scale-110 transition-transform">
                <FileText size={18} />
              </div>
              <div className="flex flex-col overflow-hidden">
                <span className="text-[9px] font-extrabold text-blue-600 uppercase tracking-widest mb-1">Official Fact-Sheet Link</span>
                <a 
                  href={sourceUrl} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-xs font-bold text-slate-700 truncate hover:text-sbi-navy flex items-center gap-1.5"
                >
                  {sourceUrl}
                  <ExternalLink size={10} className="shrink-0" />
                </a>
                <span className="text-[9px] text-slate-400 font-bold mt-1 uppercase">Last updated from sources: {lastUpdated || 'recent'}</span>
              </div>
            </div>
          )}

          {isRefusal && (
            <div className="flex flex-col gap-4">
              <div className="bg-amber-50 border-2 border-amber-200 rounded-2xl p-5 shadow-sm text-amber-900">
                <div className="flex items-center gap-3 mb-3 text-sbi-red">
                  <ShieldCheck size={20} className="shrink-0" />
                  <span className="text-xs font-black uppercase tracking-widest">Regulatory Safety Guardrail</span>
                </div>
                <p className="text-[13px] font-bold leading-relaxed mb-4">
                  I am programmed to provide strictly factual information from AMC documentation. 
                  <span className="underline decoration-sbi-red/30">I cannot offer investment advice, comparisons, or financial planning.</span>
                </p>
                
                <div className="bg-white/60 p-4 rounded-xl border border-amber-200/50">
                  <span className="text-[10px] uppercase font-black text-amber-700 block mb-2 tracking-[0.1em]">Suggested Regulatory Resources</span>
                  <div className="flex flex-col gap-2">
                    <a 
                      href="https://www.amfiindia.com/investor-corner" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center justify-between p-2 bg-white rounded-lg border border-amber-100 hover:border-sbi-navy transition-colors text-xs font-bold text-slate-700"
                    >
                      AMFI Investor Education Portal
                      <ExternalLink size={12} className="text-slate-400" />
                    </a>
                    <a 
                      href="https://www.sebi.gov.in/individual-investor.html" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center justify-between p-2 bg-white rounded-lg border border-amber-100 hover:border-sbi-navy transition-colors text-xs font-bold text-slate-700"
                    >
                      SEBI Investor Protection
                      <ExternalLink size={12} className="text-slate-400" />
                    </a>
                  </div>
                </div>
              </div>
              <p className="text-[10px] font-bold text-slate-400 italic px-2 uppercase tracking-tight">
                Disclaimer: For personalized planning, please consult a SEBI Registered Investment Advisor (RIA).
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
