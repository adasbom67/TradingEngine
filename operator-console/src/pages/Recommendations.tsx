import { Activity } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import type { RecommendationCandidate, RecommendationResponse, ScanHistorySummary, TradingProfile } from "../types";
import { Metric } from "../components/common/Metric";
import { DecisionBadge, Detail } from "../components/common/RecommendationAtoms";
import { formatDelta, money } from "../utils/format";
import { ConstraintExplorer } from "../components/recommendations/ConstraintExplorer";
import { apiUrl } from "../api/client";

type SchwabConnection = {
  status: "CONNECTED" | "EXPIRING" | "EXPIRED" | "DISCONNECTED" | "INVALID" | "NOT_CONFIGURED";
  configured: boolean;
  requires_reconnect: boolean;
  message: string;
  callback_url?: string;
  refresh_expires_at?: string;
};

export function Recommendations() {
  const [symbolsText, setSymbolsText] = useState("SPY, QQQ, IWM, DIA");
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [selected, setSelected] = useState<RecommendationCandidate | null>(null);
  const [decisionFilter, setDecisionFilter] = useState("ALL");
  const [strategyMode, setStrategyMode] = useState("BOTH");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const [minimumDte, setMinimumDte] = useState("");
  const [maximumDte, setMaximumDte] = useState("");
  const [widthsText, setWidthsText] = useState("");
  const [maximumResults, setMaximumResults] = useState("");
  const [minimumCreditContract, setMinimumCreditContract] = useState("");
  const [minimumCreditWidth, setMinimumCreditWidth] = useState("");
  const [minimumRor, setMinimumRor] = useState("");
  const [minimumPop, setMinimumPop] = useState("");
  const [minimumEv, setMinimumEv] = useState("");
  const [minimumManagedEv, setMinimumManagedEv] = useState("");
  const [minimumDelta, setMinimumDelta] = useState("");
  const [maximumDelta, setMaximumDelta] = useState("");
  const [maximumNetDelta, setMaximumNetDelta] = useState("");
  const [maximumLoss, setMaximumLoss] = useState("");
  const [minimumOi, setMinimumOi] = useState("");
  const [minimumVolume, setMinimumVolume] = useState("");
  const [maximumBidAsk, setMaximumBidAsk] = useState("");
  const [minimumScore, setMinimumScore] = useState("");
  const [pricingMethod, setPricingMethod] = useState("SCORING");
  const [excludeWarnings, setExcludeWarnings] = useState(false);
  const [positiveManagedEv, setPositiveManagedEv] = useState(false);
  const [priceVs20, setPriceVs20] = useState("ANY");
  const [includeTrade, setIncludeTrade] = useState(true);
  const [includeWatch, setIncludeWatch] = useState(true);
  const [includePass, setIncludePass] = useState(false);
  const [profiles, setProfiles] = useState<TradingProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState("");
  const [profileName, setProfileName] = useState("");
  const [profileMessage, setProfileMessage] = useState("");
  const [sortBy, setSortBy] = useState("score");
  const [sortDirection, setSortDirection] = useState("desc");
  const [history, setHistory] = useState<ScanHistorySummary[]>([]);
  const [historyMessage, setHistoryMessage] = useState("");
  const [paperStatus, setPaperStatus] = useState("");
  const [paperSubmitting, setPaperSubmitting] = useState(false);
  const [schwabConnection, setSchwabConnection] = useState<SchwabConnection | null>(null);
  const [schwabFlowOpen, setSchwabFlowOpen] = useState(false);
  const [schwabAuthorizationUrl, setSchwabAuthorizationUrl] = useState("");
  const [schwabRedirectUrl, setSchwabRedirectUrl] = useState("");
  const [schwabMessage, setSchwabMessage] = useState("");
  const [schwabBusy, setSchwabBusy] = useState(false);

  useEffect(() => {
    fetch(apiUrl("/api/trading-profiles"))
      .then((response) => response.json())
      .then((data) => setProfiles(data.profiles ?? []))
      .catch(() => setProfiles([]));
    fetch(apiUrl("/api/recommendations/history"))
      .then((response) => response.json())
      .then((data) => setHistory(data.history ?? []))
      .catch(() => setHistory([]));
    refreshSchwabStatus();
  }, []);

  async function refreshSchwabStatus() {
    try {
      const response = await fetch(apiUrl("/api/schwab/status"));
      if (!response.ok) throw new Error("Status request failed.");
      setSchwabConnection(await response.json());
    } catch {
      setSchwabConnection(null);
    }
  }

  async function beginSchwabReconnect() {
    setSchwabBusy(true);
    setSchwabMessage("");
    setSchwabRedirectUrl("");
    try {
      const response = await fetch(apiUrl("/api/schwab/authorize"), { method: "POST" });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Could not start Schwab authorization.");
      setSchwabAuthorizationUrl(payload.authorization_url);
      setSchwabFlowOpen(true);
      setSchwabMessage("Complete the Schwab login, then copy the entire callback URL from the browser address bar.");
      window.open(payload.authorization_url, "_blank", "noopener,noreferrer");
    } catch (caught) {
      setSchwabMessage(caught instanceof Error ? caught.message : "Could not start Schwab authorization.");
    } finally {
      setSchwabBusy(false);
    }
  }

  async function completeSchwabReconnect() {
    if (!schwabRedirectUrl.trim()) {
      setSchwabMessage("Paste the entire callback URL first.");
      return;
    }
    setSchwabBusy(true);
    setSchwabMessage("Securely exchanging the one-time code with Schwab…");
    try {
      const response = await fetch(apiUrl("/api/schwab/authorize/complete"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ redirect_url: schwabRedirectUrl.trim() }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Schwab reconnection failed.");
      setSchwabConnection(payload);
      setSchwabRedirectUrl("");
      setSchwabAuthorizationUrl("");
      setSchwabFlowOpen(false);
      setSchwabMessage("Schwab reconnected successfully. You can run the scan now.");
      setError("");
    } catch (caught) {
      setSchwabMessage(caught instanceof Error ? caught.message : "Schwab reconnection failed.");
    } finally {
      setSchwabBusy(false);
    }
  }

  function optionalNumber(value: string) {
    return value.trim() === "" ? null : Number(value);
  }

  function currentSymbols() {
    return symbolsText
      .split(/[\s,]+/)
      .map((symbol) => symbol.trim().toUpperCase())
      .filter(Boolean);
  }

  function currentConstraints() {
    const allowedWidths = widthsText
      .split(/[\s,]+/)
      .map(Number)
      .filter((value) => Number.isFinite(value) && value > 0);
    const includeDecisions = [
      includeTrade ? "TRADE" : null,
      includeWatch ? "WATCH" : null,
      includePass ? "PASS" : null,
    ].filter(Boolean);
    return {
      minimum_dte: optionalNumber(minimumDte),
      maximum_dte: optionalNumber(maximumDte),
      allowed_spread_widths: allowedWidths.length ? allowedWidths : null,
      maximum_results_per_symbol: optionalNumber(maximumResults),
      minimum_credit_per_contract: optionalNumber(minimumCreditContract),
      minimum_credit_percent_of_width: minimumCreditWidth === "" ? null : Number(minimumCreditWidth) / 100,
      minimum_return_on_risk: minimumRor === "" ? null : Number(minimumRor) / 100,
      minimum_probability_of_profit: minimumPop === "" ? null : Number(minimumPop) / 100,
      minimum_expected_value: optionalNumber(minimumEv),
      minimum_managed_expected_value: optionalNumber(minimumManagedEv),
      minimum_short_delta: optionalNumber(minimumDelta),
      maximum_short_delta: optionalNumber(maximumDelta),
      maximum_absolute_net_delta: optionalNumber(maximumNetDelta),
      maximum_loss_per_contract: optionalNumber(maximumLoss),
      minimum_open_interest: optionalNumber(minimumOi),
      minimum_volume: optionalNumber(minimumVolume),
      maximum_bid_ask_spread: optionalNumber(maximumBidAsk),
      minimum_score: optionalNumber(minimumScore),
      include_decisions: includeDecisions.length ? includeDecisions : null,
      exclude_candidates_with_warnings: excludeWarnings,
      require_positive_managed_expected_value: positiveManagedEv,
      price_vs_20_sma: priceVs20,
      pricing_method: pricingMethod,
    };
  }

  function applyProfile(profile: TradingProfile) {
    const c = profile.constraints ?? {};
    setSymbolsText(profile.symbols.join(", "));
    const profileStrategies = profile.strategies ?? ["BULL_PUT"];
    setStrategyMode(profileStrategies.length === 2 ? "BOTH" : profileStrategies[0]);
    setMinimumDte(c.minimum_dte == null ? "" : String(c.minimum_dte));
    setMaximumDte(c.maximum_dte == null ? "" : String(c.maximum_dte));
    setWidthsText(Array.isArray(c.allowed_spread_widths) ? c.allowed_spread_widths.join(", ") : "");
    setMaximumResults(c.maximum_results_per_symbol == null ? "" : String(c.maximum_results_per_symbol));
    setMinimumCreditContract(c.minimum_credit_per_contract == null ? "" : String(c.minimum_credit_per_contract));
    setMinimumCreditWidth(c.minimum_credit_percent_of_width == null ? "" : String(Number(c.minimum_credit_percent_of_width) * 100));
    setMinimumRor(c.minimum_return_on_risk == null ? "" : String(Number(c.minimum_return_on_risk) * 100));
    setMinimumPop(c.minimum_probability_of_profit == null ? "" : String(Number(c.minimum_probability_of_profit) * 100));
    setMinimumEv(c.minimum_expected_value == null ? "" : String(c.minimum_expected_value));
    setMinimumManagedEv(c.minimum_managed_expected_value == null ? "" : String(c.minimum_managed_expected_value));
    setMinimumDelta(c.minimum_short_delta == null ? "" : String(c.minimum_short_delta));
    setMaximumDelta(c.maximum_short_delta == null ? "" : String(c.maximum_short_delta));
    setMaximumNetDelta(c.maximum_absolute_net_delta == null ? "" : String(c.maximum_absolute_net_delta));
    setMaximumLoss(c.maximum_loss_per_contract == null ? "" : String(c.maximum_loss_per_contract));
    setMinimumOi(c.minimum_open_interest == null ? "" : String(c.minimum_open_interest));
    setMinimumVolume(c.minimum_volume == null ? "" : String(c.minimum_volume));
    setMaximumBidAsk(c.maximum_bid_ask_spread == null ? "" : String(c.maximum_bid_ask_spread));
    setMinimumScore(c.minimum_score == null ? "" : String(c.minimum_score));
    setPricingMethod(c.pricing_method ?? "SCORING");
    setExcludeWarnings(Boolean(c.exclude_candidates_with_warnings));
    setPositiveManagedEv(Boolean(c.require_positive_managed_expected_value));
    setPriceVs20(c.price_vs_20_sma ?? "ANY");
    const decisions = Array.isArray(c.include_decisions) ? c.include_decisions : ["TRADE", "WATCH", "PASS"];
    setIncludeTrade(decisions.includes("TRADE"));
    setIncludeWatch(decisions.includes("WATCH"));
    setIncludePass(decisions.includes("PASS"));
    setProfileMessage(`Loaded ${profile.name}.`);
  }

  async function saveProfile() {
    const name = profileName.trim();
    if (!name) { setProfileMessage("Enter a profile name first."); return; }
    const response = await fetch(apiUrl("/api/trading-profiles"), {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({name, symbols: currentSymbols(), strategies: strategyMode === "BOTH" ? ["BULL_PUT", "BEAR_CALL"] : [strategyMode], constraints: currentConstraints()}),
    });
    const data = await response.json();
    if (!response.ok) { setProfileMessage(data.detail ?? "Could not save profile."); return; }
    const refreshed = await fetch(apiUrl("/api/trading-profiles")).then((r)=>r.json());
    setProfiles(refreshed.profiles ?? []); setSelectedProfile(data.profile.name); setProfileMessage(`Saved ${data.profile.name}.`);
  }

  async function deleteProfile() {
    if (!selectedProfile) { setProfileMessage("Select a saved profile first."); return; }
    const response = await fetch(apiUrl(`/api/trading-profiles/${encodeURIComponent(selectedProfile)}`), {method:"DELETE"});
    if (!response.ok) { setProfileMessage("Could not delete profile."); return; }
    setProfiles((items)=>items.filter((item)=>item.name!==selectedProfile)); setSelectedProfile(""); setProfileMessage("Profile deleted.");
  }

  async function renameProfile() {
    if (!selectedProfile) { setProfileMessage("Select a saved profile first."); return; }
    const newName = window.prompt("New profile name", selectedProfile)?.trim();
    if (!newName || newName === selectedProfile) return;
    const response = await fetch(apiUrl(`/api/trading-profiles/${encodeURIComponent(selectedProfile)}/rename`), {method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({new_name:newName})});
    const data = await response.json();
    if (!response.ok) { setProfileMessage(data.detail ?? "Could not rename profile."); return; }
    const refreshed = await fetch(apiUrl("/api/trading-profiles")).then((r)=>r.json());
    setProfiles(refreshed.profiles ?? []); setSelectedProfile(data.profile.name); setProfileName(data.profile.name); setProfileMessage(`Renamed to ${data.profile.name}.`);
  }

  async function duplicateProfile() {
    if (!selectedProfile) { setProfileMessage("Select a saved profile first."); return; }
    const newName = window.prompt("Name for duplicated profile", `${selectedProfile} Copy`)?.trim();
    if (!newName) return;
    const response = await fetch(apiUrl(`/api/trading-profiles/${encodeURIComponent(selectedProfile)}/duplicate`), {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({new_name:newName})});
    const data = await response.json();
    if (!response.ok) { setProfileMessage(data.detail ?? "Could not duplicate profile."); return; }
    const refreshed = await fetch(apiUrl("/api/trading-profiles")).then((r)=>r.json());
    setProfiles(refreshed.profiles ?? []); setSelectedProfile(data.profile.name); setProfileName(data.profile.name); setProfileMessage(`Duplicated as ${data.profile.name}.`);
  }

  async function setDefaultProfile() {
    if (!selectedProfile) { setProfileMessage("Select a saved profile first."); return; }
    const response = await fetch(apiUrl(`/api/trading-profiles/${encodeURIComponent(selectedProfile)}/default`), {method:"PUT"});
    const data = await response.json();
    if (!response.ok) { setProfileMessage(data.detail ?? "Could not set default profile."); return; }
    const refreshed = await fetch(apiUrl("/api/trading-profiles")).then((r)=>r.json());
    setProfiles(refreshed.profiles ?? []); setProfileMessage(`${data.profile.name} is now the default.`);
  }

  async function loadHistory(historyId: string) {
    if (!historyId) return;
    setHistoryMessage("Loading saved scanâ€¦");
    const response = await fetch(apiUrl(`/api/recommendations/history/${historyId}`));
    const data = await response.json();
    if (!response.ok) { setHistoryMessage(data.detail ?? "Could not load scan history."); return; }
    setResult(data.scan); setSelected(data.scan.candidates?.[0] ?? null);
    if (Array.isArray(data.scan.strategies)) {
      setStrategyMode(data.scan.strategies.length === 2 ? "BOTH" : data.scan.strategies[0]);
    }
    setHistoryMessage(`Loaded scan from ${new Date(data.scan.scanned_at).toLocaleString()}.`);
  }

  async function scan(event: FormEvent) {
    event.preventDefault();
    const symbols = currentSymbols();
    const constraints = currentConstraints();

    setLoading(true);
    setStatus("Loading Schwab market history and option chainsâ€¦");
    setError("");
    setResult(null);
    setSelected(null);

    const timer = window.setTimeout(
      () => setStatus("Applying hard constraints and evaluating candidatesâ€¦"),
      900,
    );

    try {
      const response = await fetch(
        apiUrl("/api/recommendations/scan"),
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            symbols,
            strategies: strategyMode === "BOTH" ? ["BULL_PUT", "BEAR_CALL"] : [strategyMode],
            constraints,
          }),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((item: { msg: string }) => item.msg).join("; ")
          : typeof data.detail === "object"
            ? data.detail.message
            : data.detail;
        if (response.status === 401 && data.detail?.code === "SCHWAB_RECONNECT_REQUIRED") {
          setSchwabConnection((current) => ({
            status: "EXPIRED",
            configured: current?.configured ?? true,
            requires_reconnect: true,
            callback_url: current?.callback_url,
            message: detail || "Schwab must be reconnected.",
          }));
          setSchwabFlowOpen(true);
        }
        throw new Error(detail || "Recommendation scan failed.");
      }
      setResult(data);
      setSelected(data.candidates[0] ?? null);
      fetch(apiUrl("/api/recommendations/history")).then((response)=>response.json()).then((historyData)=>setHistory(historyData.history ?? [])).catch(()=>undefined);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Recommendation scan failed.",
      );
    } finally {
      window.clearTimeout(timer);
      setStatus("");
      setLoading(false);
    }
  }

  async function executePaperTrade(candidate: RecommendationCandidate) {
    const requested = window.prompt(
      `Paper contracts for ${candidate.symbol} ${candidate.short_strike}/${candidate.long_strike}`,
      "1",
    );
    if (requested == null) return;

    const quantity = Number(requested);
    if (!Number.isInteger(quantity) || quantity <= 0) {
      setPaperStatus("Enter a positive whole-number contract quantity.");
      return;
    }

    const confirmed = window.confirm(
      [
        "SIMULATION ONLY â€” no Schwab order will be submitted.",
        candidate.decision === "WATCH"
          ? "EXPERIMENTAL WATCH â€” this candidate was not approved as a TRADE."
          : "Approved TRADE recommendation.",
        "",
        `${candidate.symbol} ${(candidate.strategy_name ?? "Bull Put Credit Spread").toLowerCase()}`,
        `Expiration: ${candidate.expiration}`,
        `Short / long strikes: ${candidate.short_strike} / ${candidate.long_strike}`,
        `Credit: $${candidate.selected_credit.toFixed(2)} per spread`,
        `Quantity: ${quantity}`,
        `Maximum risk: ${money.format(candidate.maximum_risk * quantity)}`,
      ].join("\n"),
    );
    if (!confirmed) return;

    setPaperSubmitting(true);
    setPaperStatus("Creating simulated paper positionâ€¦");

    try {
      const response = await fetch(apiUrl("/api/paper/positions"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: candidate.symbol,
          expiration: candidate.expiration,
          short_strike: candidate.short_strike,
          long_strike: candidate.long_strike,
          entry_credit: candidate.selected_credit,
          quantity,
          entry_decision: candidate.decision,
          allow_watch_simulation: candidate.decision === "WATCH",
          entry_score: candidate.score,
          entry_thesis: candidate.decision_reasons,
          entry_reasons: candidate.reasons,
          entry_warnings: candidate.warnings,
          entry_constraints: result?.constraints ?? {},
          market_regime: candidate.market_regime,
          source_scan_reference: result?.history_id ?? result?.scanned_at ?? null,
          selected_pricing_method: candidate.selected_pricing_method,
          quote_audit_status: candidate.quote.audit_status,
          strategy_type: candidate.strategy_type ?? "BULL_PUT",
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Could not create paper position.");
      }
      setPaperStatus(
        `${candidate.symbol} paper position created. Open Paper Trading to review it.`,
      );
    } catch (caught) {
      setPaperStatus(
        caught instanceof Error ? caught.message : "Paper trade creation failed.",
      );
    } finally {
      setPaperSubmitting(false);
    }
  }

  const visibleCandidates =
    (result?.candidates.filter((candidate) => decisionFilter === "ALL" || candidate.decision === decisionFilter) ?? []).slice().sort((left, right) => {
      const values: Record<string, (candidate: RecommendationCandidate) => number> = {
        score: (candidate) => candidate.score, credit: (candidate) => candidate.selected_credit, return_on_risk: (candidate) => candidate.return_on_risk, probability_of_profit: (candidate) => candidate.probability_of_profit, expected_value: (candidate) => candidate.expected_value, managed_expected_value: (candidate) => candidate.managed_expected_value, expiration: (candidate) => new Date(candidate.expiration).getTime(),
      };
      const difference = values[sortBy](left) - values[sortBy](right);
      return sortDirection === "asc" ? difference : -difference;
    });

  return (
    <div className="recommendations-workspace">
      <article className={`card schwab-connection-card ${schwabConnection?.status.toLowerCase() ?? "unknown"}`}>
        <div>
          <p className="eyebrow">SCHWAB MARKET DATA</p>
          <h3>{schwabConnection?.status === "CONNECTED" ? "Connected" : schwabConnection?.status === "EXPIRING" ? "Connected · renewal due soon" : schwabConnection ? "Reconnect required" : "Checking connection…"}</h3>
          <p>{schwabConnection?.message ?? "Reading the locally saved connection status."}</p>
        </div>
        <button type="button" className="primary" disabled={schwabBusy || !schwabConnection?.configured} onClick={beginSchwabReconnect}>
          {schwabBusy ? "Working…" : schwabConnection?.requires_reconnect ? "Reconnect Schwab" : "Renew Schwab connection"}
        </button>
      </article>

      {(schwabFlowOpen || schwabMessage) && (
        <article className="card schwab-reconnect-panel">
          <div className="schwab-reconnect-heading">
            <div><p className="eyebrow">SECURE REAUTHORIZATION</p><h3>Reconnect Schwab</h3></div>
            {schwabFlowOpen && <button type="button" onClick={() => setSchwabFlowOpen(false)}>Close</button>}
          </div>
          {schwabFlowOpen && (
            <>
              <ol>
                <li>Complete the Schwab login in the browser window.</li>
                <li>At the callback page, copy the entire URL from the address bar.</li>
                <li>Paste it below and select <strong>Finish connection</strong>.</li>
              </ol>
              {schwabAuthorizationUrl && <a href={schwabAuthorizationUrl} target="_blank" rel="noreferrer">Open Schwab login again</a>}
              <label>Schwab callback URL<input type="password" autoComplete="off" value={schwabRedirectUrl} onChange={(event) => setSchwabRedirectUrl(event.target.value)} placeholder={schwabConnection?.callback_url ? `${schwabConnection.callback_url}/?code=…` : "Paste the entire callback URL"}/></label>
              <div className="schwab-reconnect-actions">
                <button type="button" className="primary" disabled={schwabBusy} onClick={completeSchwabReconnect}>{schwabBusy ? "Connecting…" : "Finish connection"}</button>
                <span>The callback is sent only to the TradingEngine service running on this computer.</span>
              </div>
            </>
          )}
          {schwabMessage && <p className="schwab-message">{schwabMessage}</p>}
        </article>
      )}
      <article className="card profile-toolbar">
        <label>Saved profile<select value={selectedProfile} onChange={(event)=>{const name=event.target.value; setSelectedProfile(name); const profile=profiles.find((item)=>item.name===name); if(profile) applyProfile(profile);}}><option value="">None â€” current criteria</option>{profiles.map((profile)=><option key={profile.name} value={profile.name}>{profile.is_default ? "â˜… " : ""}{profile.name}</option>)}</select></label>
        <label>Profile name<input value={profileName} onChange={(event)=>setProfileName(event.target.value)} placeholder="Example: Conservative Income"/></label>
        <button type="button" onClick={saveProfile}>Save / update</button>
        <button type="button" onClick={renameProfile}>Rename</button>
        <button type="button" onClick={duplicateProfile}>Duplicate</button>
        <button type="button" onClick={setDefaultProfile}>Set default</button>
        <button type="button" className="danger-button" onClick={deleteProfile}>Delete</button>
        {profileMessage && <span className="profile-message">{profileMessage}</span>}
      </article>
      <article className="card trust-toolbar">
        <label>Sort recommendations<select value={sortBy} onChange={(event)=>setSortBy(event.target.value)}><option value="score">Score</option><option value="credit">Selected credit</option><option value="return_on_risk">Return on risk</option><option value="probability_of_profit">Probability of profit</option><option value="expected_value">Expected value</option><option value="managed_expected_value">Managed EV</option><option value="expiration">Expiration</option></select></label>
        <label>Direction<select value={sortDirection} onChange={(event)=>setSortDirection(event.target.value)}><option value="desc">Highest first</option><option value="asc">Lowest first</option></select></label>
        <label>Recommendation history<select defaultValue="" onChange={(event)=>loadHistory(event.target.value)}><option value="">Select a prior scan</option>{history.map((entry)=><option key={entry.id} value={entry.id}>{new Date(entry.scanned_at).toLocaleString()} Â· {entry.symbols.join(", ")} Â· {entry.summary.candidate_count ?? 0} included</option>)}</select></label>
        {historyMessage && <span className="profile-message">{historyMessage}</span>}
      </article>
      <form className="constraints-form" onSubmit={scan}>
        <article className="card scan-toolbar">
          <label>
            Symbols
            <input
              value={symbolsText}
              onChange={(event) => setSymbolsText(event.target.value)}
              placeholder="SPY, QQQ, IWM, DIA"
            />
          </label>
          <label>
            Strategy
            <select value={strategyMode} onChange={(event) => setStrategyMode(event.target.value)}>
              <option value="BOTH">Bull Put + Bear Call</option>
              <option value="BULL_PUT">Bull Put only</option>
              <option value="BEAR_CALL">Bear Call only</option>
            </select>
          </label>
          <label>
            Display decision
            <select
              value={decisionFilter}
              onChange={(event) => setDecisionFilter(event.target.value)}
            >
              <option value="ALL">All included decisions</option>
              <option value="TRADE">TRADE</option>
              <option value="WATCH">WATCH</option>
              <option value="PASS">PASS</option>
            </select>
          </label>
          <button className="primary scan-button" disabled={loading || Boolean(schwabConnection?.requires_reconnect)}>
            {loading ? "Scanningâ€¦" : "Run constrained scan"}
          </button>
        </article>

        <div className="constraint-groups">
          <details className="card constraint-group" open>
            <summary>1. Universe</summary>
            <div className="constraint-grid">
              <label>Maximum results per symbol<input type="number" min="1" value={maximumResults} onChange={(e)=>setMaximumResults(e.target.value)}/></label>
              <label>Pricing method<select value={pricingMethod} onChange={(e)=>setPricingMethod(e.target.value)}><option value="SCORING">Existing scoring credit</option><option value="NATURAL">Natural credit</option><option value="MIDPOINT">Midpoint credit</option><option value="CONSERVATIVE">Conservative estimate</option></select></label>
            </div>
          </details>

          <details className="card constraint-group">
            <summary>2. Structure</summary>
            <div className="constraint-grid">
              <label>Minimum DTE<input type="number" min="0" value={minimumDte} onChange={(e)=>setMinimumDte(e.target.value)}/></label>
              <label>Maximum DTE<input type="number" min="0" value={maximumDte} onChange={(e)=>setMaximumDte(e.target.value)}/></label>
              <label className="span-field">Allowed spread widths<input value={widthsText} onChange={(e)=>setWidthsText(e.target.value)} placeholder="Blank = Bull Put 3/5/10; Bear Call 2/3/5"/></label>
              <label>Minimum short |Delta|<input type="number" min="0" max="1" step=".01" value={minimumDelta} onChange={(e)=>setMinimumDelta(e.target.value)}/></label>
              <label>Maximum short |Delta|<input type="number" min="0" max="1" step=".01" value={maximumDelta} onChange={(e)=>setMaximumDelta(e.target.value)}/></label>
              <label>Maximum absolute net Delta<input type="number" min="0" step=".01" value={maximumNetDelta} onChange={(e)=>setMaximumNetDelta(e.target.value)}/></label>
            </div>
          </details>

          <details className="card constraint-group">
            <summary>3. Credit & Return</summary>
            <div className="constraint-grid">
              <label>Minimum credit / contract ($)<input type="number" min="0" step="1" value={minimumCreditContract} onChange={(e)=>setMinimumCreditContract(e.target.value)}/></label>
              <label>Minimum credit / width (%)<input type="number" min="0" max="100" step=".1" value={minimumCreditWidth} onChange={(e)=>setMinimumCreditWidth(e.target.value)}/></label>
              <label>Minimum return on risk (%)<input type="number" min="0" step=".1" value={minimumRor} onChange={(e)=>setMinimumRor(e.target.value)}/></label>
              <label>Minimum POP (%)<input type="number" min="0" max="100" step=".1" value={minimumPop} onChange={(e)=>setMinimumPop(e.target.value)}/></label>
              <label>Minimum expected value ($)<input type="number" step=".01" value={minimumEv} onChange={(e)=>setMinimumEv(e.target.value)}/></label>
              <label>Minimum managed EV ($)<input type="number" step=".01" value={minimumManagedEv} onChange={(e)=>setMinimumManagedEv(e.target.value)}/></label>
            </div>
          </details>

          <details className="card constraint-group">
            <summary>4. Risk & Liquidity</summary>
            <div className="constraint-grid">
              <label>Maximum loss / contract ($)<input type="number" min="1" value={maximumLoss} onChange={(e)=>setMaximumLoss(e.target.value)}/></label>
              <label>Optional minimum open interest, each leg<input type="number" min="0" value={minimumOi} onChange={(e)=>setMinimumOi(e.target.value)}/></label>
              <label>Optional minimum volume, each leg<input type="number" min="0" value={minimumVolume} onChange={(e)=>setMinimumVolume(e.target.value)}/></label>
              <label>Optional maximum bid-ask spread, each leg ($)<input type="number" min="0" step=".01" value={maximumBidAsk} onChange={(e)=>setMaximumBidAsk(e.target.value)}/></label>
              <p className="span-field constraint-note">Baseline liquidity: short-leg OI ≥ 100 and regular-hours volume ≥ 10; protective-leg OI ≥ 25 with no volume minimum. Quote widths are evaluated relative to each option midpoint.</p>
            </div>
          </details>

          <details className="card constraint-group">
            <summary>5. Trend & Decision Quality</summary>
            <div className="constraint-grid">
              <label>Price vs 20-day SMA<select value={priceVs20} onChange={(e)=>setPriceVs20(e.target.value)}><option value="ANY">Any</option><option value="ABOVE">Above</option><option value="BELOW">Below</option></select></label>
              <label>Minimum overall score<input type="number" min="0" max="100" step=".1" value={minimumScore} onChange={(e)=>setMinimumScore(e.target.value)}/></label>
              <fieldset className="span-field"><legend>Decisions eligible for recommendation</legend><label><input type="checkbox" checked={includeTrade} onChange={(e)=>setIncludeTrade(e.target.checked)}/> TRADE</label><label><input type="checkbox" checked={includeWatch} onChange={(e)=>setIncludeWatch(e.target.checked)}/> WATCH</label><label><input type="checkbox" checked={includePass} onChange={(e)=>setIncludePass(e.target.checked)}/> PASS</label></fieldset>
              <label className="checkbox-label"><input type="checkbox" checked={excludeWarnings} onChange={(e)=>setExcludeWarnings(e.target.checked)}/> Exclude candidates with warnings</label>
              <label className="checkbox-label"><input type="checkbox" checked={positiveManagedEv} onChange={(e)=>setPositiveManagedEv(e.target.checked)}/> Require positive managed EV</label>
            </div>
          </details>
        </div>
      </form>

      {loading && <div className="run-status recommendations-status" role="status"><span className="spinner"/><span>{status}</span></div>}
      {error && <div className="error-card">{error}</div>}

      {result && (
        <>
          {result.market_session?.provisional && (
            <article className="card provisional-scan-banner" role="status">
              <div>
                <p className="eyebrow">PROVISIONAL OFF-HOURS SCAN</p>
                <h3>{result.market_session.status.replace("_", " ")}</h3>
                <p>{result.market_session.message} Re-scan during regular market hours before acting on prices.</p>
              </div>
            </article>
          )}
          <div className="recommendation-summary diagnostics-summary">
            <Metric label="Evaluated" value={String(result.summary.evaluated_count)} />
            <Metric label="Included" value={String(result.summary.candidate_count)} />
            <Metric label="Rejected" value={String(result.summary.rejected_count)} />
            <Metric label="Elapsed" value={`${(result.summary.elapsed_ms / 1000).toFixed(2)}s`} />
          </div>
          <article className={`card scan-outcome ${result.summary.outcome.toLowerCase()}`}>
            <div>
              <p className="eyebrow">SCAN OUTCOME</p>
              <h2>{result.summary.outcome === "RESULTS" ? "Qualified recommendations found" : result.summary.outcome === "ALL_REJECTED" ? "Candidates evaluated; all were rejected" : result.summary.outcome === "NO_PIPELINE_CANDIDATES" ? "No candidates reached constraint evaluation" : "Scan encountered an error"}</h2>
              <p>{result.summary.symbols_succeeded} of {result.summary.symbols_requested} symbols completed successfully. {result.summary.symbols_failed ? `${result.summary.symbols_failed} failed.` : ""}</p>
            </div>
          </article>
          <ConstraintExplorer
            distribution={result.pipeline_validation.delta_distribution ?? {}}
            filterRejections={result.pipeline_validation.filter_rejections ?? {}}
            minimumDelta={typeof result.constraints.minimum_short_delta === "number" ? result.constraints.minimum_short_delta : null}
            maximumDelta={typeof result.constraints.maximum_short_delta === "number" ? result.constraints.maximum_short_delta : null}
          />
          <article className="card pipeline-validation-card">
            <div className="pipeline-validation-header">
              <div>
                <p className="eyebrow">Recommendation pipeline validation</p>
                <h3>Candidate-generation funnel</h3>
              </div>
              <span>Live Schwab scan</span>
            </div>
            <div className="pipeline-funnel">
              {[
                ["Contracts", result.pipeline_validation.totals.total_contracts],
                ["Option legs", (result.pipeline_validation.totals.total_puts ?? 0) + (result.pipeline_validation.totals.total_calls ?? 0)],
                ["Eligible short legs", (result.pipeline_validation.totals.eligible_puts ?? 0) + (result.pipeline_validation.totals.eligible_calls ?? 0)],
                ["Valid widths", result.pipeline_validation.totals.allowed_width_pairs],
                ["Credit passed", result.pipeline_validation.totals.minimum_credit_pairs],
                ["Risk passed", result.pipeline_validation.totals.risk_approved_pairs],
                ["Built", result.pipeline_validation.totals.candidates_built],
                ["Ranked", result.pipeline_validation.totals.candidates_ranked],
              ].map(([label, value], index, rows) => {
                const previous = index === 0 ? Number(value) : Number(rows[index - 1][1]);
                const retained = previous > 0 ? (Number(value) / previous) * 100 : 0;
                return <div className={`pipeline-stage ${Number(value) === 0 ? "zero" : ""}`} key={String(label)}>
                  <span>{label}</span>
                  <strong>{Number(value).toLocaleString()}</strong>
                  {index > 0 && <small>{retained.toFixed(1)}% of prior stage</small>}
                </div>;
              })}
            </div>
            <div className="pipeline-rejection-columns">
              <div>
                <h4>Contract-filter removals</h4>
                {Object.entries(result.pipeline_validation.filter_rejections).length
                  ? Object.entries(result.pipeline_validation.filter_rejections).slice(0, 8).map(([reason,count])=><div className="pipeline-rejection-row" key={reason}><span>{reason.replaceAll("_"," ")}</span><strong>{count}</strong></div>)
                  : <p>No contract-filter removals recorded.</p>}
              </div>
              <div>
                <h4>Spread-builder removals</h4>
                {Object.entries(result.pipeline_validation.builder_rejections).length
                  ? Object.entries(result.pipeline_validation.builder_rejections).slice(0, 8).map(([reason,count])=><div className="pipeline-rejection-row" key={reason}><span>{reason.replaceAll("_"," ")}</span><strong>{count}</strong></div>)
                  : <p>No spread-builder removals recorded.</p>}
              </div>
            </div>
          </article>

          <div className="diagnostics-grid">
            <article className="card diagnostics-card">
              <h3>Per-symbol diagnostics</h3>
              {result.diagnostics.map((item)=><div className="diagnostic-row" key={`${item.symbol}-${item.strategy_type ?? "BULL_PUT"}`}><strong>{item.symbol}</strong><span>{item.strategy_type === "BEAR_CALL" ? "Bear Call" : "Bull Put"}</span><span className={item.status === "ERROR" ? "diagnostic-error" : ""}>{item.status}</span><span>{item.evaluated_count} evaluated</span><span>{item.included_count} included · {item.message}</span></div>)}
            </article>
            <article className="card diagnostics-card">
              <h3>Constraint impact</h3>
              {result.constraint_impact.length ? result.constraint_impact.map((item)=><div className="impact-row" key={item.reason}><div><strong>{item.count}</strong><span>{item.reason}</span></div><div className="impact-bar"><span style={{width:`${Math.min(item.candidate_percent,100)}%`}}/></div></div>) : <p>No post-pipeline rejection reasons were recorded.</p>}
            </article>
          </div>
          {result.what_if_hints.length > 0 && <article className="card what-if-card"><h3>What to review</h3>{result.what_if_hints.map((hint)=><div key={hint.constraint}><strong>{hint.affected_candidates} candidate(s)</strong><span>{hint.suggestion}</span></div>)}</article>}
          <p className="pricing-disclosure">{result.diagnostics_disclosure}</p>
          <p className="pricing-disclosure">{result.pricing_disclosure}</p>
        </>
      )}

      <div className="recommendation-layout">
        <section className="candidate-list">
          {!result && !loading && !error && <article className="card empty-result"><Activity size={28}/><h2>Constrained recommendations</h2><p>Leave a field blank to avoid imposing that constraint.</p></article>}
          {result && visibleCandidates.length === 0 && <article className="card empty-result"><h2>{result.summary.outcome === "NO_PIPELINE_CANDIDATES" ? "No candidates were produced by the baseline strategy pipeline" : "No candidates met the active constraints"}</h2><p>{result.summary.outcome === "NO_PIPELINE_CANDIDATES" ? "Review the per-symbol diagnostics. This is different from candidates being evaluated and rejected by your selected constraints." : "Review constraint impact and rejected-candidate reasons before relaxing a rule."}</p></article>}

          {visibleCandidates.length > 0 && (
            <article className="card recommendations-table-card">
              <div className="table-scroll">
                <table className="recommendations-table">
                  <thead>
                    <tr>
                      <th>Rank</th><th>Symbol</th><th>Strategy</th><th>Expiration</th><th>Spread</th>
                      <th>Score</th><th>Credit</th><th>POP</th><th>ROR</th>
                      <th>Risk</th><th>Audit</th><th>Decision</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleCandidates.map((candidate, index) => (
                      <tr
                        key={`${candidate.symbol}-${candidate.expiration}-${candidate.short_strike}-${candidate.long_strike}`}
                        className={selected===candidate ? "selected-row" : ""}
                        onClick={()=>setSelected(candidate)}
                      >
                        <td>{index + 1}</td>
                        <td><strong>{candidate.symbol}</strong></td>
                        <td><span className={`strategy-chip ${(candidate.strategy_type ?? "BULL_PUT").toLowerCase()}`}>{candidate.strategy_type === "BEAR_CALL" ? "Bear Call" : "Bull Put"}</span></td>
                        <td>{candidate.expiration}<small>{candidate.dte} DTE</small></td>
                        <td>{candidate.short_strike}/{candidate.long_strike}</td>
                        <td><span className={`score-chip ${candidate.score >= 85 ? "high" : candidate.score >= 70 ? "medium" : "low"}`}>{candidate.score.toFixed(1)}</span></td>
                        <td>${candidate.selected_credit.toFixed(2)}<small>${candidate.selected_credit_per_contract.toFixed(0)} / contract</small></td>
                        <td>{(candidate.probability_of_profit*100).toFixed(1)}%</td>
                        <td>{(candidate.return_on_risk*100).toFixed(1)}%</td>
                        <td>{money.format(candidate.maximum_risk)}</td>
                        <td><span className={`audit-chip ${candidate.quote.audit_status.toLowerCase()}`}>{candidate.quote.audit_status}</span></td>
                        <td><DecisionBadge decision={candidate.decision}/></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>
          )}

          {result && result.rejected_candidates.length > 0 && (
            <details className="card rejected-card">
              <summary>Rejected candidates ({result.rejected_candidates.length})</summary>
              {result.rejected_candidates.slice(0,50).map((candidate,index)=>(
                <div className="rejected-row" key={`${candidate.symbol}-${index}`}>
                  <strong>{candidate.symbol} {candidate.strategy_type === "BEAR_CALL" ? "Bear Call" : "Bull Put"} {candidate.short_strike}/{candidate.long_strike}</strong>
                  <span>{candidate.expiration}</span>
                  <ul>{candidate.reasons.map((reason)=><li key={reason}>{reason}</li>)}</ul>
                </div>
              ))}
            </details>
          )}
        </section>

        <aside className="trade-detail">
          {selected ? (
            <article className="card trade-detail-card">
              <div className="trade-detail-header"><div><p className="eyebrow">{selected.direction ?? "BULLISH"} · {selected.market_regime || "MARKET REGIME UNKNOWN"}</p><h2>{selected.symbol} · {selected.strategy_name ?? "Bull Put Credit Spread"}</h2></div><DecisionBadge decision={selected.decision}/></div>
              <div className="trade-summary-strip">
                <div><small>Score</small><strong>{selected.score.toFixed(1)}</strong></div>
                <div><small>Credit / contract</small><strong>${selected.selected_credit_per_contract.toFixed(0)}</strong></div>
                <div><small>POP</small><strong>{(selected.probability_of_profit*100).toFixed(1)}%</strong></div>
                <div><small>Return on risk</small><strong>{(selected.return_on_risk*100).toFixed(1)}%</strong></div>
                <div><small>Managed EV</small><strong>{money.format(selected.managed_expected_value)}</strong></div>
              </div>
              <div className="detail-grid">
                <Detail label="Expiration" value={selected.expiration}/>
                <Detail label="DTE" value={String(selected.dte)}/>
                <Detail label={`Short ${(selected.option_type ?? "PUT").toLowerCase()}`} value={`${selected.short_strike} · Δ ${formatDelta(selected.short_delta)}`}/>
                <Detail label={`Long ${(selected.option_type ?? "PUT").toLowerCase()}`} value={`${selected.long_strike} · Δ ${formatDelta(selected.long_delta)}`}/>
                <Detail label="Net position Δ" value={formatDelta(selected.net_position_delta)}/>
                <Detail label="Selected credit" value={`$${selected.selected_credit.toFixed(2)}`}/>
                <Detail label="Credit / contract" value={`$${selected.selected_credit_per_contract.toFixed(2)}`}/>
                <Detail label="Scoring credit" value={`$${selected.quote.scoring_credit.toFixed(2)}`}/>
                <Detail label="Natural credit" value={`$${selected.quote.natural_credit.toFixed(2)}`}/>
                <Detail label="Midpoint credit" value={`$${selected.quote.midpoint_credit.toFixed(2)}`}/>
                <Detail label="Max risk" value={money.format(selected.maximum_risk)}/>
                <Detail label="POP" value={`${(selected.probability_of_profit*100).toFixed(1)}%`}/>
              </div>

              <section className={`detail-section quote-audit-panel ${selected.quote.audit_status === "REVIEW" ? "review" : "aligned"}`}>
                <div className="quote-audit-heading"><h3>Quote Audit</h3><span>{selected.quote.audit_status}</span></div>
                <p>{selected.quote.audit_message}</p>
                <div className="quote-differences"><span>Engine vs natural: {selected.quote.scoring_vs_natural >= 0 ? "+" : ""}${selected.quote.scoring_vs_natural.toFixed(2)}</span><span>Engine vs midpoint: {selected.quote.scoring_vs_midpoint >= 0 ? "+" : ""}${selected.quote.scoring_vs_midpoint.toFixed(2)}</span><span>Review threshold: ${selected.quote.material_difference_threshold.toFixed(2)}</span></div>
                <h3>Schwab leg quotes</h3>
                <div className="quote-grid">
                  <Detail label="Short bid / ask" value={`$${selected.quote.short_bid.toFixed(2)} / $${selected.quote.short_ask.toFixed(2)}`}/>
                  <Detail label="Long bid / ask" value={`$${selected.quote.long_bid.toFixed(2)} / $${selected.quote.long_ask.toFixed(2)}`}/>
                  <Detail label="Short OI / volume" value={`${selected.quote.short_open_interest} / ${selected.quote.short_volume}`}/>
                  <Detail label="Long OI / volume" value={`${selected.quote.long_open_interest} / ${selected.quote.long_volume}`}/>
                  <Detail label="Quote timestamp" value={selected.quote.quote_timestamp ?? "Unavailable from normalized contract"}/>
                  <Detail label="Pricing method" value={selected.selected_pricing_method}/>
                </div>
              </section>

              <section className="detail-section"><h3>Why this decision?</h3><ul>{[...selected.decision_reasons,...selected.reasons].filter((value,index,values)=>value&&values.indexOf(value)===index).map((reason)=><li key={reason}>{reason}</li>)}</ul></section>
              {selected.warnings.length>0&&<section className="detail-section warning-section"><h3>Warnings</h3><ul>{selected.warnings.map((warning)=><li key={warning}>{warning}</li>)}</ul></section>}
                            <div className="safe-action-row">
                <button
                  type="button"
                  className="primary"
                  disabled={paperSubmitting || selected.decision === "PASS"}
                  onClick={() => executePaperTrade(selected)}
                >
                  {paperSubmitting ? "Creating paper positionâ€¦" : selected.decision === "WATCH" ? "Simulate WATCH in Paper" : "Execute in Paper"}
                </button>
                <button disabled>Live order unavailable</button>
              </div>
              {selected.decision !== "TRADE" && (
                <p className="pricing-disclosure">
                  PASS recommendations are always blocked. WATCH candidates may be simulated only as explicitly labeled experiments.
                </p>
              )}
              {paperStatus && <p className="pricing-disclosure">{paperStatus}</p>}
            </article>
          ) : <article className="card empty-result"><h2>Trade review</h2><p>Select an included recommendation to inspect its quotes and rationale.</p></article>}
        </aside>
      </div>
    </div>
  );
}



