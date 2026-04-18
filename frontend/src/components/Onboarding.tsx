'use client';

import React from 'react';
import { Info, MessageSquare } from 'lucide-react';

interface OnboardingProps {
  onSelect: (query: string) => void;
}

const Onboarding: React.FC<OnboardingProps> = ({ onSelect }) => {
  const examples = [
    { label: 'SBI ELSS Details', query: 'What is the lock-in period for SBI ELSS Tax Saver?' },
    { label: 'Exit Load Policy', query: 'What is the exit load for SBI Mutual Flexicap Fund?' },
    { label: 'SIP Minimums', query: 'What is the minimum SIP amount for SBI Large Cap Fund?' },
    { label: 'Stamp Duty', query: 'What are the stamp duty charges for SBI Mutual Fund investments?' }
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-12 text-center animate-in fade-in zoom-in-95 duration-700">
      <div className="w-20 h-20 bg-sbi-light border-2 border-slate-200 rounded-3xl flex items-center justify-center text-sbi-navy font-black text-3xl mb-8 shadow-xl">
        SBI
      </div>
      
      <h2 className="text-3xl font-extrabold text-slate-800 mb-3 tracking-tight">How can I assist your research?</h2>
      <p className="text-sm text-slate-500 max-w-lg mb-12 font-semibold leading-relaxed">
        I am a secured AI assistant trained exclusively on <span className="text-sbi-navy">Official SBI Mutual Fund</span> documentation. I provide strictly factual answers and valid citations.
      </p>

      <div className="grid grid-cols-2 gap-4 w-full max-w-2xl">
        {examples.map((ex) => (
          <button
            key={ex.label}
            onClick={() => onSelect(ex.query)}
            className="p-5 bg-white border border-slate-200 rounded-2xl text-xs font-bold text-slate-700 hover:border-sbi-red hover:shadow-lg transition-all active:scale-[0.98] text-left group flex items-start gap-4"
          >
            <div className="bg-slate-50 p-2 rounded-lg group-hover:bg-red-50 group-hover:text-sbi-red transition-colors shrink-0">
              <MessageSquare size={16} />
            </div>
            <div className="flex flex-col gap-1">
              <span className="opacity-40 uppercase tracking-widest text-[9px]">Suggested Query</span>
              <span className="leading-snug">{ex.label}</span>
            </div>
          </button>
        ))}
      </div>

      <div className="mt-16 flex items-center gap-2 px-4 py-2 bg-sbi-navy/5 text-sbi-navy rounded-full text-[10px] font-bold uppercase tracking-widest">
        <Info size={14} />
        This assistant does not provide investment advice
      </div>
    </div>
  );
};

export default Onboarding;
