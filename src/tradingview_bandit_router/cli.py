from __future__ import annotations

from collections import Counter
from pathlib import Path

import typer

from tradingview_bandit_router.app import default_config
from tradingview_bandit_router.models import RewardEvent, TradingViewAlert
from tradingview_bandit_router.policy import ThompsonRouter

app = typer.Typer(help="Run a local Thompson Sampling alert-routing demo.")


@app.command()
def replay(sample: Path = Path("examples/sample_alerts.jsonl")) -> None:
    """Route all alerts in JSONL file and display routing decisions and posterior convergence."""
    router = ThompsonRouter(default_config())
    decisions = []

    typer.echo("")
    typer.echo("TradingView Bandit Alert Router — Routing Decisions")
    typer.echo("=" * 55)
    typer.echo(f"  {'Alert ID':<14} {'Status':<10} {'Arm':<16} Reason")
    typer.echo("  " + "-" * 68)

    for line in sample.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        alert = TradingViewAlert.model_validate_json(line)
        decision = router.decide(alert)
        decisions.append(decision)

        status_label = decision.status.value.upper()
        arm_label = decision.selected_arm or "-"
        typer.echo(
            f"  {decision.alert_id:<14} {status_label:<10} {arm_label:<16} {decision.reason}"
        )

        if decision.selected_arm:
            router.update_reward(
                RewardEvent(
                    alert_id=decision.alert_id,
                    selected_arm=decision.selected_arm,
                    reward=1.0 if alert.confidence >= 0.70 else 0.4,
                )
            )

    evidence = router.evidence()
    status_counts = Counter(d.status.value for d in decisions)

    typer.echo("")
    typer.echo("Routing Summary")
    typer.echo("-" * 45)
    typer.echo(f"  Total alerts : {len(decisions)}")
    typer.echo(f"  Routed       : {status_counts.get('routed', 0)}")
    typer.echo(f"  Blocked      : {status_counts.get('blocked', 0)}")
    typer.echo(f"  Duplicates   : {status_counts.get('duplicate', 0)}")

    typer.echo("")
    typer.echo("Arm Posterior State (after replay)")
    typer.echo("-" * 45)
    typer.echo(f"  {'Arm':<20} {'a':>6}  {'b':>6}  {'Posterior Mean':>14}")
    typer.echo("  " + "-" * 48)
    for arm in sorted(router.arms, key=lambda a: -a.posterior_mean):
        typer.echo(
            f"  {arm.name:<20} {arm.alpha:>6.0f}  {arm.beta:>6.0f}  {arm.posterior_mean:>14.4f}"
        )

    typer.echo("")
    typer.echo("Evidence Contract")
    typer.echo("-" * 45)
    for check in evidence.checks:
        icon = "✓" if check.status == "pass" else "⚠" if check.status == "review" else "✗"
        typer.echo(f"  [{icon}] {check.check}: {check.evidence}")
    typer.echo("")
