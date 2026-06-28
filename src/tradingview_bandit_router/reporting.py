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
    return f"""#set page(margin: 15mm)
#set text(font: "Arial", size: 10pt)
#set heading(numbering: none)

#let ink = rgb("#111827")
#let muted = rgb("#64748b")
#let panel = rgb("#f3f6fb")
#let line = rgb("#d7dee8")
#let warn = rgb("#b45309")

#let card(label, value, note: none) = block[
  #rect(fill: panel, radius: 6pt, inset: 9pt, width: 100%)[
    #text(size: 8pt, fill: muted, weight: "bold")[#upper(label)]
    #linebreak()
    #text(size: 19pt, fill: ink, weight: "bold")[#value]
    #if note != none [#linebreak() #text(size: 8pt, fill: muted)[#note]]
  ]
]

#let check(label, value) = block[
  #text(weight: "bold")[#label]
  #linebreak()
  #text(fill: muted)[#value]
]

#text(size: 22pt, weight: "bold", fill: ink)[TradingView Bandit Alert Router]

#text(fill: muted)[
  Sample routing report for a Thompson Sampling alert workflow. The router validates,
  blocks, routes, and records feedback without touching broker execution.
]

#grid(columns: (1fr, 1fr, 1fr), gutter: 8pt)[
  #card("Routed", "{routed}", note: "accepted alerts")
][
  #card("Blocked", "{blocked}", note: "guarded before policy")
][
  #card("Policy", "Thompson", note: "route selection")
]

#v(10pt)
#grid(columns: (1.75fr, .95fr), gutter: 14pt)[
  #text(size: 13pt, weight: "bold")[Decision Log]
  #v(4pt)
  #table(
    columns: (.9fr, .6fr, 1.25fr, 2.25fr),
    stroke: line,
    inset: 5pt,
    [*Alert*], [*Status*], [*Route*], [*Reason*],
{rows}
  )
][
  #text(size: 13pt, weight: "bold")[Evidence Contract]
  #v(4pt)
  #block(stroke: line, radius: 6pt, inset: 8pt)[
    #check("Validation", "Pydantic rejects malformed webhook payloads.")
    #v(5pt)
    #check("Idempotency", "Duplicate alert IDs do not receive new route decisions.")
    #v(5pt)
    #check("Risk guard", "Low-confidence or oversized alerts are blocked first.")
    #v(5pt)
    #check("Boundary", "Routing feedback is not a profit forecast.")
  ]
]

#v(10pt)
#block(fill: rgb("#fffbeb"), radius: 6pt, inset: 8pt)[
  #text(weight: "bold", fill: warn)[Interpretation:] This service is a decision
  router. Live capital deployment, broker credentials, and exchange adapters belong
  in a separate, stricter execution boundary.
]
"""

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


if __name__ == "__main__":
    main()
