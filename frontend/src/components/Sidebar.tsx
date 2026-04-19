'use client';

import React from 'react';
import { Plus, Archive, ShieldCheck, Database } from 'lucide-react';

interface SidebarProps {
  onNewChat: () => void;
  onSelectThread: (id: string) => void;
  onClearThread: () => void;
  activeId: string;
  threads: Record<string, any[]>;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  onNewChat, 
  onSelectThread, 
  onClearThread,
  activeId, 
  threads 
}) => {
  return (
    <aside className="w-72 bg-white border-r border-sbi-border flex flex-col shrink-0 animate-in slide-in-from-left duration-300">
      <div className="p-6 flex flex-col gap-6">
        {/* Status Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-[10px] font-bold self-start border border-green-200 uppercase tracking-widest">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          System Live & Secure
        </div>

        {/* Profile Card */}
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-sbi-navy rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-sm">
            AI
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold text-slate-800 leading-tight">Mutual Fund Expert</span>
            <span className="text-[10px] text-slate-500 font-semibold italic">Facts-only Intelligence</span>
          </div>
        </div>

        {/* Main Action */}
        <button 
          onClick={onNewChat}
          className="w-full bg-sbi-red hover:bg-red-700 text-white py-3 rounded-xl flex items-center justify-center gap-2 text-sm font-bold transition-all shadow-md active:scale-95 group"
        >
          <Plus size={18} className="group-hover:rotate-90 transition-transform" />
          New Conversation
        </button>
      </div>

      {/* History Area */}
      <div className="flex-1 overflow-y-auto px-6 py-2 custom-scrollbar">
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3 px-1 text-slate-400">
            <Archive size={12} />
            <h3 className="text-[10px] font-bold uppercase tracking-widest">Recent Activity</h3>
          </div>
          <div className="flex flex-col gap-1.5">
            {Object.keys(threads).length === 0 && (
              <div className="p-4 border border-dashed border-slate-200 rounded-xl text-center">
                <span className="text-[10px] text-slate-400 font-medium">No history found.</span>
              </div>
            )}
            {Object.entries(threads)
              .filter(([_, msgs]) => msgs.length > 0)
              .map(([id, msgs]) => (
              <button
                key={id}
                onClick={() => onSelectThread(id)}
                className={`w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all truncate border ${
                  activeId === id 
                    ? 'bg-sbi-light text-sbi-navy border-sbi-navy shadow-sm' 
                    : 'bg-transparent text-slate-600 border-transparent hover:bg-slate-50'
                }`}
              >
                {msgs.length > 0 ? msgs[0].content : 'Initialization...'}
              </button>
            ))}
          </div>
        </div>

        {/* Fund Catalog */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-4 px-1 text-slate-400">
            <Database size={12} />
            <h3 className="text-[10px] font-bold uppercase tracking-widest">Index Content</h3>
          </div>
          <ul className="flex flex-col gap-3 px-1">
            {[
              'SBI Tax Saver (ELSS)',
              'SBI Mutual Flexicap',
              'SBI Large Cap Fund',
              'SBI Magnum Multiplier',
              'SBI Small Midcap'
            ].map(fund => (
              <li key={fund} className="text-[11px] font-semibold text-slate-500 hover:text-sbi-navy cursor-help flex items-center gap-3 group">
                <div className="w-1 h-1 bg-slate-300 rounded-full group-hover:bg-sbi-navy transition-colors" />
                {fund}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Footer */}
      <div className="p-6 border-t border-sbi-border">
        <button 
          onClick={onClearThread}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-slate-200 text-[10px] font-bold text-slate-400 hover:text-sbi-red hover:border-sbi-red hover:bg-red-50 transition-all active:scale-95"
        >
          Clear Current Thread
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
