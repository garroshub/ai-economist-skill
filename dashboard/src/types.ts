export interface GrowthNowcast {
  nowcast: number;
  calibratedNowcast: number;
  confidence: string;
  measurementAdj: number;
  mlCalibrationAdj: number;
  targetQuarter: string;
  dataThrough: string;
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
  shrinkageGain: number;
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
