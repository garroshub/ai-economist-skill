import React from 'react';
import { TrendingUp, Activity, BarChart3 } from 'lucide-react';
import type { GrowthNowcast, PolicyStance } from '../types';

interface Props {
  usGrowth: GrowthNowcast;
  canadaGrowth: GrowthNowcast;
  policyStance: PolicyStance;
}

const LiveSnapshot: React.FC<Props> = ({ usGrowth, canadaGrowth, policyStance }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="bento-card border-l-4 border-l-bloomberg-emerald">
        <div className="flex justify-between items-start mb-2">
          <span className="text-[10px] text-bloomberg-teal font-bold uppercase tracking-wider">US Growth</span>
          <TrendingUp size={16} className="text-bloomberg-emerald" />
        </div>
        <div className="grid grid-cols-2 gap-3 mb-2">
          <div>
            <div className="text-[9px] text-bloomberg-teal opacity-70 uppercase">Baseline</div>
            <div className="text-2xl font-bold text-white">{usGrowth.nowcast.toFixed(2)}%</div>
          </div>
          <div>
            <div className="text-[9px] text-bloomberg-teal opacity-70 uppercase">Calibrated</div>
            <div className="text-2xl font-bold text-bloomberg-emerald">{usGrowth.calibratedNowcast.toFixed(2)}%</div>
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">Target Q</span>
            <span className="text-white font-bold uppercase">{usGrowth.targetQuarter}</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">Data Thru</span>
            <span className="text-white font-bold uppercase">{usGrowth.dataThrough}</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">Confidence</span>
            <span className="text-bloomberg-emerald font-bold uppercase">{usGrowth.confidence}</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">Measurement Adj</span>
            <span className={`font-mono ${usGrowth.measurementAdj >= 0 ? 'text-bloomberg-emerald' : 'text-bloomberg-red'}`}>
              {usGrowth.measurementAdj >= 0 ? '+' : ''}{usGrowth.measurementAdj.toFixed(2)}%
            </span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">ML Calib Adj</span>
            <span className={`font-mono ${usGrowth.mlCalibrationAdj >= 0 ? 'text-bloomberg-emerald' : 'text-bloomberg-red'}`}>
              {usGrowth.mlCalibrationAdj >= 0 ? '+' : ''}{usGrowth.mlCalibrationAdj.toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

      <div className="bento-card border-l-4 border-l-bloomberg-teal">
        <div className="flex justify-between items-start mb-2">
          <span className="text-[10px] text-bloomberg-teal font-bold uppercase tracking-wider">Canada Growth</span>
          <Activity size={16} className="text-bloomberg-teal" />
        </div>
        <div className="grid grid-cols-2 gap-3 mb-2">
          <div>
            <div className="text-[9px] text-bloomberg-teal opacity-70 uppercase">Baseline</div>
            <div className="text-2xl font-bold text-white">{canadaGrowth.nowcast.toFixed(2)}%</div>
          </div>
          <div>
            <div className="text-[9px] text-bloomberg-teal opacity-70 uppercase">Calibrated</div>
            <div className="text-2xl font-bold text-bloomberg-emerald">{canadaGrowth.calibratedNowcast.toFixed(2)}%</div>
          </div>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">Target Q</span>
            <span className="text-white font-bold uppercase">{canadaGrowth.targetQuarter}</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">Data Thru</span>
            <span className="text-white font-bold uppercase">{canadaGrowth.dataThrough}</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">Confidence</span>
            <span className="text-bloomberg-yellow font-bold uppercase">{canadaGrowth.confidence}</span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">Measurement Adj</span>
            <span className={`font-mono ${canadaGrowth.measurementAdj >= 0 ? 'text-bloomberg-emerald' : 'text-bloomberg-red'}`}>
              {canadaGrowth.measurementAdj >= 0 ? '+' : ''}{canadaGrowth.measurementAdj.toFixed(2)}%
            </span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-bloomberg-teal opacity-70 uppercase">ML Calib Adj</span>
            <span className={`font-mono ${canadaGrowth.mlCalibrationAdj >= 0 ? 'text-bloomberg-emerald' : 'text-bloomberg-red'}`}>
              {canadaGrowth.mlCalibrationAdj >= 0 ? '+' : ''}{canadaGrowth.mlCalibrationAdj.toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

      <div className="bento-card border-l-4 border-l-bloomberg-blue">
        <div className="flex justify-between items-start mb-2">
          <span className="text-[10px] text-bloomberg-teal font-bold uppercase tracking-wider">Policy Stance</span>
          <BarChart3 size={16} className="text-bloomberg-blue" />
        </div>
        <div className="grid grid-cols-2 gap-2 mt-2">
          <div className="flex flex-col">
            <span className="text-[9px] text-bloomberg-teal opacity-70 uppercase">Fed</span>
            <span className="text-sm font-bold text-white">{policyStance.fed.label}</span>
            <span className="text-[10px] text-bloomberg-emerald font-mono">+{policyStance.fed.bps}bps</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[9px] text-bloomberg-teal opacity-70 uppercase">BoC</span>
            <span className="text-sm font-bold text-white">{policyStance.boc.label}</span>
            <span className="text-[10px] text-bloomberg-red font-mono">{policyStance.boc.bps}bps</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveSnapshot;
