# tests/test_ganzhi.py
from datetime import date
from ganzhi import day_ganzhi, year_ganzhi, month_ganzhi, hour_ganzhi, get_nayin


def test_day_ganzhi_2026_07_15():
    """2026-07-15 = 庚寅日"""
    gan, zhi = day_ganzhi(date(2026, 7, 15))
    assert gan == "庚", f"expected 庚, got {gan}"
    assert zhi == "寅", f"expected 寅, got {zhi}"


def test_day_ganzhi_2026_01_01():
    """2026-01-01 = 乙亥日"""
    gan, zhi = day_ganzhi(date(2026, 1, 1))
    assert gan == "乙", f"expected 乙, got {gan}"
    assert zhi == "亥", f"expected 亥, got {zhi}"


def test_day_ganzhi_2026_02_04():
    """2026-02-04 立春 = 己酉日"""
    gan, zhi = day_ganzhi(date(2026, 2, 4))
    assert gan == "己", f"expected 己, got {gan}"
    assert zhi == "酉", f"expected 酉, got {zhi}"


def test_year_ganzhi_2026():
    """2026 = 丙午年"""
    gan, zhi = year_ganzhi(date(2026, 7, 15))
    assert gan == "丙", f"expected 丙, got {gan}"
    assert zhi == "午", f"expected 午, got {zhi}"


def test_year_ganzhi_before_lichun():
    """立春前属于上年 — 2026-02-03 还在乙巳年"""
    gan, zhi = year_ganzhi(date(2026, 2, 3))
    assert gan == "乙", f"expected 乙 (2025年干), got {gan}"
    assert zhi == "巳", f"expected 巳 (2025年支), got {zhi}"


def test_month_ganzhi_2026_07_15():
    """2026-07-15 小暑后 = 乙未月"""
    gan, zhi = month_ganzhi(date(2026, 7, 15))
    assert gan == "乙", f"expected 乙, got {gan}"
    assert zhi == "未", f"expected 未, got {zhi}"


def test_hour_ganzhi_morning():
    """2026-07-15 07:00 辰时 = 庚辰时（日干庚，五鼠遁：乙庚丙子起 → 子丙子, 丑丁丑, 寅戊寅, 卯己卯, 辰庚辰）"""
    gan, zhi = hour_ganzhi(7, "庚")
    assert gan == "庚", f"expected 庚, got {gan}"
    assert zhi == "辰", f"expected 辰, got {zhi}"


def test_nayin_bingwu():
    """丙午 = 天河水"""
    assert get_nayin("丙", "午") == "天河水"


def test_nayin_yiwei():
    """乙未 = 沙中金"""
    assert get_nayin("乙", "未") == "沙中金"


def test_nayin_gengyin():
    """庚寅 = 松柏木"""
    assert get_nayin("庚", "寅") == "松柏木"
