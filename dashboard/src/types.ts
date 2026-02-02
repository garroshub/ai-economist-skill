export interface GrowthNowcast {
  nowcast: number;
  confidence: string;
  r2: number;
}

export interface PolicyStance {
  fed: {
    label: string;
    bps: number;
  };
  boc: {
    label: string;
    bps: number;
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
