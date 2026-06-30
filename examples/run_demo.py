"""
End-to-end demo: route all sample alerts through the Thompson Sampling router.

Usage:
    python examples/run_demo.py
    python examples/run_demo.py --sample examples/sample_alerts.jsonl
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tradingview_bandit_router.app import default_config
from tradingview_bandit_router.models import RewardEvent, TradingViewAlert
from tradingview_bandit_router.policy import ThompsonRouter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample", type=Path, default=Path("examples/sample_alerts.jsonl")
    )
    args = parser.parse_args()

    router = ThompsonRouter(default_config())
    decisions = []

    print()
    print("TradingView Bandit Alert Router — Routing Demo")
    print("=" * 60)
    print(f"  {'Alert ID':<14} {'Status':<10} {'Arm':<22} {'p(mean)':>8}  Reason")
    print("  " + "-" * 74)

    for line in args.sample.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        alert = TradingViewAlert.model_validate_json(line)
        decision = router.decide(alert)
        decisions.append(decision)

        status_label = decision.status.value.upper()
        arm_label = decision.selected_arm or "-"
        posterior = f"{decision.posterior_mean:.4f}" if decision.posterior_mean else "  -   "
        print(
            f"  {decision.alert_id:<14} {status_label:<10} {arm_label:<22} "
            f"{posterior:>8}  {decision.reason}"
        )

        if decision.selected_arm:
            # Reward based on confidence: high confidence = likely good signal
            reward = 1.0 if alert.confidence >= 0.70 else 0.3
            router.update_reward(
                RewardEvent(
                    alert_id=decision.alert_id,
                    selected_arm=decision.selected_arm,
                    reward=reward,
                    pnl_r=None,
                )
            )

    evidence = router.evidence()
    status_counts = Counter(d.status.value for d in decisions)

    print()
    print("Routing Summary")
    print("-" * 50)
    print(f"  Total alerts : {len(decisions)}")
    print(f"  Routed       : {status_counts.get('routed', 0)}")
    print(f"  Blocked      : {status_counts.get('blocked', 0)}")
    print(f"  Duplicates   : {status_counts.get('duplicate', 0)}")
    print(f"  Rewards given: {evidence.rewards}")

    print()
    print("Arm Posterior State (after replay)")
    print("-" * 50)
    print(f"  {'Arm':<20} {'a':>6}  {'b':>6}  {'Posterior Mean':>14}")
    print("  " + "-" * 52)
    for arm in sorted(router.arms, key=lambda a: -a.posterior_mean):
        print(
            f"  {arm.name:<20} {arm.alpha:>6.0f}  {arm.beta:>6.0f}  "
            f"{arm.posterior_mean:>14.4f}"
        )

    # Interpretation
    best = max(router.arms, key=lambda a: a.posterior_mean)
    print()
    print("Interpretation")
    print("-" * 50)
    print(
        f"  After {len(decisions)} alerts, the Thompson Sampling policy "
        f"has converged towards '{best.name}'\n"
        f"  (posterior mean = {best.posterior_mean:.4f}) as the best-performing route arm."
    )
    print(
        "  Run more alerts to tighten the posterior. Use pnl_r feedback\n"
        "  (actual trade P&L) for a higher-quality reward signal."
    )

    print()
    print("Evidence Contract")
    print("-" * 50)
    for check in evidence.checks:
        icon = "OK" if check.status == "pass" else "!!" if check.status == "review" else "--"
        print(f"  [{icon}] {check.check}: {check.evidence}")
    print()


if __name__ == "__main__":
    main()
