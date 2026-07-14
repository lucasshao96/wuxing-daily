"""端到端集成测试 — 只测数据流，不测邮件发送。"""

import json, os
from datetime import date
from email_report import build_report_data


def test_build_report_smoke():
    """冒烟测试: 用假用户跑一次完整的报表构建"""
    users = [
        {"name": "佳辉", "day_master": "丁", "zodiac": "鼠"},
        {"name": "婷婷", "day_master": "乙", "zodiac": "虎"},
    ]
    report = build_report_data(date(2026, 7, 15), users)

    assert report["day_ganzhi"] == "庚寅", f"expected 庚寅, got {report['day_ganzhi']}"
    assert report["year_ganzhi"] == "丙午"
    assert report["month_ganzhi"] == "乙未"
    assert len(report["users"]) == 2

    for wx in ["木","火","土","金","水"]:
        assert wx in report["wuxing"], f"missing {wx}"
        assert "score" in report["wuxing"][wx]
        assert "level" in report["wuxing"][wx]

    assert report["chong_zodiac"] == "猴"
    assert len(report["ji_shi"]) == 6
    assert len(report["yi"]) > 0

    for ub in report["users"]:
        assert "advice" in ub
        assert "colors" in ub
        assert "fit" in ub["advice"]


def test_build_report_another_date():
    """再测一天确保不是碰巧"""
    users = [{"name": "佳辉", "day_master": "丁", "zodiac": "鼠"}]
    report = build_report_data(date(2026, 1, 1), users)

    assert report["day_ganzhi"] == "乙亥"
    assert "丑" in report["month_ganzhi"]
    assert len(report["users"]) == 1


def test_report_serializable():
    """确保 report dict 可以序列化为 JSON（给未来 API 扩展预留）"""
    users = [{"name": "佳辉", "day_master": "丁", "zodiac": "鼠"}]
    report = build_report_data(date(2026, 7, 15), users)
    json.dumps(report, ensure_ascii=False, default=str)


def test_html_renders():
    """HTML 渲染不走样"""
    from email_report import render_html
    users = [{"name": "佳辉", "day_master": "丁", "zodiac": "鼠"}]
    report = build_report_data(date(2026, 7, 15), users)
    html = render_html(report)
    assert "<!DOCTYPE html>" in html
    assert "庚寅" in html
    assert "佳辉" in html
    assert "文化参考" in html


def test_plain_renders():
    """纯文本渲染不走样"""
    from email_report import render_plain
    users = [{"name": "佳辉", "day_master": "丁", "zodiac": "鼠"}]
    report = build_report_data(date(2026, 7, 15), users)
    text = render_plain(report)
    assert "庚寅" in text
    assert "佳辉" in text
    assert "文化参考" in text
