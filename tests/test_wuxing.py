# tests/test_wuxing.py
from datetime import date
from wuxing import calc_wuxing


def test_wuxing_2026_07_15_ranking():
    """2026-07-15 丙午年未月庚寅日: 土极旺 金极旺 火旺 木旺 水平 — 验证排名顺序"""
    scores = calc_wuxing(date(2026, 7, 15))
    # 关键验证: 土(月令当令+午未合土)最强, 金(庚辛透+乙庚合化金)次之
    assert scores["土"]["score"] > scores["金"]["score"], \
        f"土({scores['土']['score']}) should be > 金({scores['金']['score']})"
    assert scores["金"]["score"] > scores["火"]["score"], \
        f"金({scores['金']['score']}) should be > 火({scores['火']['score']})"
    assert scores["木"]["score"] > scores["水"]["score"], \
        f"木({scores['木']['score']}) should be > 水({scores['水']['score']})"


def test_wuxing_levels_consistent():
    """分值 → 等级映射一致性"""
    scores = calc_wuxing(date(2026, 7, 15))
    for elem, data in scores.items():
        s = data["score"]
        level = data["level"]
        # 用阈值验证等级
        if s >= 8:
            assert level == "极旺", f"{elem}: {s} should be 极旺, got {level}"
        elif s >= 5:
            assert level in ("旺", "强"), f"{elem}: {s} should be 旺/强, got {level}"
        elif s >= 2:
            assert level == "平", f"{elem}: {s} should be 平, got {level}"
        elif s >= -1:
            assert level == "弱", f"{elem}: {s} should be 弱, got {level}"
        else:
            assert level == "极弱", f"{elem}: {s} should be 极弱, got {level}"


def test_wuxing_sum_conserved():
    """分值应该有一定范围，不应全是极端值"""
    scores = calc_wuxing(date(2026, 7, 15))
    vals = [d["score"] for d in scores.values()]
    # 至少有一个元素在中间范围 (-2 到 +8)
    has_mid = any(-2 <= v <= 8 for v in vals)
    assert has_mid, f"all scores are extreme: {vals}"


def test_wuxing_another_date():
    """测试另一天的结果是否合理"""
    scores = calc_wuxing(date(2026, 1, 1))  # 乙亥日，丑月
    for elem, data in scores.items():
        assert "score" in data
        assert "level" in data
        assert isinstance(data["score"], (int, float))
