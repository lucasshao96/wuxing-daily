"""个性化分析引擎 — 十神判定 + 建议生成 + 配色 + 年度策略。

输入: 用户八字数据 + 当日干支
输出: 当日建议 + 配色方案 + 策略警报
"""

from datetime import date
from ganzhi import day_ganzhi, year_ganzhi, TIAN_GAN
from wuxing import calc_wuxing, CANG_GAN

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
        "msg": "⚠️ 本月子午冲最重，建议凡事多加留意。亥水入局带来新变数——机遇与风险并存。优先推进已论证的方向，暂缓全新尝试。"
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


# 十神简短含义（用于解读文本）
SHI_SHEN_MEANING = {
    "正财": "处理财务", "偏财": "灵活投资",
    "正官": "推进工作", "偏官": "应对挑战",
    "正印": "学习充电", "偏印": "深度思考",
    "食神": "创作放松", "伤官": "表达交流",
    "比肩": "合作共赢", "劫财": "社交拓展",
}


def analyze_cang_gan(day_master: str, day_zhi: str) -> list[dict]:
    """分析日支藏干对日主的十神关系。

    Returns: [{"gan": "甲", "shi_shen": "正印", "qi": "本气", "meaning": "学习思考"}, ...]
    """
    hidden = CANG_GAN.get(day_zhi, {})
    results = []
    for qi, gan in hidden.items():
        ss = shi_shen(day_master, gan)
        results.append({
            "gan": gan,
            "shi_shen": ss,
            "qi": qi,
            "meaning": SHI_SHEN_MEANING.get(ss, ""),
        })
    return results


def generate_daily_reading(day_master: str, day_gan: str, day_zhi: str, zodiac: str) -> str:
    """生成 2-3 句综合解读，串起日干十神 + 藏干 + 冲煞。"""
    dm_wx = GAN_WUXING[day_master]
    main_ss = shi_shen(day_master, day_gan)
    cang = analyze_cang_gan(day_master, day_zhi)

    sentences = []

    # 第一句: 日干十神主调
    main_meaning = SHI_SHEN_MEANING.get(main_ss, "")
    day_wx = GAN_WUXING[day_gan]
    sentences.append(
        f"明日{day_gan}{day_wx}为你的{main_ss}——建议关注{main_meaning}相关事项。"
    )

    # 第二句: 藏干分析
    cang_parts = []
    for c in cang:
        cang_parts.append(f"{c['gan']}({c['shi_shen']})")
    sentences.append(f"{day_zhi}中藏{'·'.join(cang_parts)}，暗含多层影响。")

    # 第三句: 综合行动建议
    good_ss = [c for c in cang if c["shi_shen"] in ("正印", "正官", "正财", "食神")]
    warn_ss = [c for c in cang if c["shi_shen"] in ("伤官", "偏官", "劫财")]
    tips = []
    if good_ss:
        tips.append(f"适合处理{good_ss[0]['meaning']}相关事务")
    if warn_ss:
        tips.append(f"在{warn_ss[0]['meaning']}方面多加留意")
    if tips:
        sentences.append("综合来看，" + "，".join(tips) + "。")

    return "".join(sentences)


def generate_lifestyle(day_master: str, day_zhi: str, wuxing_scores: dict, zodiac: str) -> dict:
    """根据五行旺衰和冲煞生成日常生活建议。

    Returns: {"health": "...", "diet": [...], "travel": "...", "routine": "..."}
    """
    # 找最弱和最强五行
    sorted_wx = sorted(wuxing_scores.items(), key=lambda x: x[1]["score"])
    weakest = sorted_wx[0][0]
    strongest = sorted_wx[-1][0]

    # 五行→五脏
    wx_organ = {"木": "肝", "火": "心", "土": "脾胃", "金": "肺", "水": "肾"}

    # 五行→养生建议
    wx_health = {
        "木": "养肝护肝。早睡（23:00前），少喝酒熬夜。",
        "火": "养心安神。午间小憩片刻，避免情绪过激。",
        "土": "健脾养胃。三餐规律，少食生冷油腻。",
        "金": "润肺防燥。深呼吸练习，多喝温水。",
        "水": "补肾藏精。23:00前入睡，减少消耗性活动。",
    }

    # 五行→对应食物
    wx_foods = {
        "木": ["绿色蔬菜（菠菜、芹菜）", "绿豆", "绿茶"],
        "火": ["红枣", "枸杞", "番茄", "苦瓜"],
        "土": ["小米粥", "南瓜", "山药", "红薯"],
        "金": ["白萝卜", "雪梨", "银耳", "百合"],
        "水": ["黑豆", "黑芝麻", "海带", "黑木耳"],
    }

    # 冲煞出行
    from shensha import get_chong_zodiac
    chong_zod, sha_dir = get_chong_zodiac(day_zhi)

    health = wx_health.get(weakest, "保持规律作息，适当运动。")
    diet = wx_foods.get(weakest, ["均衡饮食，多喝水"])[:3]

    travel = ""
    if zodiac == chong_zod:
        travel = f"明日是你的冲煞日，出行建议多加留意。重要安排尽量避开{sha_dir}。"
    else:
        travel = f"明日煞{sha_dir}，重要安排建议避开此方位。"

    routine = f"明日{weakest}弱，重点养护{wx_organ.get(weakest, '身体')}。"

    return {"health": health, "diet": diet, "travel": travel, "routine": routine}


def generate_advice(user: dict, d: date) -> dict:
    """为指定用户生成当日个性化建议。

    Args:
        user: {"name": "佳辉", "day_master": "丁", "zodiac": "鼠"}
        d: 日期

    Returns:
        {"day_master": "丁火", "shi_shen_main": "正财",
         "cang_gan": [...], "daily_reading": "...",
         "fit": [...], "avoid": "...", "zodiac_alert": "..."}
    """
    dg, dz = day_ganzhi(d)
    dm = user.get("day_master", "丁")
    zodiac = user.get("zodiac", "")

    # 日干十神 → 主建议
    main_ss = shi_shen(dm, dg)
    advice = SHI_SHEN_ADVICE.get(main_ss, {"fit": ["保持平常心"], "avoid": "无特别提醒"})

    # 藏干分析
    cang_gan = analyze_cang_gan(dm, dz)

    # 综合解读
    daily_reading = generate_daily_reading(dm, dg, dz, zodiac)

    # 冲煞检查
    from shensha import get_chong_zodiac
    chong_zod, _ = get_chong_zodiac(dz)
    zodiac_alert = ""
    if zodiac == chong_zod:
        zodiac_alert = f"🐒 明日冲{zodiac}，属{zodiac}的人重要决策建议多加留意"

    return {
        "day_master": f"{dm}{GAN_WUXING[dm]}",
        "shi_shen_main": main_ss,
        "cang_gan": cang_gan,
        "daily_reading": daily_reading,
        "fit": advice["fit"],
        "avoid": advice["avoid"],
        "zodiac_alert": zodiac_alert,
    }


def generate_colors(wuxing_scores: dict) -> dict:
    """根据五行旺衰生成配色建议。

    Returns:
        {"recommend": ["白色/金色", "黄色/棕色"], "avoid": ["绿色/青色"],
         "reason": "明日金弱需补，土生金为辅。木旺需避。"}
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
    reason = f"明日{weakest}弱需补{'，' + second_weakest + '为辅' if second_weakest != weakest else ''}。{strongest}旺需避。"

    return {"recommend": recommend, "avoid": avoid, "reason": reason}


def check_annual_alert(d: date) -> str | None:
    """检查日期是否落在年度策略关键时间窗口内。"""
    for alert in ANNUAL_ALERTS:
        if alert["start"] <= d <= alert["end"]:
            return alert["msg"]
    return None
