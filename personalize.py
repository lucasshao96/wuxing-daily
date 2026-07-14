"""个性化分析引擎 — 十神判定 + 建议生成 + 配色 + 年度策略。

输入: 用户八字数据 + 当日干支
输出: 当日建议 + 配色方案 + 策略警报
"""

from datetime import date
from ganzhi import day_ganzhi, year_ganzhi, TIAN_GAN
from wuxing import calc_wuxing

# ── 十神判定 ───────────────────────────────────────────
# 天干阴阳
GAN_YINYANG = {
    "甲": "阳", "丙": "阳", "戊": "阳", "庚": "阳", "壬": "阳",
    "乙": "阴", "丁": "阴", "己": "阴", "辛": "阴", "癸": "阴",
}

# 天干→五行
GAN_WUXING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 五行生克
WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_KE   = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 十神建议表
SHI_SHEN_ADVICE = {
    "正财": {"fit": ["财务规划", "理性消费"], "avoid": "过度计较得失"},
    "偏财": {"fit": ["投资理财", "副业探索"], "avoid": "投机心态"},
    "正官": {"fit": ["签约", "履行职责"], "avoid": "压力过大"},
    "偏官": {"fit": ["突破瓶颈", "竞争性事务"], "avoid": "冲突冲动"},
    "正印": {"fit": ["学习", "读书考证"], "avoid": "拖延想多做少"},
    "偏印": {"fit": ["钻研技术", "独处计划"], "avoid": "孤僻疑心"},
    "食神": {"fit": ["创作", "社交聚会"], "avoid": "懒散拖延"},
    "伤官": {"fit": ["表达创新", "展示才华"], "avoid": "口舌是非"},
    "比肩": {"fit": ["合作", "健身运动"], "avoid": "争执计较"},
    "劫财": {"fit": ["拓展人脉", "团队协作"], "avoid": "破财被占便宜"},
}

# 颜色映射
COLOR_MAP = {
    "木": ["绿色", "青色"],
    "火": ["红色", "紫色"],
    "土": ["黄色", "棕色"],
    "金": ["白色", "金色", "银色"],
    "水": ["黑色", "蓝色"],
}

# ── 年度策略时间窗口 ─────────────────────────────────
ANNUAL_ALERTS = [
    {
        "start": date(2026, 11, 7), "end": date(2026, 12, 6),
        "msg": "⚠️ 本月子午冲最重，诸事小心。亥水入局激活受伤的子水——机会出现但风险并存。只接8-10月讨论过的方向，不碰全新事物。"
    },
    {
        "start": date(2026, 8, 7), "end": date(2026, 10, 7),
        "msg": "⭐ 申酉月金到位，全年判断力最佳窗口。适合做重要决定。"
    },
]

# ── 函数 ──────────────────────────────────────────────

def shi_shen(day_master: str, other_gan: str) -> str:
    """计算日主对另一天干的十神关系。

    Args:
        day_master: 日主天干，如 "丁"
        other_gan: 另一天干，如 "庚"

    Returns:
        十神名称，如 "正财"
    """
    dm_wx = GAN_WUXING[day_master]
    og_wx = GAN_WUXING[other_gan]
    dm_yy = GAN_YINYANG[day_master]
    og_yy = GAN_YINYANG[other_gan]
    same_yy = (dm_yy == og_yy)  # 同性

    if dm_wx == og_wx:
        return "比肩" if same_yy else "劫财"
    elif WUXING_SHENG[dm_wx] == og_wx:
        return "食神" if same_yy else "伤官"
    elif WUXING_KE[dm_wx] == og_wx:
        return "偏财" if same_yy else "正财"
    elif WUXING_KE[og_wx] == dm_wx:
        return "偏官" if same_yy else "正官"
    elif WUXING_SHENG[og_wx] == dm_wx:
        return "偏印" if same_yy else "正印"

    return "未知"


def generate_advice(user: dict, d: date) -> dict:
    """为指定用户生成当日个性化建议。

    Args:
        user: {"name": "佳辉", "day_master": "丁", "zodiac": "鼠"}
        d: 日期

    Returns:
        {"day_master": "丁火", "shi_shen_main": "正财",
         "fit": [...], "avoid": "...", "zodiac_alert": "..."}
    """
    dg, dz = day_ganzhi(d)
    dm = user.get("day_master", "丁")
    zodiac = user.get("zodiac", "")

    # 日干十神 → 主建议
    main_ss = shi_shen(dm, dg)
    advice = SHI_SHEN_ADVICE.get(main_ss, {"fit": ["保持平常心"], "avoid": "无特别提醒"})

    # 冲煞检查
    from shensha import get_chong_zodiac
    chong_zod, _ = get_chong_zodiac(dz)
    zodiac_alert = ""
    if zodiac == chong_zod:
        zodiac_alert = f"🐒 今日冲{zodiac}，属{zodiac}的人今天小心行事"

    return {
        "day_master": f"{dm}火",
        "shi_shen_main": main_ss,
        "fit": advice["fit"],
        "avoid": advice["avoid"],
        "zodiac_alert": zodiac_alert,
    }


def generate_colors(wuxing_scores: dict) -> dict:
    """根据五行旺衰生成配色建议。

    Returns:
        {"recommend": ["白色/金色", "黄色/棕色"], "avoid": ["绿色/青色"],
         "reason": "今日金弱需补，土生金为辅。木旺需避。"}
    """
    # 按分数排序
    sorted_wx = sorted(wuxing_scores.items(), key=lambda x: x[1]["score"])
    weakest = sorted_wx[0][0]        # 最弱元素
    second_weakest = sorted_wx[1][0]  # 次弱
    strongest = sorted_wx[-1][0]      # 最强元素

    recommend = [f"{COLOR_MAP[weakest][0]}/{COLOR_MAP[weakest][1]}"]
    recommend.append(f"{COLOR_MAP[second_weakest][0]}/{COLOR_MAP[second_weakest][1]}")

    avoid = [f"{COLOR_MAP[strongest][0]}/{COLOR_MAP[strongest][1]}"]

    # 理由
    reason = f"今日{weakest}弱需补{'，' + second_weakest + '为辅' if second_weakest != weakest else ''}。{strongest}旺需避。"

    return {"recommend": recommend, "avoid": avoid, "reason": reason}


def check_annual_alert(d: date) -> str | None:
    """检查日期是否落在年度策略关键时间窗口内。"""
    for alert in ANNUAL_ALERTS:
        if alert["start"] <= d <= alert["end"]:
            return alert["msg"]
    return None
