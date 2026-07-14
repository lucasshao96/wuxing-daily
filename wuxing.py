"""子平法五行旺衰计算 — 四层计算引擎。

算法: 月令基础分 → 天干透出 → 地支通根 → 合化刑冲 → 退气惩罚 → 等级映射。
所有阈值均为模块级常量，可独立调参。
"""

from datetime import date
from ganzhi import day_ganzhi, year_ganzhi, month_ganzhi, hour_ganzhi

# ── 可调参数 ──────────────────────────────────────────
# 等级阈值
LEVEL_EXTREME_HIGH = 8    # 极旺
LEVEL_HIGH        = 5     # 旺/强
LEVEL_FLAT        = 2     # 平
LEVEL_WEAK        = -1    # 弱 (低于此为极弱)

# 月令基础分
MONTH_SCORE_DANGLING  = 3    # 当令（同五行）
MONTH_SCORE_JITU      = 2    # 季土额外加分（辰戌丑未月）
MONTH_SCORE_SHENGWO   = 1    # 生我（月令生此五行）
MONTH_SCORE_WOSHENG   = 0.5  # 我生（此五行生月令）
MONTH_SCORE_KEWO      = -1   # 克我（月令克此五行）
MONTH_SCORE_WOKE      = -0.5 # 我克（此五行克月令）

# 天干透出
GANTU_TOUCHU  = 2  # 每透出一个
GANTU_TONGGEN = 1  # 透出且有地支通根加分

# 地支通根
ZHI_BENQI = 3   # 本气根
ZHI_ZHONGQI = 2 # 中气根
ZHI_YUQI   = 1  # 余气根
ZHI_KUGEN  = 1.5 # 库根（辰戌丑未中的藏干）

# 合化
HUA_FULL  = 2   # 合化成功（化神在月令得地）
HUA_BAN   = 1   # 合绊（化神不得地）

# 三合/三会
SAN_HE_FULL = 4     # 三合方局成立
SAN_HE_HALF = 1.5   # 半合
SAN_HUI_FULL = 4    # 三会成立
SAN_HUI_HALF = 1.5  # 拱会

# 冲
CHONG_FULL   = -2   # 双方力量相当时各-2
CHONG_STRONG = -0.5 # 强者被弱冲时损失
CHONG_WEAK   = -3   # 弱者冲强时损失
CHONG_POWER_RATIO = 3  # 力量比 > 此值判定为弱冲强

# 刑
XING_SAN = -1.5  # 三刑（寅巳申）
XING_ER  = -1    # 二刑（丑戌未、子卯）
XING_ZI  = -1    # 自刑（午午、辰辰、酉酉、亥亥）

# 退气
TUIQI_PENALTY = -3  # 四季土月对前一季五行的退气惩罚

# ── 数据表 ────────────────────────────────────────────

# 地支藏干 {地支: {气: 天干}}
CANG_GAN = {
    "子": {"本气": "癸"},
    "丑": {"本气": "己", "中气": "癸", "余气": "辛"},
    "寅": {"本气": "甲", "中气": "丙", "余气": "戊"},
    "卯": {"本气": "乙"},
    "辰": {"本气": "戊", "中气": "乙", "余气": "癸"},
    "巳": {"本气": "丙", "中气": "庚", "余气": "戊"},
    "午": {"本气": "丁", "中气": "己"},
    "未": {"本气": "己", "中气": "丁", "余气": "乙"},
    "申": {"本气": "庚", "中气": "壬", "余气": "戊"},
    "酉": {"本气": "辛"},
    "戌": {"本气": "戊", "中气": "辛", "余气": "丁"},
    "亥": {"本气": "壬", "中气": "甲"},
}

# 天干→五行
GAN_WUXING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 地支→五行（本气五行，用于冲煞定位等）
ZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 五行生克关系
WUXING_SHENG = {  # 生: key 生 value
    "木": "火", "火": "土", "土": "金", "金": "水", "水": "木",
}
WUXING_KE = {  # 克: key 克 value
    "木": "土", "土": "水", "水": "火", "火": "金", "金": "木",
}

# 四季土月 → 退气五行
TUIQI_MAP = {"辰": "木", "未": "火", "戌": "金", "丑": "水"}

# 月令五行映射
MONTH_ZHI_WUXING = ZHI_WUXING  # 地支本气即月令五行

# ── 辅助函数 ──────────────────────────────────────────

def _wuxing_of_gan(gan: str) -> str:
    return GAN_WUXING.get(gan, "")

def _wuxing_of_zhi(zhi: str, qi: str = "本气") -> str:
    """取地支中指定气的五行"""
    gan = CANG_GAN.get(zhi, {}).get(qi, "")
    return GAN_WUXING.get(gan, "")

def _has_tonggen(gan: str, all_zhi: list[str]) -> bool:
    """检查天干在四柱地支中是否有通根（藏干同五行）"""
    gan_wx = _wuxing_of_gan(gan)
    for zhi in all_zhi:
        for qi, cg in CANG_GAN.get(zhi, {}).items():
            if GAN_WUXING.get(cg) == gan_wx:
                return True
    return False

def _count_zhi_wuxing(all_zhi: list[str], wx: str, qi_type: str) -> int:
    """统计地支中指定五行在指定气层的出现次数"""
    count = 0
    for zhi in all_zhi:
        cg = CANG_GAN.get(zhi, {}).get(qi_type, "")
        if GAN_WUXING.get(cg) == wx:
            count += 1
    return count

# ── 地支配对检测 ─────────────────────────────────────

# 六冲
LIU_CHONG_PAIRS = [("子","午"), ("丑","未"), ("寅","申"),
                    ("卯","酉"), ("辰","戌"), ("巳","亥")]

# 六合
LIU_HE_PAIRS = [("子","丑"), ("寅","亥"), ("卯","戌"),
                ("辰","酉"), ("巳","申"), ("午","未")]

# 三合局 {化神五行: (地支1, 地支2, 地支3)}
SAN_HE = {
    "水": ("申", "子", "辰"),
    "木": ("亥", "卯", "未"),
    "火": ("寅", "午", "戌"),
    "金": ("巳", "酉", "丑"),
}

# 三会局 {化神五行: (地支1, 地支2, 地支3)}
SAN_HUI = {
    "木": ("寅", "卯", "辰"),
    "火": ("巳", "午", "未"),
    "金": ("申", "酉", "戌"),
    "水": ("亥", "子", "丑"),
}

# 天干五合 {(干1,干2): 化神五行}
TIANGAN_HE = {
    ("甲","己"): "土", ("己","甲"): "土",
    ("乙","庚"): "金", ("庚","乙"): "金",
    ("丙","辛"): "水", ("辛","丙"): "水",
    ("丁","壬"): "木", ("壬","丁"): "木",
    ("戊","癸"): "火", ("癸","戊"): "火",
}

# ── 核心计算 ──────────────────────────────────────────

def calc_wuxing(d: date) -> dict[str, dict]:
    """计算给定日期的五行旺衰分数和等级。

    Returns: {"木": {"score": 5.5, "level": "旺"}, "火": {...}, ...}
    """
    # 获取四柱
    yg, yz = year_ganzhi(d)
    mg, mz = month_ganzhi(d)
    dg, dz = day_ganzhi(d)
    hg, hz = hour_ganzhi(9, dg)  # 固定用辰时(9点)代表当日

    all_gan = [yg, mg, dg, hg]
    all_zhi = [yz, mz, dz, hz]
    month_zhi = mz
    month_wx = MONTH_ZHI_WUXING.get(month_zhi, "土")

    scores = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}

    # ── 第一层: 月令得分 ──
    for wx in scores:
        if wx == month_wx:
            scores[wx] += MONTH_SCORE_DANGLING
            # 季土额外加分
            if wx == "土" and month_zhi in ("辰","戌","丑","未"):
                scores[wx] += MONTH_SCORE_JITU
        elif WUXING_SHENG.get(wx) == month_wx:
            scores[wx] += MONTH_SCORE_WOSHENG  # 我生月令
        elif WUXING_SHENG.get(month_wx) == wx:
            scores[wx] += MONTH_SCORE_SHENGWO  # 月令生我
        elif WUXING_KE.get(wx) == month_wx:
            scores[wx] += MONTH_SCORE_WOKE    # 我克月令
        elif WUXING_KE.get(month_wx) == wx:
            scores[wx] += MONTH_SCORE_KEWO    # 月令克我

    # ── 第二层: 天干透出 ──
    for gan in all_gan:
        wx = _wuxing_of_gan(gan)
        if wx:
            scores[wx] += GANTU_TOUCHU
            if _has_tonggen(gan, all_zhi):
                scores[wx] += GANTU_TONGGEN

    # ── 第三层: 地支通根 ──
    for qi_type, score_val in [("本气", ZHI_BENQI), ("中气", ZHI_ZHONGQI), ("余气", ZHI_YUQI)]:
        for wx in scores:
            count = _count_zhi_wuxing(all_zhi, wx, qi_type)
            if count > 0:
                scores[wx] += count * score_val

    # 库根: 辰为水库,戌为火库,丑为金库,未为木库
    ku_map = {"辰": "水", "戌": "火", "丑": "金", "未": "木"}
    for zhi in all_zhi:
        if zhi in ku_map:
            wx = ku_map[zhi]
            scores[wx] += ZHI_KUGEN

    # ── 第四层: 合化刑冲 ──

    # 天干五合
    for i in range(len(all_gan)):
        for j in range(i+1, len(all_gan)):
            pair = (all_gan[i], all_gan[j])
            if pair in TIANGAN_HE:
                hua_wx = TIANGAN_HE[pair]
                # 化神在月令得地？
                if month_wx == hua_wx or WUXING_SHENG.get(month_wx) == hua_wx:
                    mag = HUA_FULL
                else:
                    mag = HUA_BAN
                wx_i, wx_j = _wuxing_of_gan(all_gan[i]), _wuxing_of_gan(all_gan[j])
                scores[wx_i] -= mag
                scores[wx_j] -= mag
                scores[hua_wx] += mag * 2

    # 地支六合
    for i in range(len(all_zhi)):
        for j in range(i+1, len(all_zhi)):
            pair = (all_zhi[i], all_zhi[j])
            pair_rev = (all_zhi[j], all_zhi[i])
            for he_pair in LIU_HE_PAIRS:
                if pair == he_pair or pair_rev == he_pair:
                    hua_wx = MONTH_ZHI_WUXING.get(he_pair[1], "")
                    if month_wx == hua_wx:
                        mag = HUA_FULL
                    else:
                        mag = HUA_BAN
                    wx_i = MONTH_ZHI_WUXING.get(all_zhi[i], "")
                    wx_j = MONTH_ZHI_WUXING.get(all_zhi[j], "")
                    scores[wx_i] -= mag
                    scores[wx_j] -= mag
                    scores[hua_wx] += mag * 2

    # 地支六冲
    for i in range(len(all_zhi)):
        for j in range(i+1, len(all_zhi)):
            pair = (all_zhi[i], all_zhi[j])
            pair_rev = (all_zhi[j], all_zhi[i])
            for chong_pair in LIU_CHONG_PAIRS:
                if pair == chong_pair or pair_rev == chong_pair:
                    wx_i = MONTH_ZHI_WUXING.get(all_zhi[i], "")
                    wx_j = MONTH_ZHI_WUXING.get(all_zhi[j], "")
                    si = abs(scores.get(wx_i, 0))
                    sj = abs(scores.get(wx_j, 0))
                    if si > sj * CHONG_POWER_RATIO:
                        scores[wx_i] += CHONG_STRONG
                        scores[wx_j] += CHONG_WEAK
                    elif sj > si * CHONG_POWER_RATIO:
                        scores[wx_j] += CHONG_STRONG
                        scores[wx_i] += CHONG_WEAK
                    else:
                        scores[wx_i] += CHONG_FULL
                        scores[wx_j] += CHONG_FULL

    # 自刑: 午午、辰辰、酉酉、亥亥
    zi_xing_zhi = {"午", "辰", "酉", "亥"}
    zhi_counts = {}
    for z in all_zhi:
        zhi_counts[z] = zhi_counts.get(z, 0) + 1
    for zhi, count in zhi_counts.items():
        if zhi in zi_xing_zhi and count >= 2:
            wx = MONTH_ZHI_WUXING.get(zhi, "")
            scores[wx] += XING_ZI * (count - 1)

    # ── 退气惩罚 ──
    if month_zhi in TUIQI_MAP:
        wx = TUIQI_MAP[month_zhi]
        scores[wx] += TUIQI_PENALTY

    # ── 等级判定 ──
    result = {}
    for wx, score in scores.items():
        rounded = round(score, 1)
        if rounded >= LEVEL_EXTREME_HIGH:
            level = "极旺"
        elif rounded >= LEVEL_HIGH:
            level = "旺"
        elif rounded >= LEVEL_FLAT:
            level = "平"
        elif rounded >= LEVEL_WEAK:
            level = "弱"
        else:
            level = "极弱"
        result[wx] = {"score": rounded, "level": level}

    return result
