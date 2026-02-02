import React from 'react';
import { Terminal } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="terminal-header py-4 px-6 mb-6">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="bg-bloomberg-emerald p-1.5 rounded-sm">
            <Terminal size={24} className="text-black" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-bloomberg-emerald tracking-tight">AI ECONOMIST INTELLIGENCE HUB</h1>
            <p className="text-xs text-bloomberg-teal opacity-80 uppercase tracking-widest">Real-time Macroeconomic Nowcasting & Structural Policy Inference</p>
          </div>
        </div>
        <div className="hidden md:flex gap-6 text-[10px] text-bloomberg-teal uppercase tracking-widest font-bold">
          <div className="flex flex-col border-l border-bloomberg-lightGray pl-3">
            <span>Market Status</span>
            <span className="text-bloomberg-emerald">ACTIVE</span>
          </div>
          <div className="flex flex-col border-l border-bloomberg-lightGray pl-3">
            <span>Terminal ID</span>
            <span className="text-white">AE-7792-X</span>
          </div>
          <div className="flex flex-col border-l border-bloomberg-lightGray pl-3">
            <span>Last Sync</span>
            <span className="text-white">{new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
