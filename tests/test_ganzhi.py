# tests/test_ganzhi.py
import pytest
from datetime import date
from ganzhi import day_ganzhi, year_ganzhi, month_ganzhi, hour_ganzhi, get_nayin
from ganzhi import days_from_1900, get_jieqi


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


def test_hour_ganzhi_midnight():
    """hour=0 → 子时 (23:00-01:00)"""
    gan, zhi = hour_ganzhi(0, "甲")
    assert zhi == "子", f"expected 子, got {zhi}"


def test_hour_ganzhi_noon():
    """hour=12 → 午时 (11:00-13:00)"""
    gan, zhi = hour_ganzhi(12, "甲")
    assert zhi == "午", f"expected 午, got {zhi}"


def test_hour_ganzhi_last():
    """hour=23 → 子时 (23:00-01:00)"""
    gan, zhi = hour_ganzhi(23, "甲")
    assert zhi == "子", f"expected 子, got {zhi}"


def test_hour_ganzhi_negative_raises():
    """hour < 0 raises ValueError"""
    with pytest.raises(ValueError, match="0-23"):
        hour_ganzhi(-1, "甲")


def test_hour_ganzhi_too_high_raises():
    """hour > 23 raises ValueError"""
    with pytest.raises(ValueError, match="0-23"):
        hour_ganzhi(24, "甲")


def test_days_from_1900_anchor():
    """1900-01-01 is day 0"""
    assert days_from_1900(1900, 1, 1) == 0


def test_days_from_1900_one_day():
    """1900-01-02 is day 1"""
    assert days_from_1900(1900, 1, 2) == 1


def test_days_from_1900_known():
    """2026-07-15: verify against known day_ganzhi anchor (甲戌 = gan_idx 0, zhi_idx 10).
    day_ganzhi(2026-07-15) = 庚寅 → gan_idx 6, zhi_idx 2.
    diff = days_from_1900, (0 + diff) % 10 == 6, (10 + diff) % 12 == 2
    diff ≡ 6 (mod 10), diff ≡ 4 (mod 12) → verify it works"""
    diff = days_from_1900(2026, 7, 15)
    # 庚 = TIAN_GAN[6], 寅 = DI_ZHI[2]
    assert diff % 10 == 6, f"expected diff % 10 == 6, got {diff % 10}"
    assert diff % 12 == 4, f"expected diff % 12 == 4, got {diff % 12} (寅 is index 2, so 10+4=14 ≡ 2 mod 12)"


def test_get_jieqi_lichun():
    """2月4日 = 立春"""
    assert get_jieqi(date(2026, 2, 4)) == "立春"


def test_get_jieqi_xiaoshu():
    """7月7日 = 小暑"""
    assert get_jieqi(date(2026, 7, 7)) == "小暑"


def test_get_jieqi_not_term():
    """7月15日不是节气"""
    assert get_jieqi(date(2026, 7, 15)) is None


def test_nayin_bingwu():
    """丙午 = 天河水"""
    assert get_nayin("丙", "午") == "天河水"


def test_nayin_yiwei():
    """乙未 = 沙中金"""
    assert get_nayin("乙", "未") == "沙中金"


def test_nayin_gengyin():
    """庚寅 = 松柏木"""
    assert get_nayin("庚", "寅") == "松柏木"
