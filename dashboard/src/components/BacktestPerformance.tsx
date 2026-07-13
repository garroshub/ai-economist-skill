import React from 'react';
import { History, ShieldCheck, Target, Zap } from 'lucide-react';
import type { BacktestMetric } from '../types';

interface Props {
  us: BacktestMetric;
  canada: BacktestMetric;
}

const BacktestPerformance: React.FC<Props> = ({ us, canada }) => {
  const renderMetric = (label: string, metric: BacktestMetric) => (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[10px] font-bold text-white bg-bloomberg-lightGray px-2 py-0.5 rounded-sm">{label}</span>
        <div className="h-[1px] flex-grow bg-bloomberg-lightGray"></div>
        <span className="text-[9px] text-bloomberg-teal uppercase">{metric.windowStart} - {metric.windowEnd}</span>
      </div>
      <div className="grid grid-cols-3 gap-x-4 gap-y-5">
        <div className="flex flex-col">
          <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
            <Target size={10} />
            <span>Baseline R2</span>
          </div>
          <span className="text-lg font-mono font-bold text-white">{metric.baselineR2.toFixed(4)}</span>
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
            <Target size={10} />
            <span>ML-Cal R2</span>
          </div>
          <span className="text-lg font-mono font-bold text-white">{metric.calibratedR2.toFixed(4)}</span>
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
            <Zap size={10} />
            <span>RMSE Gain</span>
          </div>
          <span className={`text-lg font-mono font-bold ${metric.rmseGain >= 0 ? 'text-bloomberg-emerald' : 'text-bloomberg-red'}`}>
            {metric.rmseGain >= 0 ? '+' : ''}{metric.rmseGain.toFixed(2)}%
          </span>
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
            <ShieldCheck size={10} />
            <span>Base RMSE</span>
          </div>
          <span className="text-sm font-mono font-bold text-white">{metric.baselineRmse.toFixed(2)}%</span>
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
            <ShieldCheck size={10} />
            <span>ML RMSE</span>
          </div>
          <span className="text-sm font-mono font-bold text-white">{metric.calibratedRmse.toFixed(2)}%</span>
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1 text-[9px] text-bloomberg-teal opacity-70 uppercase mb-1">
            <History size={10} />
            <span>Quarters</span>
          </div>
          <span className="text-sm font-mono font-bold text-white">{metric.observations}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="bento-card">
      <div className="flex items-center gap-2 mb-6">
        <div className="bg-bloomberg-teal p-1 rounded-sm">
          <History size={18} className="text-black" />
        </div>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Backtest Performance Metrics</h2>
      </div>

      <div className="space-y-8">
        {renderMetric('USA', us)}
        {renderMetric('CAN', canada)}
      </div>

      <div className="mt-8 pt-4 border-t border-bloomberg-lightGray">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-bloomberg-emerald animate-pulse"></div>
          <span className="text-[9px] text-bloomberg-teal uppercase font-bold tracking-widest">Rolling OOS; quarter start + 105 days; release-lag filtered</span>
        </div>
      </div>
    </div>
  );
};

export default BacktestPerformance;
