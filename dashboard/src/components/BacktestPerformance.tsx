import React from 'react';
import { History, ShieldCheck, Target, Zap } from 'lucide-react';
import type { BacktestMetric } from '../types';

interface Props {
  us: BacktestMetric;
  canada: BacktestMetric;
}

const BacktestPerformance: React.FC<Props> = ({ us, canada }) => {
  return (
    <div className="bento-card">
      <div className="flex items-center gap-2 mb-6">
        <div className="bg-bloomberg-teal p-1 rounded-sm">
          <History size={18} className="text-black" />
        </div>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Backtest Performance Metrics</h2>
      </div>

      <div className="space-y-8">
        {/* US Performance */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px] font-bold text-white bg-bloomberg-lightGray px-2 py-0.5 rounded-sm">USA</span>
            <div className="h-[1px] flex-grow bg-bloomberg-lightGray"></div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex flex-col">
              <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
                <Target size={10} />
                <span>R-Squared</span>
              </div>
              <span className="text-lg font-mono font-bold text-white">{us.r2.toFixed(4)}</span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
                <ShieldCheck size={10} />
                <span>RMSE</span>
              </div>
              <span className="text-lg font-mono font-bold text-white">{us.rmse.toFixed(2)}%</span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
                <Zap size={10} />
                <span>AI Alpha</span>
              </div>
              <span className="text-lg font-mono font-bold text-bloomberg-emerald">+{us.alpha.toFixed(2)}%</span>
            </div>
          </div>
        </div>

        {/* Canada Performance */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px] font-bold text-white bg-bloomberg-lightGray px-2 py-0.5 rounded-sm">CAN</span>
            <div className="h-[1px] flex-grow bg-bloomberg-lightGray"></div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="flex flex-col">
              <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
                <Target size={10} />
                <span>R-Squared</span>
              </div>
              <span className="text-lg font-mono font-bold text-white">{canada.r2.toFixed(4)}</span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
                <ShieldCheck size={10} />
                <span>RMSE</span>
              </div>
              <span className="text-lg font-mono font-bold text-white">{canada.rmse.toFixed(2)}%</span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
                <Zap size={10} />
                <span>AI Alpha</span>
              </div>
              <span className="text-lg font-mono font-bold text-bloomberg-emerald">+{canada.alpha.toFixed(2)}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 pt-4 border-t border-bloomberg-lightGray">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-bloomberg-emerald animate-pulse"></div>
          <span className="text-[9px] text-bloomberg-teal uppercase font-bold tracking-widest">Statistical Significance: 99.2%</span>
        </div>
      </div>
    </div>
  );
};

export default BacktestPerformance;
