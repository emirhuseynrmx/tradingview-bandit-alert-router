from __future__ import annotations

from litestar import Litestar, get, post
from litestar.exceptions import HTTPException

from tradingview_bandit_router.models import (
    RewardEvent,
    RouteArm,
    RouteDecision,
    RouterConfig,
    TradingViewAlert,
)
from tradingview_bandit_router.policy import ThompsonRouter


def default_config() -> RouterConfig:
    return RouterConfig(
        allowed_symbols={"BTCUSDT", "ETHUSDT", "SPY", "QQQ"},
        min_confidence=0.58,
        max_total_risk_usd=2_000,
        arms=[
            RouteArm(name="paper_trade", channel="webhook", max_risk_usd=2_000, tags=("audit",)),
            RouteArm(name="telegram_ops", channel="telegram", max_risk_usd=800, tags=("human",)),
            RouteArm(
                name="discord_research",
                channel="discord",
                max_risk_usd=500,
                tags=("research",),
            ),
        ],
    )


router = ThompsonRouter(default_config())


@get("/health", sync_to_thread=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


@post("/v1/alerts", sync_to_thread=False)
def route_alert(data: TradingViewAlert) -> RouteDecision:
    return router.decide(data)


@post("/v1/rewards", sync_to_thread=False)
def reward_route(data: RewardEvent) -> RouteArm:
    try:
        return router.update_reward(data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@get("/v1/arms", sync_to_thread=False)
def route_arms() -> list[RouteArm]:
    return router.arms


app = Litestar(
    route_handlers=[health, route_alert, reward_route, route_arms],
    debug=False,
)
