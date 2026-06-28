from tradingview_bandit_router.reporting import build_report_typ


def test_report_contains_policy_and_decisions() -> None:
    report = build_report_typ()

    assert "TradingView Bandit Alert Router" in report
    assert "Thompson" in report
    assert "Decision Log" in report
