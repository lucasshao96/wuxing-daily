"""神煞系统 — 冲煞、吉时、贵人。

输入: 日柱干支
输出: 冲煞生肖/方位、黄道吉时列表、天乙贵人
"""

from ganzhi import get_zodiac

# ── 六冲表 ─────────────────────────────────────────────
LIU_CHONG = {
    "子": "午", "丑": "未", "寅": "申", "卯": "酉",
    "辰": "戌", "巳": "亥",
    "午": "子", "未": "丑", "申": "寅", "酉": "卯",
    "戌": "辰", "亥": "巳",
}

# 煞方映射 (被冲地支 → 方位)
SHA_FANG = {
    "子": "正南", "午": "正北",
    "丑": "西南偏南", "未": "东北偏北",
    "寅": "西南偏西", "申": "东北偏东",
    "卯": "正西",   "酉": "正东",
    "辰": "西北偏西", "戌": "东南偏东",
    "巳": "西北偏北", "亥": "东南偏南",
}

# 黄道黑道十二神（按青龙起位置固定顺序）
HUANGDAO_SHEN = [
    ("青龙", True),  ("明堂", True),  ("天刑", False),  ("朱雀", False),
    ("金匮", True),  ("天德", True),  ("白虎", False),  ("玉堂", True),
    ("天牢", False), ("玄武", False), ("司命", True),  ("勾陈", False),
]

# 各日支的青龙起始时辰（地支索引）
QINGLONG_START = {
    "寅": 0, "申": 0,   # 寅申日 → 子时起青龙
    "卯": 2, "酉": 2,   # 卯酉日 → 寅时起青龙
    "辰": 4, "戌": 4,   # 辰戌日 → 辰时起青龙
    "巳": 6, "亥": 6,   # 巳亥日 → 午时起青龙
    "子": 8, "午": 8,   # 子午日 → 申时起青龙
    "丑": 10, "未": 10, # 丑未日 → 戌时起青龙
}

# 时辰地支列表
HOUR_ZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# 时辰对应的时间范围
HOUR_RANGE = {
    "子": "23-1", "丑": "1-3", "寅": "3-5", "卯": "5-7",
    "辰": "7-9", "巳": "9-11", "午": "11-13", "未": "13-15",
    "申": "15-17", "酉": "17-19", "戌": "19-21", "亥": "21-23",
}

# 天乙贵人 (日干 → 贵人生肖地支)
TIANYI_GUIREN = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
    "辛": ["午", "寅"],
}

# ── 计算函数 ──────────────────────────────────────────

def get_chong_zodiac(day_zhi: str) -> tuple[str, str]:
    """日支 → (冲的生肖, 煞方)"""
    chong_zhi = LIU_CHONG.get(day_zhi, day_zhi)
    zodiac = get_zodiac(chong_zhi)
    direction = SHA_FANG.get(chong_zhi, "未知")
    return zodiac, direction

def get_ji_shi(day_zhi: str) -> list[tuple[str, str]]:
    """日支 → [(时辰地支, 时间范围), ...] 仅返回黄道吉时"""
    start = QINGLONG_START.get(day_zhi, 0)
    ji_shi = []
    for i in range(12):
        shen_idx = (start + i) % 12
        if HUANGDAO_SHEN[shen_idx][1]:  # is 黄道
            zhi = HOUR_ZHI[i]
            ji_shi.append((zhi, HOUR_RANGE[zhi]))
    return ji_shi

def get_tianyi_gui_ren(day_gan: str) -> list[str]:
    """日干 → 天乙贵人地支列表"""
    return TIANYI_GUIREN.get(day_gan, [])

def get_all_shensha(date, day_gan: str, day_zhi: str) -> dict:
    """聚合神煞信息"""
    zodiac, direction = get_chong_zodiac(day_zhi)
    return {
        "chong": {"zodiac": zodiac, "direction": direction},
        "ji_shi": get_ji_shi(day_zhi),
        "gui_ren": get_tianyi_gui_ren(day_gan),
    }
