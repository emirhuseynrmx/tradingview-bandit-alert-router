from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tradingview_bandit_router.app import default_config
from tradingview_bandit_router.models import TradingViewAlert
from tradingview_bandit_router.policy import ThompsonRouter


def build_report_typ() -> str:
    router = ThompsonRouter(default_config())
    decisions = [
        router.decide(
            TradingViewAlert(
                alert_id=f"report-{idx:04d}",
                strategy="breakout_v1",
                symbol="BTCUSDT",
                timeframe="15m",
                side="long",
                confidence=confidence,
                price=64_000 + idx,
                risk_usd=250 + idx * 25,
                features={"atr_pct": 0.02, "volume_z": 1.5},
            )
        )
        for idx, confidence in enumerate([0.72, 0.66, 0.49, 0.81], start=1)
    ]
    routed = sum(decision.status.value == "routed" for decision in decisions)
    blocked = sum(decision.status.value == "blocked" for decision in decisions)
    rows = "\n".join(
        f'  [{decision.alert_id}], [{decision.status.value}], '
        f'[{decision.selected_arm or "-"}], [{decision.reason}],'
        for decision in decisions
    )
    routed_card = _metric_card("Routed", str(routed))
    blocked_card = _metric_card("Blocked", str(blocked))
    policy_card = _metric_card("Policy", "Thompson")
    return f"""#set page(margin: 16mm)
#set text(font: "Arial", size: 10pt)

#text(size: 18pt, weight: "bold")[TradingView Bandit Alert Router]

Sample routing report for a Thompson Sampling alert workflow.

#grid(columns: (1fr, 1fr, 1fr), gutter: 8pt)[
{routed_card}
][
{blocked_card}
][
{policy_card}
]

#v(10pt)
#text(size: 12pt, weight: "bold")[Decision Log]

#table(
  columns: (1fr, .7fr, 1fr, 2fr),
  [Alert], [Status], [Route], [Reason],
{rows}
)
"""


def _metric_card(label: str, value: str) -> str:
    return (
        f'  #block(fill: rgb("#f3f6fb"), radius: 4pt, inset: 8pt)'
        f'[{label}\\ #text(size: 18pt, weight: "bold")[{value}]]'
    )


def write_report(output_dir: Path = Path("docs/samples")) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    typ_path = output_dir / "bandit_alert_router_report.typ"
    typ_path.write_text(build_report_typ(), encoding="utf-8")
    if shutil.which("typst"):
        subprocess.run(
            ["typst", "compile", str(typ_path), str(typ_path.with_suffix(".pdf"))],
            check=True,
        )
    return typ_path


def main() -> None:
    print(write_report())
