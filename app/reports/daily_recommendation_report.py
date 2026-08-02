from __future__ import annotations

from pathlib import Path

from app.daily.models import DailyRecommendationResult


class DailyRecommendationReport:
    """Format and persist a concise daily decision report."""

    def format(self, result: DailyRecommendationResult, detail_limit: int = 3) -> str:
        counts = {"TRADE": 0, "WATCH": 0, "PASS": 0, "ERROR": 0}
        lines = [
            "# TradingEngine Daily Recommendation Report",
            "",
            f"Generated: {result.generated_at.isoformat(timespec='seconds')}",
            f"Strategy: {result.strategy}",
            f"Watchlist: {result.watchlist}",
            "",
            "## Summary",
            "",
            "| Rank | Symbol | Decision | Score | Spread | Credit | Managed EV |",
            "|---:|:---|:---|---:|:---|---:|---:|",
        ]
        ranked = []
        for item in result.symbols:
            if item.error:
                counts["ERROR"] += 1
                ranked.append((99, -1.0, item))
            elif item.best is None:
                counts["PASS"] += 1
                ranked.append((2, 0.0, item))
            else:
                decision = item.best.decision.upper()
                counts[decision] = counts.get(decision, 0) + 1
                order = {"TRADE": 0, "WATCH": 1, "PASS": 2}.get(decision, 3)
                ranked.append((order, -item.best.score, item))
        ranked.sort(key=lambda row: (row[0], row[1], row[2].symbol))

        for index, (_, __, item) in enumerate(ranked, start=1):
            best = item.best
            if item.error:
                lines.append(f"| {index} | {item.symbol} | ERROR | - | - | - | - |")
            elif best is None:
                lines.append(f"| {index} | {item.symbol} | PASS | - | No candidate | - | - |")
            else:
                spread = best.spread
                lines.append(
                    f"| {index} | {item.symbol} | {best.decision} | {best.score:.1f} | "
                    f"{spread.short_put.strike:g}/{spread.long_put.strike:g} | "
                    f"${spread.credit:.2f} | ${best.managed_expected_value:.2f} |"
                )

        lines.extend([
            "",
            f"TRADE: {counts['TRADE']}  |  WATCH: {counts['WATCH']}  |  "
            f"PASS: {counts['PASS']}  |  ERROR: {counts['ERROR']}",
            "",
            "## Details",
        ])
        detailed = 0
        for _, __, item in ranked:
            if detailed >= detail_limit:
                break
            best = item.best
            if item.error:
                lines.extend(["", f"### {item.symbol} — ERROR", "", item.error])
                detailed += 1
            elif best:
                spread = best.spread
                lines.extend([
                    "",
                    f"### {item.symbol} — {best.decision}",
                    "",
                    f"- Score: {best.score:.1f}/100",
                    f"- Spread: Sell {spread.short_put.strike:g} / Buy {spread.long_put.strike:g}",
                    f"- Expiration: {spread.short_put.expiration_date}",
                    f"- Credit: ${spread.credit:.2f}",
                    f"- Max risk: ${spread.max_loss:.2f}",
                    f"- Probability of profit: {best.probability_of_profit:.1%}",
                    f"- Managed expected value: ${best.managed_expected_value:.2f}",
                ])
                if best.decision_reasons:
                    lines.append("- Decision rationale: " + "; ".join(best.decision_reasons))
                if best.warnings:
                    lines.append("- Warnings: " + "; ".join(best.warnings))
                detailed += 1
        lines.extend(["", "_Research and paper-trading output only; not investment advice._", ""])
        return "\n".join(lines)

    def write(self, result: DailyRecommendationResult, directory: str | Path = "reports/daily") -> Path:
        folder = Path(directory)
        folder.mkdir(parents=True, exist_ok=True)
        timestamp = result.generated_at.strftime("%Y-%m-%d_%H%M%S")
        path = folder / f"daily_recommendations_{timestamp}.md"
        path.write_text(self.format(result), encoding="utf-8")
        return path
