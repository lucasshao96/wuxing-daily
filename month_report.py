"""月报生成器 — 节气换月日发布月运总览。"""

from datetime import date, timedelta
from ganzhi import day_ganzhi, month_ganzhi, get_jieqi
from wuxing import calc_wuxing, MONTH_ZHI_WUXING
from shensha import get_chong_zodiac
from huangli import is_jie_month_change, JIE_MONTHS
from personalize import shi_shen


def build_monthly_section(d: date, users: list) -> dict | None:
    """节气换月日生成月报块，非换月日返回 None。"""
    if not is_jie_month_change(d):
        return None

    jieqi_name = get_jieqi(d)
    mg, mz = month_ganzhi(d)
    month_wx = MONTH_ZHI_WUXING.get(mz, "土")

    # 月令五行基调
    wx_mood = {
        "木": "木气当令，生长扩张之月。适合启动新项目、学习、社交。",
        "火": "火气当令，热情行动之月。适合推进、展示、竞争。",
        "土": "土气当令，稳定积累之月。适合收尾、整理、规划。",
        "金": "金气当令，收敛判断之月。适合决策、签约、理财。",
        "水": "水气当令，内省储能之月。适合学习、研究、休息。",
    }

    # 本月关键日（未来 ~30 天内的冲煞日）
    key_days = []
    for i in range(30):
        nd = d + timedelta(days=i)
        dg, dz = day_ganzhi(nd)
        chong_zod, sha_dir = get_chong_zodiac(dz)
        # 标记冲煞日和节气日
        next_jq = get_jieqi(nd)
        if next_jq or chong_zod:
            label = f"冲{chong_zod}" if chong_zod else ""
            if next_jq:
                label = f"🌾 {next_jq}" + (f" + {label}" if label else "")
            key_days.append({
                "date": nd.strftime("%m/%d"),
                "ganzhi": f"{dg}{dz}",
                "label": label,
            })

    # 每人月运提示
    user_tips = []
    for u in users:
        dm = u.get("day_master", "丁")
        # 日主 × 月令天干
        main_ss = shi_shen(dm, mg)
        user_tips.append({
            "name": u["name"],
            "day_master": f"{dm}火",
            "month_shi_shen": main_ss,
            "tip": _month_tip(main_ss),
        })

    return {
        "jieqi_name": jieqi_name,
        "month_ganzhi": f"{mg}{mz}",
        "month_wx": month_wx,
        "mood": wx_mood.get(month_wx, ""),
        "key_days": key_days[:8],  # 最多展示 8 个关键日
        "user_tips": user_tips,
    }


def _month_tip(shi_shen_name: str) -> str:
    tips = {
        "正财": "适合财务规划和理性消费，是梳理个人财务的好时机。",
        "偏财": "适合探索副业或研究投资，同时做好风险评估。",
        "正官": "适合签约、述职、推进重点工作，事业节奏加快。",
        "偏官": "适合解决遗留问题和参与竞争性事务。建议注意沟通方式。",
        "正印": "适合考试、读书、考证，学习效率较高。",
        "偏印": "适合深度钻研和独立项目。建议保持适度社交。",
        "食神": "适合创作、社交和享受生活。注意保持节奏不过度放松。",
        "伤官": "适合展示才华和创新。表达时多注意方式方法。",
        "比肩": "适合团队协作和竞赛。与人合作时注意分寸。",
        "劫财": "适合拓展社交圈。建议做好开销规划。",
    }
    return tips.get(shi_shen_name, "保持平常心，按部就班。")
