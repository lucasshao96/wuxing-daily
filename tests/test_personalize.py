"""Tests for personalize.py — 个性化分析引擎."""

from datetime import date
from personalize import shi_shen, generate_colors, check_annual_alert


def test_shi_shen_ding_huo_vs_geng():
    """丁火(阴) x 庚金(阳): 火克金, 异性 -> 正财"""
    assert shi_shen("丁", "庚") == "正财", \
        f"expected 正财, got {shi_shen('丁', '庚')}"


def test_shi_shen_ding_huo_vs_jia():
    """丁火(阴) x 甲木(阳): 木生火, 异性 -> 正印"""
    assert shi_shen("丁", "甲") == "正印"


def test_shi_shen_yi_mu_vs_geng():
    """乙木(阴) x 庚金(阳): 金克木, 异性 -> 正官"""
    assert shi_shen("乙", "庚") == "正官"


def test_shi_shen_ding_huo_vs_bing():
    """丁火(阴) x 丙火(阳): 同五行, 异性 -> 劫财"""
    assert shi_shen("丁", "丙") == "劫财"


def test_colors_weak_metal():
    """金弱时应推荐白色/金色 (金 score=0.0, second-weakest)"""
    scores = {"木": {"score": 5.5}, "火": {"score": 7.5},
              "土": {"score": 10.5}, "金": {"score": 0.0}, "水": {"score": -1.0}}
    colors = generate_colors(scores)
    # 金是第二弱元素，应在推荐列表中
    assert "白色" in colors["recommend"][1] or "金色" in colors["recommend"][1], \
        f"金弱应推荐白色/金色, got {colors['recommend']}"


def test_colors_avoid_strongest():
    """最强元素应出现在避免列表中"""
    scores = {"木": {"score": 5.5}, "火": {"score": 7.5},
              "土": {"score": 10.5}, "金": {"score": 0.0}, "水": {"score": -1.0}}
    colors = generate_colors(scores)
    # 土最旺(10.5), 应避免黄色
    assert any("黄色" in a for a in colors["avoid"]), \
        f"土最旺应避免黄色, got {colors['avoid']}"


def test_annual_alert_august():
    """8/7-10/7 申酉月: 金到位, 全年最佳窗口"""
    alert = check_annual_alert(date(2026, 8, 15))
    assert alert is not None, "8/15 should trigger annual alert"
    assert "申酉月" in alert or "金到位" in alert, f"unexpected alert: {alert}"


def test_annual_alert_november():
    """11/7-12/6 亥月: 子午冲最重"""
    alert = check_annual_alert(date(2026, 11, 15))
    assert alert is not None, "11/15 should trigger annual alert"
    assert "子午冲" in alert, f"unexpected alert: {alert}"


def test_annual_alert_none():
    """非关键日期不应触发警报"""
    alert = check_annual_alert(date(2026, 5, 1))
    assert alert is None, f"5/1 should not trigger alert, got {alert}"
