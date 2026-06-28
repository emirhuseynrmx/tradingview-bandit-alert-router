from tradingview_bandit_router.models import (
    RewardEvent,
    RouteArm,
    RouterConfig,
    RouteStatus,
    TradingViewAlert,
)
from tradingview_bandit_router.policy import ThompsonRouter


def make_router() -> ThompsonRouter:
    return ThompsonRouter(
        RouterConfig(
            allowed_symbols={"BTCUSDT"},
            min_confidence=0.5,
            max_total_risk_usd=1_000,
            arms=[
                RouteArm(name="paper", channel="webhook", max_risk_usd=1_000),
                RouteArm(name="human", channel="telegram", max_risk_usd=300),
            ],
        )
    )


def make_alert(**overrides) -> TradingViewAlert:
    payload = {
        "alert_id": "alert-0001",
        "strategy": "breakout_v1",
        "symbol": "btcusdt",
        "timeframe": "15m",
        "side": "long",
        "confidence": 0.71,
        "price": 64_000,
        "risk_usd": 250,
        "features": {"atr_pct": 0.02, "volume_z": 1.8},
    }
    payload.update(overrides)
    return TradingViewAlert.model_validate(payload)


def test_routes_allowed_alert_once() -> None:
    router = make_router()
    decision = router.decide(make_alert())
    duplicate = router.decide(make_alert())

    assert decision.status == RouteStatus.ROUTED
    assert decision.selected_arm in {"paper", "human"}
    assert duplicate.status == RouteStatus.DUPLICATE


def test_blocks_symbol_not_allowed() -> None:
    decision = make_router().decide(make_alert(symbol="DOGEUSDT"))

    assert decision.status == RouteStatus.BLOCKED
    assert "not allowed" in decision.reason


def test_blocks_low_confidence() -> None:
    decision = make_router().decide(make_alert(confidence=0.2))

    assert decision.status == RouteStatus.BLOCKED
    assert "confidence" in decision.reason


def test_reward_updates_selected_arm() -> None:
    router = make_router()
    before = router.arms[0].posterior_mean
    arm = router.update_reward(RewardEvent(alert_id="alert-0001", selected_arm="paper", reward=1.0))

    assert arm.posterior_mean > before
