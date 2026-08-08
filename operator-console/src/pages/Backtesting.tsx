import { BarChart3, BookOpen } from "lucide-react";
import { type FormEvent, useState } from "react";
import type { BacktestResult } from "../types";
import { Metric } from "../components/common/Metric";
import { money } from "../utils/format";
import { apiUrl } from "../api/client";

export function Backtesting() {
  const [symbol, setSymbol] = useState("SPY");
  const [capitalText, setCapitalText] = useState("100,000");
  const [runStatus, setRunStatus] = useState("");
  const [minimumDte, setMinimumDte] = useState(30);
  const [maximumDte, setMaximumDte] = useState(45);
  const [widthPreset, setWidthPreset] = useState("5");
  const [customWidth, setCustomWidth] = useState(7.5);
  const [periodYears, setPeriodYears] = useState(5);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const spreadWidth =
    widthPreset === "custom" ? customWidth : Number(widthPreset);
  const capital = Number(capitalText.replace(/,/g, "")) || 0;

  function updateCapital(raw: string) {
    const digits = raw.replace(/\D/g, "");
    setCapitalText(digits ? Number(digits).toLocaleString("en-US") : "");
  }

  function applyCapitalPreset(value: number) {
    setCapitalText(value.toLocaleString("en-US"));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    setRunStatus("Loading historical prices…");

    const evaluationTimer = window.setTimeout(
      () => setRunStatus("Evaluating strategy signals and trades…"),
      700,
    );
    const reportTimer = window.setTimeout(
      () => setRunStatus("Generating research report…"),
      1800,
    );

    try {
      const response = await fetch(
        apiUrl("/api/backtests"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            symbol,
            initial_capital: capital,
            minimum_dte: minimumDte,
            maximum_dte: maximumDte,
            spread_width: spreadWidth,
            period_years: periodYears,
          }),
        },
      );

      const data = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((item: { msg: string }) => item.msg).join("; ")
          : data.detail;
        throw new Error(detail || "Backtest failed.");
      }
      setResult(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Backtest failed.");
    } finally {
      window.clearTimeout(evaluationTimer);
      window.clearTimeout(reportTimer);
      setRunStatus("");
      setLoading(false);
    }
  }

  return (
    <div className="research-layout">
      <form className="card form-card" onSubmit={submit}>
        <div className="card-title">
          <span>Configuration</span>
          <BookOpen size={18} />
        </div>

        <label>
          Symbol
          <input
            value={symbol}
            maxLength={10}
            onChange={(event) => setSymbol(event.target.value.toUpperCase())}
          />
        </label>

        <label>
          Starting capital
          <div className="money-input">
            <span>$</span>
            <input
              type="text"
              inputMode="numeric"
              value={capitalText}
              onChange={(event) => updateCapital(event.target.value)}
              aria-label="Starting capital"
            />
          </div>
        </label>

        <div className="capital-presets" aria-label="Starting capital presets">
          {[25000, 50000, 100000, 250000, 500000].map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => applyCapitalPreset(value)}
            >
              {value >= 1000 ? `$${value / 1000}K` : `$${value}`}
            </button>
          ))}
        </div>

        <div className="form-row">
          <label>
            Minimum DTE
            <input
              type="number"
              min="8"
              max="180"
              value={minimumDte}
              onChange={(event) => setMinimumDte(Number(event.target.value))}
            />
          </label>

          <label>
            Maximum DTE
            <input
              type="number"
              min="8"
              max="180"
              value={maximumDte}
              onChange={(event) => setMaximumDte(Number(event.target.value))}
            />
          </label>
        </div>

        <label>
          Spread width
          <select
            value={widthPreset}
            onChange={(event) => setWidthPreset(event.target.value)}
          >
            {[1, 2, 3, 5, 10].map((value) => (
              <option key={value} value={String(value)}>
                ${value}
              </option>
            ))}
            <option value="custom">Custom</option>
          </select>
        </label>

        {widthPreset === "custom" && (
          <label>
            Custom width
            <input
              type="number"
              min="0.01"
              max="100"
              step="0.5"
              value={customWidth}
              onChange={(event) => setCustomWidth(Number(event.target.value))}
            />
          </label>
        )}

        <label>
          Historical period
          <select
            value={periodYears}
            onChange={(event) => setPeriodYears(Number(event.target.value))}
          >
            {[2, 3, 5, 10].map((value) => (
              <option key={value} value={value}>
                {value} years
              </option>
            ))}
          </select>
        </label>

        <button className="primary" disabled={loading || capital <= 0}>
          {loading ? "Running backtest…" : "Run backtest"}
        </button>

        {loading && (
          <div className="run-status" role="status" aria-live="polite">
            <span className="spinner" />
            <span>{runStatus}</span>
          </div>
        )}

        <p className="form-note">
          The current engine uses the midpoint of the selected DTE range as one
          representative entry DTE. A full expiration sweep will be added as a
          later research-engine enhancement.
        </p>
      </form>

      <section className="results">
        {error && <div className="error-card">{error}</div>}

        {!result && !error && (
          <article className="card empty-result">
            <BarChart3 size={26} />
            <h2>Research results</h2>
            <p>Configure and run a historical simulation.</p>
          </article>
        )}

        {result && (
          <>
            <div className="result-heading">
              <h2>{result.configuration.symbol} backtest</h2>
              <p>
                {result.configuration.minimum_dte}–
                {result.configuration.maximum_dte} DTE · effective{" "}
                {result.configuration.effective_entry_dte} DTE · $
                {result.configuration.spread_width} width ·{" "}
                {result.configuration.period_years} years
              </p>
            </div>

            <div className="metric-grid">
              <Metric
                label="Trades"
                value={String(result.summary.trade_count)}
              />
              <Metric
                label="Win rate"
                value={`${(result.summary.win_rate * 100).toFixed(1)}%`}
              />
              <Metric
                label="Total P/L"
                value={`${result.summary.total_pnl >= 0 ? "+" : ""}${money.format(result.summary.total_pnl)}`}
                tone={result.summary.total_pnl >= 0 ? "positive" : "negative"}
              />
              <Metric
                label="Ending capital"
                value={money.format(result.summary.ending_capital)}
              />
              <Metric
                label="Profit factor"
                value={
                  result.summary.profit_factor === null
                    ? "∞"
                    : result.summary.profit_factor.toFixed(2)
                }
              />
              <Metric
                label="Max drawdown"
                value={`-${money.format(result.summary.maximum_drawdown)}`}
                tone="negative"
              />
            </div>

            <article className="card table-card">
              <div className="card-title">
                <span>Recent trades</span>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Entry</th>
                      <th>Exit</th>
                      <th>Spread</th>
                      <th>Credit</th>
                      <th>P/L</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.recent_trades
                      .slice()
                      .reverse()
                      .map((trade, index) => (
                        <tr key={`${trade.entry_date}-${index}`}>
                          <td>{trade.entry_date}</td>
                          <td>{trade.exit_date}</td>
                          <td>
                            {trade.short_strike}/{trade.long_strike}
                          </td>
                          <td>${trade.entry_credit.toFixed(2)}</td>
                          <td className={trade.pnl >= 0 ? "positive-text" : "negative-text"}>
                            {trade.pnl >= 0 ? "+" : ""}
                            {money.format(trade.pnl)}
                          </td>
                          <td>{trade.exit_reason.replace(/_/g, " ")}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </article>

            <p className="disclosure">{result.disclosure}</p>
          </>
        )}
      </section>
    </div>
  );
}

