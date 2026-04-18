import React from 'react';

const Header = () => {
  return (
    <header className="h-16 bg-sbi-navy flex items-center px-8 text-white shrink-0 shadow-md">
      <div className="flex flex-col">
        <h1 className="font-bold text-lg tracking-tight leading-none mb-1">SBI Mutual Fund FAQ Assistant</h1>
        <div className="flex items-center gap-2">
          <span className="text-[9px] text-white/50 uppercase font-bold tracking-widest bg-white/10 px-1.5 py-0.5 rounded">Compliance Engine v1.0</span>
          <span className="text-[10px] text-sbi-red font-black uppercase tracking-[0.15em] bg-white px-2 py-0.5 rounded-sm">Facts-only. No investment advice.</span>
        </div>
      </div>
      
      <div className="ml-auto flex items-center gap-6 text-[10px] font-bold uppercase tracking-wider">
        <span className="opacity-60 hover:opacity-100 cursor-pointer transition-opacity">Our Funds</span>
        <span className="opacity-60 hover:opacity-100 cursor-pointer transition-opacity">Planning Tools</span>
        <span className="px-3 py-1 bg-white/10 rounded-full">Secured</span>
      </div>
    </header>
  );
};

export default Header;
