'use client';

import { useState, useEffect, useRef } from 'react';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import ChatMessage from '@/components/ChatMessage';
import Onboarding from '@/components/Onboarding';
import ChatInput from '@/components/ChatInput';
import ComplianceBanner from '@/components/ComplianceBanner';
import { api, ChatMessage as ChatMessageType } from '@/lib/api';

export default function Home() {
  const [threads, setThreads] = useState<Record<string, ChatMessageType[]>>({});
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 1. Initial Session Logic & Persistence
  useEffect(() => {
    const init = async () => {
      // Check for persisted state
      const savedThreads = localStorage.getItem('sbi-mf-threads');
      const savedActiveId = localStorage.getItem('sbi-mf-active-id');
      
      if (savedThreads && savedActiveId) {
        try {
          setThreads(JSON.parse(savedThreads));
          setActiveSessionId(savedActiveId);
          return; // Skip init if rehydrated
        } catch (e) {
          console.error('Failed to parse saved threads');
        }
      }

      try {
        const sid = await api.initSession();
        setThreads({ [sid]: [] });
        setActiveSessionId(sid);
      } catch (err) {
        console.error('Initial session failed:', err);
      }
    };
    init();
  }, []);

  // 1b. Peristence sync
  useEffect(() => {
    if (Object.keys(threads).length > 0) {
      localStorage.setItem('sbi-mf-threads', JSON.stringify(threads));
    }
  }, [threads]);

  useEffect(() => {
    if (activeSessionId) {
      localStorage.setItem('sbi-mf-active-id', activeSessionId);
    }
  }, [activeSessionId]);

  // 2. Smooth Auto-Scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [threads, activeSessionId, isLoading]);

  // 3. Thread Management
  const handleNewChat = async () => {
    try {
      const sid = await api.initSession();
      setThreads(prev => ({ ...prev, [sid]: [] }));
      setActiveSessionId(sid);
    } catch (err) {
      console.error('Failed to start new thread:', err);
    }
  };

  const clearCurrentThread = () => {
    if (activeSessionId) {
      setThreads(prev => ({ ...prev, [activeSessionId]: [] }));
    }
  };

  // 4. Message Orchestration
  const handleSendMessage = async (query: string) => {
    if (!activeSessionId) return;

    // Push user message immediately
    const userMsg: ChatMessageType = { role: 'user', content: query };
    setThreads(prev => ({
      ...prev,
      [activeSessionId]: [...(prev[activeSessionId] || []), userMsg]
    }));

    setIsLoading(true);
    try {
      const response = await api.queryChat(activeSessionId, query);
      const botMsg: ChatMessageType = { 
        role: 'assistant', 
        content: response.answer, 
        payload: response 
      };
      
      setThreads(prev => ({
        ...prev,
        [activeSessionId]: [...(prev[activeSessionId] || []), botMsg]
      }));
    } catch (err) {
      const errorMsg: ChatMessageType = { 
        role: 'assistant', 
        content: 'I managed to encounter a connectivity issue with the facts engine. Please verify the backend status.' 
      };
      setThreads(prev => ({
        ...prev,
        [activeSessionId]: [...(prev[activeSessionId] || []), errorMsg]
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const currentMessages = threads[activeSessionId] || [];

  return (
    <main className="flex flex-col h-screen bg-sbi-light">
      <Header />
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar 
          onNewChat={handleNewChat}
          onSelectThread={setActiveSessionId}
          onClearThread={clearCurrentThread}
          activeId={activeSessionId}
          threads={threads}
        />

        <div className="flex-1 flex flex-col bg-slate-50 relative overflow-hidden">
          <ComplianceBanner />

          {/* Main Conversational Area */}
          <div 
            ref={scrollRef}
            className="flex-1 overflow-y-auto px-12 pb-36 pt-4 scroll-smooth custom-scrollbar"
          >
            {currentMessages.length === 0 ? (
              <Onboarding onSelect={handleSendMessage} />
            ) : (
              <div className="max-w-4xl mx-auto w-full">
                {currentMessages.map((msg, i) => (
                  <ChatMessage 
                    key={i} 
                    message={msg} 
                    isLast={i === currentMessages.length - 1} 
                  />
                ))}
                
                {isLoading && (
                  <div className="flex items-center gap-4 animate-pulse ml-14 mb-8">
                    <div className="w-10 h-10 bg-slate-200 rounded-xl" />
                    <div className="bg-white rounded-2xl h-14 w-64 border border-slate-200 shadow-sm" />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Input Layer */}
          <div className="absolute bottom-0 left-0 right-0 z-10">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
          </div>
        </div>
      </div>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { 
          background: #cbd5e1; 
          border-radius: 10px; 
        }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
      `}</style>
    </main>
  );
}
