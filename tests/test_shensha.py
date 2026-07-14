# tests/test_shensha.py
from shensha import get_chong_zodiac, get_ji_shi, get_tianyi_gui_ren


def test_chong_yin_day():
    """寅日冲申=猴，煞北(西南)"""
    zodiac, direction = get_chong_zodiac("寅")
    assert zodiac == "猴", f"expected 猴, got {zodiac}"
    assert "北" in direction or "西南" in direction, f"unexpected direction: {direction}"


def test_chong_zi_day():
    """子日冲午=马"""
    zodiac, direction = get_chong_zodiac("子")
    assert zodiac == "马", f"expected 马, got {zodiac}"


def test_ji_shi_yin_shen_day():
    """寅申日 → 子时起青龙"""
    ji_shi = get_ji_shi("寅")
    assert len(ji_shi) > 0, "should have 吉时"
    # 青龙(子时, 0) → 明堂(丑时, 1) → 金匮(辰时, 4) → ...
    # 黄道神: 青龙(0), 明堂(1), 金匮(4), 天德(5), 玉堂(7), 司命(10)
    hour_zhi_names = [h[0] for h in ji_shi]
    assert "丑" in hour_zhi_names, f"丑时 should be 明堂(吉), got {hour_zhi_names}"
    # 午时=白虎(黑道凶时), 应排除
    assert "午" not in hour_zhi_names, f"午时 is 白虎(凶), should not be in {hour_zhi_names}"


def test_ji_shi_returns_six():
    """每天应该有6个黄道吉时"""
    ji_shi = get_ji_shi("寅")
    assert len(ji_shi) == 6, f"expected 6 吉时, got {len(ji_shi)}"


def test_tianyi_geng_day():
    """庚日贵人 = 丑未"""
    gui_ren = get_tianyi_gui_ren("庚")
    assert "丑" in gui_ren, f"丑 should be 贵人 for 庚日, got {gui_ren}"
    assert "未" in gui_ren, f"未 should be 贵人 for 庚日, got {gui_ren}"


def test_tianyi_ding_day():
    """丁日贵人 = 亥酉"""
    gui_ren = get_tianyi_gui_ren("丁")
    assert "亥" in gui_ren and "酉" in gui_ren, f"expected 亥酉, got {gui_ren}"
