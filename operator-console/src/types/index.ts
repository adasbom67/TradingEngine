export type HealthCheck = { name: string; status: string; message: string };
export type Health = { healthy: boolean; checks: HealthCheck[] };

export type Page =
  | "Dashboard"
  | "Backtesting"
  | "Optimization"
  | "Walk Forward"
  | "Recommendations"
  | "Paper Trading"
  | "Live Trading"
  | "Portfolio"
  | "Operations"
  | "Settings";

export type BacktestResult = {
  configuration: {
    symbol: string;
    initial_capital: number;
    minimum_dte: number;
    maximum_dte: number;
    effective_entry_dte: number;
    spread_width: number;
    period_years: number;
    dte_method: string;
  };
  summary: {
    trade_count: number;
    win_rate: number;
    total_pnl: number;
    ending_capital: number;
    average_pnl: number;
    profit_factor: number | null;
    maximum_drawdown: number;
    average_days_held: number;
    longest_losing_streak: number;
  };
  recent_trades: Array<{
    entry_date: string;
    exit_date: string;
    short_strike: number;
    long_strike: number;
    entry_credit: number;
    pnl: number;
    exit_reason: string;
  }>;
  disclosure: string;
};

export type RecommendationCandidate = {
  symbol: string;
  rank: number;
  decision: string;
  score: number;
  expiration: string;
  dte: number;
  short_strike: number;
  long_strike: number;
  short_delta: number | null;
  long_delta: number | null;
  net_position_delta: number | null;
  credit: number;
  maximum_profit: number;
  maximum_risk: number;
  breakeven: number;
  return_on_risk: number;
  probability_of_profit: number;
  expected_value: number;
  managed_expected_value: number;
  market_regime: string;
  decision_reasons: string[];
  reasons: string[];
  warnings: string[];
  score_breakdown: Record<string, number>;
  spread_width: number;
  selected_pricing_method: string;
  selected_credit: number;
  selected_credit_per_contract: number;
  quote: {
    short_bid: number;
    short_ask: number;
    short_midpoint: number;
    short_volume: number;
    short_open_interest: number;
    long_bid: number;
    long_ask: number;
    long_midpoint: number;
    long_volume: number;
    long_open_interest: number;
    natural_credit: number;
    midpoint_credit: number;
    conservative_credit: number;
    scoring_credit: number;
    quote_timestamp: string | null;
    quote_timestamp_status: string;
    scoring_vs_natural: number;
    scoring_vs_midpoint: number;
    material_difference_threshold: number;
    audit_status: "ALIGNED" | "REVIEW";
    audit_message: string;
  };
};

export type PipelineDiagnostics = {
  total_contracts: number;
  total_puts: number;
  expiration_count: number;
  price_history_bars: number;
  filter_input_puts: number;
  eligible_puts: number;
  pair_attempts: number;
  same_expiration_pairs: number;
  ordered_strike_pairs: number;
  allowed_width_pairs: number;
  minimum_credit_pairs: number;
  valid_credit_pairs: number;
  risk_approved_pairs: number;
  candidates_built: number;
  candidates_evaluated: number;
  portfolio_rejections: number;
  candidates_ranked: number;
  filter_rejections: Record<string, number>;
  builder_rejections: Record<string, number>;
  first_zero_stage: string | null;
  primary_bottleneck: {
    reason: string;
    count: number;
  } | null;
};

export type RecommendationResponse = {
  history_id?: string;
  scanned_at: string;
  symbols: string[];
  constraints: Record<string, unknown>;
  candidates: RecommendationCandidate[];
  diagnostics: Array<{
    symbol: string;
    status: string;
    evaluated_count: number;
    included_count: number;
    rejected_count: number;
    message: string;
    pipeline?: PipelineDiagnostics | null;
  }>;
  pipeline_validation: {
    totals: Record<string, number>;
    delta_distribution: Record<string, number>;
    filter_rejections: Record<string, number>;
    builder_rejections: Record<string, number>;
  };
  summary: {
    candidate_count: number;
    rejected_count: number;
    evaluated_count: number;
    symbols_requested: number;
    symbols_succeeded: number;
    symbols_failed: number;
    elapsed_ms: number;
    outcome: "RESULTS" | "ALL_REJECTED" | "NO_PIPELINE_CANDIDATES" | "ERROR";
    trade_count: number;
    watch_count: number;
    pass_count: number;
  };
  rejection_analysis: Array<{
    reason: string;
    count: number;
    candidate_percent: number;
  }>;
  constraint_impact: Array<{
    reason: string;
    count: number;
    candidate_percent: number;
  }>;
  what_if_hints: Array<{
    constraint: string;
    affected_candidates: string;
    suggestion: string;
  }>;
  diagnostics_disclosure: string;
  execution_mode: string;
  pricing_disclosure: string;
  rejected_candidates: Array<{
    symbol: string;
    expiration: string;
    short_strike: number;
    long_strike: number;
    reasons: string[];
  }>;
};

export type TradingProfile = {
  name: string;
  symbols: string[];
  constraints: Record<string, any>;
  is_default?: boolean;
};

export type ScanHistorySummary = {
  id: string;
  scanned_at: string;
  symbols: string[];
  summary: {
    candidate_count?: number;
    rejected_count?: number;
    trade_count?: number;
    watch_count?: number;
    pass_count?: number;
  };
};

export type PlatformStatus = { status: string; message: string };

export type DashboardData = {
  refreshed_at: string;
  operating_mode: "RESEARCH" | "PAPER" | "LIVE";
  execution_mode: string;
  workspace: string;
  platform: {
    api: PlatformStatus;
    recommendation_engine: PlatformStatus;
    broker: PlatformStatus;
    market_data: PlatformStatus;
    paper_trading: PlatformStatus;
    live_trading: PlatformStatus;
  };
  health: Health;
  latest_scan: null | {
    id: string;
    scanned_at: string;
    symbols: string[];
    candidate_count: number;
    rejected_count: number;
    evaluated_count: number;
    trade_count: number;
    watch_count: number;
    pass_count: number;
    outcome: string;
  };
  portfolio: { status: string; open_positions: number | null; message: string };
  alerts: Array<{ severity: string; title: string; message: string }>;
};

