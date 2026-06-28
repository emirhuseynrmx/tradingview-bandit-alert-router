from __future__ import annotations

from pathlib import Path

import typer

from tradingview_bandit_router.app import default_config
from tradingview_bandit_router.models import RewardEvent, TradingViewAlert
from tradingview_bandit_router.policy import ThompsonRouter

app = typer.Typer(help="Run a local Thompson Sampling alert-routing demo.")


@app.command()
def replay(sample: Path = Path("examples/sample_alerts.jsonl")) -> None:
    router = ThompsonRouter(default_config())
    for line in sample.read_text(encoding="utf-8").splitlines():
        alert = TradingViewAlert.model_validate_json(line)
        decision = router.decide(alert)
        typer.echo(
            f"{decision.alert_id}: {decision.status.value} -> "
            f"{decision.selected_arm or '-'} ({decision.reason})"
        )
        if decision.selected_arm:
            router.update_reward(
                RewardEvent(
                    alert_id=decision.alert_id,
                    selected_arm=decision.selected_arm,
                    reward=1.0 if alert.confidence >= 0.7 else 0.0,
                )
            )
    typer.echo("\nPosterior means:")
    for arm in router.arms:
        typer.echo(f"- {arm.name}: {arm.posterior_mean:.3f}")

