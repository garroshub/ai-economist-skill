export interface GrowthNowcast {
  nowcast: number;
  confidence: string;
  sentimentAdj: number;
  targetQuarter: string;
}

export interface PolicyStance {
  fed: {
    label: string;
    bps: number;
    actualRate: number;
  };
  boc: {
    label: string;
    bps: number;
    actualRate: number;
  };
}

export interface BacktestMetric {
  r2: number;
  rmse: number;
  alpha: number;
}

export interface DashboardData {
  liveSnapshot: {
    usGrowth: GrowthNowcast;
    canadaGrowth: GrowthNowcast;
    policyStance: PolicyStance;
  };
  backtest: {
    us: BacktestMetric;
    canada: BacktestMetric;
  };
}
