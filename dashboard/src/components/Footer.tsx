import React from 'react';
import { Github } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="terminal-header py-6 px-6 mt-12">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <a 
            href="https://github.com/Antigravity/ai-economist-skill" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-bloomberg-teal hover:text-bloomberg-emerald transition-colors text-sm font-bold uppercase tracking-widest"
          >
            <Github size={18} />
            <span>GitHub Repository</span>
          </a>
        </div>
        <div className="text-[10px] text-bloomberg-teal opacity-60 uppercase tracking-[0.2em] text-center md:text-right">
          Built with domain expertise. Enhanced with AI.
          <br />
          © {new Date().getFullYear()} ANTIGRAVITY QUANTITATIVE STRATEGIES
        </div>
      </div>
    </footer>
  );
};

export default Footer;
