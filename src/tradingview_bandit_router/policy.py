from __future__ import annotations

import random
from dataclasses import dataclass, field

from tradingview_bandit_router.models import (
    RewardEvent,
    RouteArm,
    RouteDecision,
    RouterConfig,
    RouteStatus,
    TradingViewAlert,
)


@dataclass
class ThompsonRouter:
    config: RouterConfig
    routed_alert_ids: set[str] = field(default_factory=set)
    audit_log: list[dict[str, str | float | None]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.config.exploration_seed)

    @property
    def arms(self) -> list[RouteArm]:
        return self.config.arms

    def decide(self, alert: TradingViewAlert) -> RouteDecision:
        block_reason = self._block_reason(alert)
        if block_reason is not None:
            return self._record(alert, RouteStatus.BLOCKED, None, block_reason)

        if alert.alert_id in self.routed_alert_ids:
            return self._record(alert, RouteStatus.DUPLICATE, None, "alert_id was already routed")

        candidates = [
            arm
            for arm in self.config.arms
            if arm.enabled and alert.risk_usd <= arm.max_risk_usd
        ]
        if not candidates:
            return self._record(alert, RouteStatus.BLOCKED, None, "no route arm accepts this risk")

        selected = max(candidates, key=lambda arm: self._rng.betavariate(arm.alpha, arm.beta))
        self.routed_alert_ids.add(alert.alert_id)
        return self._record(alert, RouteStatus.ROUTED, selected, "selected by Thompson Sampling")

    def update_reward(self, reward: RewardEvent) -> RouteArm:
        arm = self._find_arm(reward.selected_arm)
        if reward.reward >= 0.5:
            arm.alpha += 1
        else:
            arm.beta += 1
        self.audit_log.append(
            {
                "type": "reward",
                "alert_id": reward.alert_id,
                "selected_arm": reward.selected_arm,
                "reward": reward.reward,
                "posterior_mean": round(arm.posterior_mean, 6),
            }
        )
        return arm

    def _block_reason(self, alert: TradingViewAlert) -> str | None:
        if self.config.allowed_symbols and alert.symbol not in self.config.allowed_symbols:
            return f"symbol {alert.symbol} is not allowed"
        if alert.confidence < self.config.min_confidence:
            return "confidence is below the routing threshold"
        if alert.risk_usd > self.config.max_total_risk_usd:
            return "risk exceeds router max_total_risk_usd"
        return None

    def _find_arm(self, name: str) -> RouteArm:
        for arm in self.config.arms:
            if arm.name == name:
                return arm
        raise ValueError(f"unknown route arm: {name}")

    def _record(
        self,
        alert: TradingViewAlert,
        status: RouteStatus,
        arm: RouteArm | None,
        reason: str,
    ) -> RouteDecision:
        decision = RouteDecision(
            alert_id=alert.alert_id,
            status=status,
            selected_arm=arm.name if arm else None,
            channel=arm.channel if arm else None,
            posterior_mean=round(arm.posterior_mean, 6) if arm else None,
            reason=reason,
        )
        self.audit_log.append(
            {
                "type": "decision",
                "alert_id": alert.alert_id,
                "status": decision.status.value,
                "selected_arm": decision.selected_arm,
                "reason": decision.reason,
            }
        )
        return decision

