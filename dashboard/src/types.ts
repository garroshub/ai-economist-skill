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
  windowStart: string;
  windowEnd: string;
  observations: number;
  baselineR2: number;
  calibratedR2: number;
  baselineRmse: number;
  calibratedRmse: number;
  rmseGain: number;
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
