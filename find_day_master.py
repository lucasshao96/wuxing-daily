"""查八字日主 + 时柱 + 生肖 — 输入阳历生日和出生时间即可。

用法:
  python find_day_master.py 1998-07-07 08:55             # 仅时间
  python find_day_master.py 1998-07-07 08:55 北京         # 时间+出生地 (真太阳时)
  python find_day_master.py 1998-07-07 08:55 泉州         # 支持地级市

不需要懂八字，输生日就行。出生地可选——不填则按北京时间(UTC+8)算。
"""

import sys, os
from datetime import date, time, datetime
from ganzhi import day_ganzhi, year_ganzhi, month_ganzhi, hour_ganzhi, get_zodiac

# Windows GBK 终端兼容
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

GAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火",
    "戊": "土", "己": "土", "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 主要城市经度 (东经) — 用于真太阳时校正
CITY_LONGITUDE = {
    "北京": 116.4, "上海": 121.5, "广州": 113.3, "深圳": 114.1,
    "杭州": 120.2, "南京": 118.8, "成都": 104.1, "重庆": 106.5,
    "武汉": 114.3, "西安": 108.9, "郑州": 113.7, "济南": 117.0,
    "青岛": 120.4, "大连": 121.6, "沈阳": 123.4, "哈尔滨": 126.6,
    "长春": 125.3, "太原": 112.5, "石家庄": 114.5, "天津": 117.2,
    "长沙": 113.0, "南昌": 115.9, "福州": 119.3, "厦门": 118.1,
    "泉州": 118.6, "漳州": 117.6, "福州": 119.3,
    "昆明": 102.7, "贵阳": 106.7, "南宁": 108.3, "海口": 110.3,
    "兰州": 103.8, "西宁": 101.8, "银川": 106.3, "乌鲁木齐": 87.6,
    "拉萨": 91.1, "呼和浩特": 111.7, "合肥": 117.3, "苏州": 120.6,
    "无锡": 120.3, "宁波": 121.5, "温州": 120.7, "珠海": 113.6,
    "佛山": 113.1, "东莞": 113.8, "香港": 114.2, "澳门": 113.5,
    "台北": 121.5, "高雄": 120.3,
}


def true_solar_hour(hour: int, minute: int, city: str) -> tuple[int, int]:
    """真太阳时校正: 北京时间 → 当地真太阳时。

    北京时间的基准经度是东经 120°。每差 1° 经度差 4 分钟。
    返回校正后的 (hour, minute)。
    """
    if city not in CITY_LONGITUDE:
        return hour, minute  # 未知城市不校正

    lon = CITY_LONGITUDE[city]
    # 与东经 120° 的差值 (度) × 4 分钟/度
    offset_minutes = round((lon - 120.0) * 4)

    total = hour * 60 + minute + offset_minutes
    total = total % (24 * 60)  # 跨天回绕
    return total // 60, total % 60


def main():
    if len(sys.argv) < 2:
        print("用法: python find_day_master.py YYYY-MM-DD [HH:MM] [城市]")
        print("示例: python find_day_master.py 1998-07-07 08:55")
        print("示例: python find_day_master.py 1998-07-07 08:55 北京")
        print()
        print("出生地可选 — 用于真太阳时校正。不填则按北京时间(UTC+8)算。")
        sys.exit(1)

    # 解析日期
    try:
        y, m, d = map(int, sys.argv[1].split("-"))
        birth_date = date(y, m, d)
    except (ValueError, TypeError):
        print("日期格式错误，请用 YYYY-MM-DD 格式")
        sys.exit(1)

    # 解析时间 (可选)
    birth_hour, birth_minute = 12, 0  # 默认中午
    time_str = None
    if len(sys.argv) >= 3:
        try:
            time_str = sys.argv[2]
            birth_hour, birth_minute = map(int, sys.argv[2].split(":"))
        except (ValueError, TypeError):
            print("时间格式错误，请用 HH:MM 格式")
            sys.exit(1)

    # 出生地 (可选)
    city = None
    if len(sys.argv) >= 4:
        city = sys.argv[3]

    # 干支
    day_gan, day_zhi = day_ganzhi(birth_date)
    year_gan, year_zhi = year_ganzhi(birth_date)
    month_gan, month_zhi = month_ganzhi(birth_date)
    zodiac = get_zodiac(year_zhi)

    # 真太阳时校正
    if city and city in CITY_LONGITUDE:
        orig_h, orig_m = birth_hour, birth_minute
        birth_hour, birth_minute = true_solar_hour(birth_hour, birth_minute, city)
        if (birth_hour, birth_minute) != (orig_h, orig_m):
            print(f"[太阳时] 真太阳时校正 ({city} 东经{CITY_LONGITUDE[city]}°): "
                  f"{orig_h:02d}:{orig_m:02d} → {birth_hour:02d}:{birth_minute:02d}")
    elif city:
        print(f"[警告] 未找到城市「{city}」的经度数据，使用北京时间")

    hour_gan, hour_zhi = hour_ganzhi(birth_hour, day_gan)

    day_wx = GAN_WUXING[day_gan]

    print(f"\n生日: {birth_date}")
    if time_str:
        print(f"时间: {time_str}" + (f" ({city})" if city else ""))
    print(f"四柱: {year_gan}{year_zhi} {month_gan}{month_zhi} {day_gan}{day_zhi} {hour_gan}{hour_zhi}")
    print(f"日主: {day_gan}{day_wx}  |  生肖: {zodiac}")

    # 五行提示
    tips = {
        "木": "需补: 水(润木) > 金(修剪) — 穿衣首选黑/白，避开绿色过多",
        "火": "需补: 金 > 水 > 土 — 穿衣首选白/黑/卡其，避开红色/绿色",
        "土": "需补: 火 > 土 > 金 — 穿衣首选红/黄/白，避开绿色/黑色过多",
        "金": "需补: 土 > 金 > 水 — 穿衣首选黄/白/黑，避开红色/绿色",
        "水": "需补: 金 > 水 > 木 — 穿衣首选白/黑/绿，避开黄色/红色过多",
    }
    print(f"五行提示: {tips.get(day_wx, '请查阅完整八字分析')}")

    # 配置提示
    print(f"\n━━━ 复制下面这段到 users.json ━━━")
    print(f'{{"name":"你的名字","day_master":"{day_gan}","zodiac":"{zodiac}","email":"你的邮箱"}}')


if __name__ == "__main__":
    main()
