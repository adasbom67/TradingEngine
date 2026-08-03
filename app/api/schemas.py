from __future__ import annotations
from pydantic import BaseModel, Field, field_validator

class HealthItem(BaseModel):
    name: str
    status: str
    message: str

class HealthResponse(BaseModel):
    version: str
    healthy: bool
    checks: list[HealthItem]

class AccountView(BaseModel):
    masked_id: str
    account_type: str
    selected: bool = False

class AccountListResponse(BaseModel):
    accounts: list[AccountView]
    selected_last_four: str | None = None

class AccountSelectionRequest(BaseModel):
    last_four: str = Field(min_length=4, max_length=4)

class BacktestRequest(BaseModel):
    symbol: str = 'SPY'
    initial_capital: float = 100000
    minimum_entry_dte: int = 30
    maximum_entry_dte: int = 45
    spread_width: float = 5

    @field_validator('symbol')
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value=value.strip().upper()
        if not value: raise ValueError('Symbol is required.')
        return value

    @field_validator('initial_capital','spread_width')
    @classmethod
    def positive(cls, value: float) -> float:
        if value <= 0: raise ValueError('Value must be positive.')
        return value

    @field_validator('maximum_entry_dte')
    @classmethod
    def valid_range(cls, value: int, info):
        minimum = info.data.get('minimum_entry_dte', 1)
        if value < minimum: raise ValueError('Maximum DTE must be at least minimum DTE.')
        return value

class BacktestTradeView(BaseModel):
    entry_date: str
    exit_date: str
    short_strike: float
    long_strike: float
    entry_dte: int
    pnl: float
    exit_reason: str

class GroupMetricView(BaseModel):
    name: str
    trade_count: int
    win_rate: float
    total_pnl: float
    average_pnl: float
    profit_factor: float | None

class BacktestResponse(BaseModel):
    symbol: str
    initial_capital: float
    ending_capital: float
    total_pnl: float
    trade_count: int
    win_rate: float
    profit_factor: float | None
    maximum_drawdown: float
    average_pnl: float
    average_winner: float
    average_loser: float
    minimum_entry_dte: int
    maximum_entry_dte: int
    spread_width: float
    by_regime: list[GroupMetricView]
    by_exit_reason: list[GroupMetricView]
    recent_trades: list[BacktestTradeView]
    equity_curve: list[float]

class RecommendationRequest(BaseModel):
    symbols: list[str] = ['SPY']
    strategy: str = 'Balanced'

    @field_validator('symbols')
    @classmethod
    def normalize_symbols(cls, values: list[str]) -> list[str]:
        result=[]
        for value in values:
            symbol=value.strip().upper()
            if symbol and symbol not in result: result.append(symbol)
        if not result: raise ValueError('At least one symbol is required.')
        return result

class RecommendationView(BaseModel):
    symbol: str
    rank: int
    decision: str
    score: float
    expiration: str
    dte: int
    short_strike: float
    long_strike: float
    short_delta: float
    long_delta: float
    net_position_delta: float
    credit: float
    max_profit: float
    max_loss: float
    breakeven: float
    probability_of_profit: float
    return_on_risk: float
    managed_expected_value: float
    market_regime: str
    reasons: list[str]
    warnings: list[str]

class SymbolScanResult(BaseModel):
    symbol: str
    status: str
    message: str
    recommendations: list[RecommendationView]

class RecommendationResponse(BaseModel):
    strategy: str
    results: list[SymbolScanResult]
    live_submission_available: bool = False
