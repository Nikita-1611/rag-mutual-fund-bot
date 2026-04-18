'use client';

import React from 'react';
import { AlertTriangle, ShieldAlert } from 'lucide-react';

const ComplianceBanner = () => {
  return (
    <div className="bg-sbi-yellow-bg border border-sbi-yellow-border rounded-2xl p-4 flex gap-4 items-center mx-8 my-6 shadow-sm animate-in fade-in slide-in-from-top-4 duration-1000">
      <div className="bg-sbi-yellow-border/40 p-3 rounded-xl text-sbi-yellow-text shrink-0">
        <ShieldAlert size={24} />
      </div>
      <div className="flex flex-col gap-1">
        <span className="text-[10px] font-black text-sbi-yellow-text uppercase tracking-widest leading-none">Objective Information Only</span>
        <p className="text-xs text-sbi-yellow-text/90 font-bold leading-relaxed italic">
          Disclaimer: This assistant provides factual data from AMC documentation. Calculations, investment advice, and wealth projections are disabled by the security engine.
        </p>
      </div>
    </div>
  );
};

export default ComplianceBanner;
