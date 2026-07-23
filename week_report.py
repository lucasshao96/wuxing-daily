"""周报生成器 — 周日生成下周运势预报。

分析未来7天的五行走势、关键冲煞日、特殊组合，
给出整体建议和每人个性化周度指南。
"""

import json, os
from datetime import date, timedelta
from collections import Counter

from ganzhi import day_ganzhi, year_ganzhi, month_ganzhi
from wuxing import calc_wuxing
from shensha import get_chong_zodiac
from huangli import get_jieqi

WEEK_LOG_PATH = "data/week_log.json"


# ── 每日日志 ──────────────────────────────────────────
def append_daily_log(d: date, wuxing_scores: dict, log_path: str = WEEK_LOG_PATH):
    """每天运行结束时追加当日五行摘要到日志文件。"""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logs = []

    date_str = d.isoformat()
    logs = [l for l in logs if l.get("date") != date_str]

    dg, dz = day_ganzhi(d)
    sorted_wx = sorted(wuxing_scores.items(), key=lambda x: x[1]["score"])
    log_entry = {
        "date": date_str,
        "day_ganzhi": f"{dg}{dz}",
        "strongest": sorted_wx[-1][0],
        "weakest": sorted_wx[0][0],
        "scores": {wx: data["score"] for wx, data in wuxing_scores.items()},
    }
    logs.append(log_entry)
    logs = logs[-14:]
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


# ── 辅助函数 ──────────────────────────────────────────

def _analyze_week_range(start: date, end: date) -> dict:
    """分析一段时间范围内的五行趋势。

    Returns: {
        "days": [{date, ganzhi, wuxing_scores, chong, jieqi}],
        "dominant": "木",     # 本周主导五行
        "climax_days": [...],  # 五行极旺的日子
        "clash_days": [...],   # 冲煞日
    }
    """
    days = []
    wx_counts = Counter()
    clash_days = []
    climax_days = []

    cur = start
    while cur <= end:
        dg, dz = day_ganzhi(cur)
        scores = calc_wuxing(cur)
        chong_zod, sha_dir = get_chong_zodiac(dz)
        jq = get_jieqi(cur)

        day_data = {
            "date": cur,
            "weekday": ["一","二","三","四","五","六","日"][cur.weekday()],
            "ganzhi": f"{dg}{dz}",
            "day_gan": dg, "day_zhi": dz,
            "wuxing": scores,
            "chong_zod": chong_zod,
            "sha_dir": sha_dir,
            "jieqi": jq,
        }
        days.append(day_data)

        # 统计最强五行
        sorted_wx = sorted(scores.items(), key=lambda x: x[1]["score"])
        wx_counts[sorted_wx[-1][0]] += 1
        wx_counts[sorted_wx[-2][0]] += 0.5  # 次强也有权重

        # 记录关键日
        if chong_zod:
            clash_days.append(day_data)
        strongest_score = sorted_wx[-1][1]["score"]
        if strongest_score >= 10:
            climax_days.append(day_data)

        cur += timedelta(days=1)

    dominant = wx_counts.most_common(1)[0][0] if wx_counts else "土"

    return {
        "days": days,
        "dominant": dominant,
        "climax_days": climax_days,
        "clash_days": clash_days,
    }


def _week_mood(dominant: str, season_wx: str) -> str:
    """根据主导五行和季节五行生成周度基调。"""
    moods = {
        "木": "生长扩张之周。适合启动新项目、学习新技能、拓展社交。思路活跃，行动力强。",
        "火": "热情行动之周。适合推进重点项目、展现个人能力、社交聚会。节奏偏快，注意劳逸结合。",
        "土": "稳定积累之周。适合整理规划、收尾总结、处理细节事务。节奏平稳，步步为营。",
        "金": "收敛判断之周。适合评估决策、财务规划、签约谈判。思路清晰，宜做关键决定。",
        "水": "内省储能之周。适合深度学习、独立研究、为下一阶段做准备。节奏放缓，厚积薄发。",
    }
    return moods.get(dominant, moods["土"])


def _weekly_user_tip(day_master: str, dominant: str) -> str:
    """根据用户日主和本周主导五行生成个性化周度建议。"""
    from personalize import shi_shen, GAN_WUXING, WUXING_SHENG, WUXING_KE

    # 找本周主导五行对应的天干代表
    wx_gan_map = {"木": "甲", "火": "丙", "土": "戊", "金": "庚", "水": "壬"}
    rep_gan = wx_gan_map.get(dominant, "戊")
    ss = shi_shen(day_master, rep_gan)

    tips = {
        "正财": "本周财务主题突出。适合梳理个人财务、制定储蓄计划。日常开销多加留意，避免冲动消费。",
        "偏财": "本周投资嗅觉敏锐。适合研究新赛道，但出手前多做功课。小额试探为主，别孤注一掷。",
        "正官": "本周事业节奏加快。适合推进重要项目、汇报述职。注意时间管理，别把自己逼太紧。",
        "偏官": "本周挑战与机遇并存。适合解决遗留难题，但沟通方式比平时多注意分寸。",
        "正印": "本周学习效率高。适合阅读、考证、深钻一门技能。独处时间比社交更有价值。",
        "偏印": "本周适合深度思考。灵感多但容易分散——挑一个方向聚焦，别同时开太多线程。",
        "食神": "本周创意高峰期。适合写作、设计、表达。社交运势不错，适合约朋友聚餐。",
        "伤官": "本周表达欲强。适合展示作品、发表观点。注意表达方式——内容好但措辞别太锋利。",
        "比肩": "本周合作运好。适合团队协作、运动竞赛。与人合作时多留几分余地，别太争强。",
        "劫财": "本周社交圈活跃。适合拓展人脉、参加活动。注意控制社交开销，别为面子花钱。",
    }
    dm_wx = GAN_WUXING.get(day_master, "")
    return tips.get(ss, f"本周{dominant}气当令，保持节奏，稳扎稳打。")


# ── 周报生成 ───────────────────────────────────────────
def build_weekly_section(d: date, users: list = None, log_path: str = WEEK_LOG_PATH) -> dict | None:
    """周日时生成下周运势预报。

    Returns: {
        "period": "07/21 - 07/27",
        "dominant": "木",
        "mood": "...",                    # 本周整体基调
        "key_days": [...],                # 3-5个关键日
        "daily": [...],                   # 每日摘要
        "advice": {"do": [...], "avoid": [...], "watch": [...]},
        "user_tips": [{"name": "..", "tip": "..."}],
    }
    """
    if d.weekday() != 6:
        return None

    # 上周回顾（从日志读取）
    logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                all_logs = json.load(f)
                cutoff = (d - timedelta(days=7)).isoformat()
                logs = [l for l in all_logs if l["date"] >= cutoff]
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    # 汇总上周趋势
    last_week_trend = ""
    if logs:
        strongest_count = Counter(l.get("strongest", "") for l in logs)
        last_week_trend = f"上周{strongest_count.most_common(1)[0][0]}气最旺"

    # 分析下周（未来7天）
    start = d + timedelta(days=1)
    end = d + timedelta(days=7)
    analysis = _analyze_week_range(start, end)

    # 季节五行（当前月令）
    _, mz = month_ganzhi(d)
    from wuxing import MONTH_ZHI_WUXING
    season_wx = MONTH_ZHI_WUXING.get(mz, "土")

    # 关键日（冲煞 + 五行极旺 + 节气）
    key_days = []
    for day in analysis["days"]:
        reasons = []
        if day["chong_zod"]:
            reasons.append(f"冲{day['chong_zod']}")
        if day["jieqi"]:
            reasons.append(f"🌾 {day['jieqi']}")
        sorted_wx = sorted(day["wuxing"].items(), key=lambda x: x[1]["score"])
        if sorted_wx[-1][1]["score"] >= 10:
            reasons.append(f"{sorted_wx[-1][0]}极旺")
        if reasons:
            key_days.append({
                "date": day["date"].strftime("%m/%d"),
                "weekday": day["weekday"],
                "ganzhi": day["ganzhi"],
                "reasons": reasons,
            })
    key_days = key_days[:5]  # 最多5个

    # 本周建议 + 生活指南
    advice = _weekly_advice(analysis["dominant"], analysis["clash_days"])
    lifestyle = _weekly_lifestyle(analysis["dominant"], analysis["clash_days"])

    # 每人个性化
    user_tips = []
    if users:
        for u in users:
            dm = u.get("day_master", "丁")
            tip = _weekly_user_tip(dm, analysis["dominant"])
            user_tips.append({"name": u["name"], "tip": tip})

    # 每日摘要
    daily = []
    for day in analysis["days"]:
            sorted_wx = sorted(day["wuxing"].items(), key=lambda x: x[1]["score"])
            daily.append({
                "date": day["date"].strftime("%m/%d"),
                "weekday": day["weekday"],
                "ganzhi": day["ganzhi"],
                "strongest": sorted_wx[-1][0],
                "chong": day["chong_zod"],
                "jieqi": day["jieqi"],
            })

    return {
        "period": f"{start.strftime('%m/%d')} - {end.strftime('%m/%d')}",
        "dominant": analysis["dominant"],
        "mood": _week_mood(analysis["dominant"], season_wx),
        "last_week_trend": last_week_trend,
        "key_days": key_days,
        "daily": daily,
        "advice": advice,
        "lifestyle": lifestyle,
        "user_tips": user_tips,
    }


def _weekly_advice(dominant: str, clash_days: list) -> dict:
    """根据主导五行和冲煞日生成周度行动建议。"""
    advice = {
        "木": {"do": ["启动新项目", "学习新技能", "拓展社交圈"],
               "avoid": ["拖延犹豫", "闭门造车", "过量饮酒"],
               "watch": ["木旺克土，注意脾胃消化"]},
        "火": {"do": ["推进重点项目", "展示个人能力", "社交聚会"],
               "avoid": ["过度劳累", "情绪冲动", "熬夜加班"],
               "watch": ["火旺克金，注意呼吸道和皮肤"]},
        "土": {"do": ["整理规划", "收尾总结", "处理文书细节"],
               "avoid": ["急躁冒进", "重大决策", "过度思虑"],
               "watch": ["土旺克水，注意肾脏和骨骼"]},
        "金": {"do": ["评估决策", "财务规划", "签约谈判"],
               "avoid": ["冲动消费", "感情用事", "大包大揽"],
               "watch": ["金旺克木，注意肝胆和筋骨"]},
        "水": {"do": ["深度学习", "独立研究", "战略规划"],
               "avoid": ["社交过多", "频繁切换任务", "焦虑担心"],
               "watch": ["水旺克火，注意心脏和血压"]},
    }
    result = advice.get(dominant, advice["土"])

    # 如果冲煞日 >= 2，加提醒
    if len(clash_days) >= 2:
        result["watch"].append("本周冲煞日较多，重要决策选在非冲煞日")

    return result


def _weekly_lifestyle(dominant: str, clash_days: list) -> dict:
    """根据本周主导五行和冲煞生成整周生活建议。"""
    lifestyle = {
        "木": {
            "health": "本周重点养肝。23:00前入睡，晨起拉伸5分钟。少喝酒，多吃绿色蔬菜。",
            "diet": ["菠菜", "芹菜", "绿茶", "枸杞", "绿豆"],
            "routine": "早睡早起，保持运动节奏。适合早晨锻炼，晚上早点收工。",
            "travel": "无特殊出行限制。" if len(clash_days) <= 1 else f"本周{len(clash_days)}天有冲煞，重要出行避开这些日子。",
        },
        "火": {
            "health": "本周重点养心。午间小憩15分钟，避免情绪大起大落。控制咖啡因。",
            "diet": ["红枣", "苦瓜", "番茄", "莲子", "菊花茶"],
            "routine": "避免连续熬夜。中午12-13点是最佳休息窗口，不要安排重要会议。",
            "travel": "无特殊出行限制。" if len(clash_days) <= 1 else f"本周{len(clash_days)}天有冲煞，重要出行避开这些日子。",
        },
        "土": {
            "health": "本周重点养脾胃。三餐规律，细嚼慢咽。少食生冷，多喝温水。",
            "diet": ["小米粥", "南瓜", "山药", "红薯", "红枣"],
            "routine": "保持稳定的作息节奏。饭后散步15分钟帮助消化，不要久坐。",
            "travel": "无特殊出行限制。" if len(clash_days) <= 1 else f"本周{len(clash_days)}天有冲煞，重要出行避开这些日子。",
        },
        "金": {
            "health": "本周重点养肺。多做深呼吸，保持室内通风。注意保暖防寒。",
            "diet": ["白萝卜", "雪梨", "银耳", "百合", "蜂蜜"],
            "routine": "适合做整理和规划。早晨做深呼吸练习，睡前用温水泡脚。",
            "travel": "无特殊出行限制。" if len(clash_days) <= 1 else f"本周{len(clash_days)}天有冲煞，重要出行避开这些日子。",
        },
        "水": {
            "health": "本周重点补肾。23:00前入睡比什么都重要。减少剧烈运动。",
            "diet": ["黑豆", "黑芝麻", "海带", "黑木耳", "核桃"],
            "routine": "适合内省和深度学习。晚上早睡，减少不必要的社交消耗。",
            "travel": "无特殊出行限制。" if len(clash_days) <= 1 else f"本周{len(clash_days)}天有冲煞，重要出行避开这些日子。",
        },
    }
    return lifestyle.get(dominant, lifestyle["土"])
