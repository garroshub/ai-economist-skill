import React, { useEffect, useState } from 'react';
import Header from './Header';
import Footer from './Footer';
import LiveSnapshot from './LiveSnapshot';
import TaylorRuleSimulator from './TaylorRuleSimulator';
import BacktestPerformance from './BacktestPerformance';
import type { DashboardData } from '../types';
import { motion } from 'framer-motion';

const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/ai-economist-skill/snapshot.json')
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading snapshot data:", err);
        // Fallback for local development
        fetch('/snapshot.json')
          .then(res => res.json())
          .then(d => {
            setData(d);
            setLoading(false);
          });
      });
  }, []);

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center font-mono">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-bloomberg-emerald border-t-transparent rounded-full animate-spin"></div>
          <span className="text-bloomberg-emerald uppercase tracking-[0.3em] text-xs">Initializing Terminal...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white font-mono flex flex-col">
      <Header />
      
      <main className="flex-grow max-w-7xl mx-auto w-full px-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6"
        >
          {/* Section 1: Live Snapshot (Top Row) */}
          <div className="lg:col-span-3">
            <LiveSnapshot 
              usGrowth={data.liveSnapshot.usGrowth}
              canadaGrowth={data.liveSnapshot.canadaGrowth}
              policyStance={data.liveSnapshot.policyStance}
            />
          </div>

          {/* Section 2: Taylor Rule Simulator (Left/Middle) */}
          <TaylorRuleSimulator 
            policyStance={data.liveSnapshot.policyStance}
          />

          {/* Section 3: Backtest Performance (Right) */}
          <BacktestPerformance 
            us={data.backtest.us}
            canada={data.backtest.canada}
          />
        </motion.div>
      </main>

      <Footer />
    </div>
  );
};

export default Dashboard;
