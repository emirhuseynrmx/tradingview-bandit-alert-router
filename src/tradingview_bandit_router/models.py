from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AlertSide(StrEnum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class RouteStatus(StrEnum):
    ROUTED = "routed"
    BLOCKED = "blocked"
    DUPLICATE = "duplicate"


class TradingViewAlert(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    alert_id: str = Field(min_length=8, max_length=96)
    strategy: str = Field(min_length=2, max_length=64)
    symbol: str = Field(min_length=1, max_length=32)
    timeframe: str = Field(min_length=1, max_length=16)
    side: AlertSide
    confidence: float = Field(ge=0, le=1)
    price: float = Field(gt=0)
    risk_usd: float = Field(gt=0, le=100_000)
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    features: dict[str, float] = Field(default_factory=dict)

    @field_validator("symbol", "strategy")
    @classmethod
    def uppercase_symbols(cls, value: str) -> str:
        return value.upper()

    @field_validator("features")
    @classmethod
    def finite_feature_values(cls, value: dict[str, float]) -> dict[str, float]:
        for key, item in value.items():
            if item != item or item in (float("inf"), float("-inf")):
                raise ValueError(f"feature {key!r} must be finite")
        return value


class RouteArm(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=64)
    channel: str = Field(min_length=2, max_length=32)
    max_risk_usd: float = Field(gt=0)
    enabled: bool = True
    alpha: float = Field(default=1.0, gt=0)
    beta: float = Field(default=1.0, gt=0)
    tags: tuple[str, ...] = ()

    @property
    def posterior_mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)


class RouterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_symbols: set[str] = Field(default_factory=set)
    min_confidence: float = Field(default=0.55, ge=0, le=1)
    max_total_risk_usd: float = Field(default=2_500, gt=0)
    exploration_seed: int = Field(default=7, ge=0)
    arms: list[RouteArm] = Field(min_length=1)

    @field_validator("allowed_symbols")
    @classmethod
    def normalize_allowed_symbols(cls, value: set[str]) -> set[str]:
        return {item.upper() for item in value}

    @model_validator(mode="after")
    def ensure_enabled_arm(self) -> RouterConfig:
        if not any(arm.enabled for arm in self.arms):
            raise ValueError("at least one route arm must be enabled")
        if len({arm.name for arm in self.arms}) != len(self.arms):
            raise ValueError("route arm names must be unique")
        return self


class RouteDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_id: str
    status: RouteStatus
    selected_arm: str | None = None
    channel: str | None = None
    posterior_mean: float | None = None
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RewardEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_id: str = Field(min_length=8, max_length=96)
    selected_arm: str = Field(min_length=2, max_length=64)
    reward: float = Field(ge=0, le=1)
    pnl_r: float | None = Field(default=None, ge=-50, le=50)
    notes: str | None = Field(default=None, max_length=240)


class RouterSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    arms: list[RouteArm]
    routed_alert_ids: set[str] = Field(default_factory=set)
    audit_log: list[dict[str, Any]] = Field(default_factory=list)

