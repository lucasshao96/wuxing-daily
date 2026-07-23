"""月报生成器 — 节气换月日发布月运总览。

分析未来~30天的五行大趋势、关键节气节点、每人月度指南。
"""

from datetime import date, timedelta
from ganzhi import day_ganzhi, month_ganzhi, get_jieqi
from wuxing import calc_wuxing, MONTH_ZHI_WUXING
from shensha import get_chong_zodiac
from huangli import is_jie_month_change, JIE_MONTHS
from personalize import shi_shen, GAN_WUXING


def build_monthly_section(d: date, users: list) -> dict | None:
    """节气换月日生成月运总览。

    Returns: {
        "month_name": "未月",
        "month_ganzhi": "乙未",
        "period": "07/07 - 08/06",
        "dominant": "土",
        "mood": "...",
        "energy_curve": "...",           # 五行变化趋势描述
        "key_dates": [...],               # 关键日（冲煞+节气+五行极值）
        "user_guides": [{name, overview, focus, caution}],
        "advice": {"do": [...], "avoid": [...], "health": "..."},
    }
    """
    if not is_jie_month_change(d):
        return None

    jieqi_name = get_jieqi(d)
    mg, mz = month_ganzhi(d)
    month_wx = MONTH_ZHI_WUXING.get(mz, "土")

    # 下个"节"的日期（月末边界）
    next_jie_date = None
    for i in range(1, 32):
        nd = d + timedelta(days=i)
        nq = get_jieqi(nd)
        if nq and nq in JIE_MONTHS:
            next_jie_date = nd
            break
    period_start = d.strftime("%m/%d")
    period_end = next_jie_date.strftime("%m/%d") if next_jie_date else "?"

    # 分析本月五行趋势（采样法：每隔3天取一个点）
    wx_trend = {}
    cur = d
    end = next_jie_date or (d + timedelta(days=30))
    while cur < end:
        scores = calc_wuxing(cur)
        for wx, data in scores.items():
            if wx not in wx_trend:
                wx_trend[wx] = []
            wx_trend[wx].append(data["score"])
        cur += timedelta(days=3)

    # 各五行平均分
    wx_avg = {wx: round(sum(vals) / len(vals), 1) for wx, vals in wx_trend.items()}

    # 月度基调
    mood = _month_mood(month_wx, jieqi_name or "")

    # 五行变化趋势文本
    sorted_wx = sorted(wx_avg.items(), key=lambda x: x[1], reverse=True)
    energy_parts = []
    for wx, avg in sorted_wx[:3]:
        level = "强" if avg >= 7 else ("旺" if avg >= 5 else ("平" if avg >= 3 else "弱"))
        energy_parts.append(f"{wx}(均{avg}/{level})")
    energy_curve = "整体趋势: " + " > ".join(energy_parts)

    # 关键日
    key_dates = []
    cur = d
    while cur < end and len(key_dates) < 8:
        dg, dz = day_ganzhi(cur)
        chong_zod, _ = get_chong_zodiac(dz)
        jq = get_jieqi(cur)
        reasons = []
        if chong_zod:
            reasons.append(f"冲{chong_zod}")
        if jq:
            reasons.append(f"🌾 {jq}")
        if reasons:
            key_dates.append({
                "date": cur.strftime("%m/%d"),
                "ganzhi": f"{dg}{dz}",
                "reasons": reasons,
            })
        cur += timedelta(days=1)

    # 月度建议
    advice = _monthly_advice(month_wx)

    # 每人月度指南
    user_guides = []
    if users:
        for u in users:
            dm = u.get("day_master", "丁")
            guide = _monthly_user_guide(dm, month_wx, mg)
            user_guides.append({"name": u["name"], **guide})

    return {
        "month_name": f"{jieqi_name}后·{mz}月",
        "month_ganzhi": f"{mg}{mz}",
        "period": f"{period_start} - {period_end}",
        "dominant": month_wx,
        "mood": mood,
        "energy_curve": energy_curve,
        "key_dates": key_dates,
        "advice": advice,
        "user_guides": user_guides,
    }


def _month_mood(month_wx: str, jieqi_name: str) -> str:
    """根据月令五行生成月度基调描述。"""
    base = {
        "木": "木气当令，万物生长。这是启动、学习、扩张的一个月。春生之气带动新想法和新机会。",
        "火": "火气当令，热情高涨。这是行动、展示、推进的一个月。能量充沛但要防止过热透支。",
        "土": "土气当令，稳重厚实。这是整理、积累、收尾的一个月。节奏不紧不慢，适合沉淀。",
        "金": "金气当令，锐利清晰。这是判断、决策、收敛的一个月。思路清楚，适合做关键决定。",
        "水": "水气当令，深沉内敛。这是思考、储蓄、准备的一个月。慢下来是为了更好地出发。",
    }
    return base.get(month_wx, base["土"])


def _monthly_advice(month_wx: str) -> dict:
    """月度行动建议。"""
    adv = {
        "木": {"do": ["启动新项目", "学习进修", "社交拓圈"], "avoid": ["犹豫观望", "过度保守", "酒精过量"], "health": "养肝护肝。早睡早起，多吃绿色蔬菜，少吃酸。"},
        "火": {"do": ["推进重点项目", "展示自己", "团队合作"], "avoid": ["过度透支", "情绪化决策", "熬夜"], "health": "养心安神。午休15分钟，少辣少油炸，控制咖啡因。"},
        "土": {"do": ["整理规划", "收尾工作", "锻炼身体"], "avoid": ["急功近利", "重大创新", "思虑过多"], "health": "健脾养胃。规律三餐，少食生冷，多吃小米南瓜。"},
        "金": {"do": ["评估决策", "理财规划", "签约"], "avoid": ["冲动消费", "过度承诺", "情绪化"], "health": "润肺防燥。多喝温水，多吃白色食物（梨、银耳）。"},
        "水": {"do": ["深度学习", "独立项目", "复盘总结"], "avoid": ["无效社交", "频繁切换方向", "焦虑"], "health": "补肾藏精。23:00前入睡，减少消耗性活动。"},
    }
    return adv.get(month_wx, adv["土"])


def _monthly_user_guide(day_master: str, month_wx: str, month_gan: str) -> dict:
    """为指定用户生成月度指南。

    Returns: {"overview": "...", "focus": "...", "caution": "..."}
    """
    from personalize import shi_shen, GAN_WUXING

    # 月干 × 日主 → 十神基调
    ss = shi_shen(day_master, month_gan)
    dm_wx = GAN_WUXING.get(day_master, "")

    guides = {
        "正财": {
            "overview": "财务主题月。收入来源或开销结构可能有调整，适合梳理和规划。",
            "focus": "财务规划、理性消费、制定预算",
            "caution": "冲动消费、计较短期得失",
        },
        "偏财": {
            "overview": "偏财活跃月。投资嗅觉敏锐，适合探索新赛道但注意风控。",
            "focus": "研究新领域、小额投资试探、副业尝试",
            "caution": "孤注一掷、轻信他人推荐",
        },
        "正官": {
            "overview": "事业推进月。工作节奏加快，有展示能力的机会，注意时间管理。",
            "focus": "推进重点项目、汇报述职、优化工作流程",
            "caution": "压力过大、忽视休息",
        },
        "偏官": {
            "overview": "挑战与突破月。会遇到一些压力测试，但也是能力跃升的窗口。",
            "focus": "解决遗留难题、建立权威、提升专业度",
            "caution": "与人碰撞时注意方式、控制情绪",
        },
        "正印": {
            "overview": "学习黄金月。思维能力在线，考试、考证、读书效率都高。",
            "focus": "系统学习、深度阅读、整理知识体系",
            "caution": "想多做少、完美主义拖延",
        },
        "偏印": {
            "overview": "深度思考月。灵感丰富但容易发散，适合聚焦一个方向深挖。",
            "focus": "独立研究、专业技术攻关、写长文",
            "caution": "孤僻离群、钻牛角尖",
        },
        "食神": {
            "overview": "创意享受月。表达欲和创造力都处于高位，社交也顺。",
            "focus": "创作输出、社交聚会、享受生活",
            "caution": "懒散拖延、过度放松",
        },
        "伤官": {
            "overview": "表达创新月。很想表达自己、展示作品。内容好但注意表达方式。",
            "focus": "发表观点、展示作品、头脑风暴",
            "caution": "言语冲突、过于犀利得罪人",
        },
        "比肩": {
            "overview": "合作共赢月。适合团队协作和良性竞争，注意分利公平。",
            "focus": "团队项目、运动竞赛、结盟合作",
            "caution": "过度争强、与人计较",
        },
        "劫财": {
            "overview": "社交拓展月。人脉圈子活跃，但社交开销也会增加。",
            "focus": "拓展人脉、参加行业活动、众筹合作",
            "caution": "为面子花钱、借钱给人",
        },
    }

    g = guides.get(ss, {"overview": "按部就班的一个月，保持节奏就好。", "focus": "维持日常节律", "caution": "无特别提醒"})
    return g
