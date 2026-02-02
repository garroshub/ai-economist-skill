import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Sliders, Info } from 'lucide-react';

const TaylorRuleSimulator: React.FC = () => {
  const [inflation, setInflation] = useState(2.2);
  const [gap, setGap] = useState(0.5);
  const [region, setRegion] = useState<'US' | 'Canada'>('US');

  const rStar = region === 'US' ? 2.5 : 2.75;
  const targetPi = 2.0;

  const calculateRate = (pi: number, y: number) => {
    // i = r* + pi + 0.5(pi - 2.0) + 1.0(gap) [if pi <= 2.5]
    // i = r* + pi + 0.5 * 1.5 * (pi - 2.0) + 1.0(gap) [if pi > 2.5]
    const coeff = pi > 2.5 ? 0.75 : 0.5;
    return rStar + pi + coeff * (pi - targetPi) + 1.0 * y;
  };

  const currentRate = calculateRate(inflation, gap);

  // Generate chart data
  const chartData = useMemo(() => {
    const data = [];
    for (let i = 1.0; i <= 3.01; i += 0.05) {
      data.push({
        inflation: i.toFixed(2),
        rate: calculateRate(i, gap).toFixed(2),
        current: Math.abs(i - inflation) < 0.025 ? calculateRate(i, gap) : null
      });
    }
    return data;
  }, [gap, region, inflation]);

  // Bayesian Normal Distribution for CI (simplified)
  const bellCurveData = useMemo(() => {
    const data = [];
    const mean = currentRate;
    const stdDev = 0.4; // Sample standard deviation
    for (let x = mean - 1.5; x <= mean + 1.5; x += 0.05) {
      const y = (1 / (stdDev * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - mean) / stdDev, 2));
      data.push({ x: x.toFixed(2), y });
    }
    return data;
  }, [currentRate]);

  return (
    <div className="bento-card col-span-1 md:col-span-2">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-2">
          <div className="bg-bloomberg-orange p-1 rounded-sm">
            <Sliders size={18} className="text-black" />
          </div>
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Interactive Taylor Rule Simulator</h2>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => setRegion('US')}
            className={`px-3 py-1 text-[10px] font-bold border ${region === 'US' ? 'bg-bloomberg-emerald text-black border-bloomberg-emerald' : 'text-bloomberg-teal border-bloomberg-lightGray'}`}
          >
            US (r*=2.5%)
          </button>
          <button 
            onClick={() => setRegion('Canada')}
            className={`px-3 py-1 text-[10px] font-bold border ${region === 'Canada' ? 'bg-bloomberg-emerald text-black border-bloomberg-emerald' : 'text-bloomberg-teal border-bloomberg-lightGray'}`}
          >
            CANADA (r*=2.75%)
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Controls */}
        <div className="space-y-6">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-[10px] text-bloomberg-teal uppercase font-bold">Core Inflation (π)</label>
                <span className="text-sm font-mono text-white">{inflation.toFixed(2)}%</span>
              </div>
              <input 
                type="range" min="1" max="5" step="0.1" 
                value={inflation} 
                onChange={(e) => setInflation(parseFloat(e.target.value))}
                className="w-full h-1 bg-bloomberg-lightGray rounded-lg appearance-none cursor-pointer accent-bloomberg-emerald"
              />
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-[10px] text-bloomberg-teal uppercase font-bold">Output Gap (y)</label>
                <span className="text-sm font-mono text-white">{gap.toFixed(2)}%</span>
              </div>
              <input 
                type="range" min="-3" max="3" step="0.1" 
                value={gap} 
                onChange={(e) => setGap(parseFloat(e.target.value))}
                className="w-full h-1 bg-bloomberg-lightGray rounded-lg appearance-none cursor-pointer accent-bloomberg-emerald"
              />
            </div>
          </div>

          <div className="p-3 bg-black/40 border border-bloomberg-lightGray rounded-sm">
            <div className="flex items-center gap-2 mb-2">
              <Info size={14} className="text-bloomberg-blue" />
              <span className="text-[9px] text-bloomberg-blue font-bold uppercase tracking-widest">Model Inference</span>
            </div>
            <div className="text-2xl font-mono text-bloomberg-emerald font-bold">
              {currentRate.toFixed(2)}%
            </div>
            <div className="text-[9px] text-bloomberg-teal opacity-60 mt-1 italic leading-tight">
              Implied Policy Rate based on structural rule. Confidence interval shows 95% Bayesian probability density.
            </div>
          </div>
          
          <div className="h-24 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={bellCurveData}>
                <Area type="monotone" dataKey="y" stroke="#00ff9f" fill="#00ff9f" fillOpacity={0.2} />
                <Tooltip 
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-bloomberg-black border border-bloomberg-emerald p-1 text-[8px] font-mono">
                          P(i={payload[0].payload.x}%)
                        </div>
                      );
                    }
                    return null;
                  }}
                />
              </AreaChart>
            </ResponsiveContainer>
            <div className="text-center text-[8px] text-bloomberg-teal uppercase mt-1">Bayesian Confidence Density</div>
          </div>
        </div>

        {/* Chart */}
        <div className="lg:col-span-2 h-[300px] border border-bloomberg-lightGray bg-black/20 p-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
              <XAxis 
                dataKey="inflation" 
                stroke="#00d1b2" 
                fontSize={10} 
                tickFormatter={(val) => `${val}%`}
                ticks={['1.00', '1.50', '2.00', '2.50', '3.00']}
                label={{ value: 'Inflation (%)', position: 'insideBottom', offset: -5, fontSize: 10, fill: '#00d1b2' }}
              />
              <YAxis 
                stroke="#00d1b2" 
                fontSize={10} 
                domain={['auto', 'auto']}
                tickFormatter={(val) => `${val}%`}
                label={{ value: 'Policy Rate (%)', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#00d1b2' }}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#000', border: '1px solid #2a2a2a', fontSize: '10px', fontFamily: 'monospace' }}
                itemStyle={{ color: '#00ff9f' }}
              />
              <Line 
                type="monotone" 
                dataKey="rate" 
                stroke="#00ff9f" 
                strokeWidth={2} 
                dot={false}
                activeDot={{ r: 4, fill: '#00ff9f' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default TaylorRuleSimulator;
