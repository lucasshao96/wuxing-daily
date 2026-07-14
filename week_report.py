"""周报生成器 — 周日自动总结本周 + 预览下周。

通过 data/week_log.json 追踪每日五行摘要。
"""

import json, os
from datetime import date, timedelta

from ganzhi import day_ganzhi, year_ganzhi, month_ganzhi
from wuxing import calc_wuxing
from shensha import get_chong_zodiac

WEEK_LOG_PATH = "data/week_log.json"

# ── 每日日志 ──────────────────────────────────────────
def append_daily_log(d: date, wuxing_scores: dict, log_path: str = WEEK_LOG_PATH):
    """每天运行结束时追加当日五行摘要到日志文件。"""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # 读取已有日志
    logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logs = []

    # 按日期去重
    date_str = d.isoformat()
    logs = [l for l in logs if l.get("date") != date_str]

    dg, dz = day_ganzhi(d)
    # 找出最强和最弱五行
    sorted_wx = sorted(wuxing_scores.items(), key=lambda x: x[1]["score"])
    log_entry = {
        "date": date_str,
        "day_ganzhi": f"{dg}{dz}",
        "strongest": sorted_wx[-1][0],
        "weakest": sorted_wx[0][0],
        "summary": f"{sorted_wx[-1][0]}旺{sorted_wx[0][0]}弱",
    }
    logs.append(log_entry)

    # 只保留最近 14 天
    logs = logs[-14:]

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# ── 周报生成 ───────────────────────────────────────────
def build_weekly_section(d: date, log_path: str = WEEK_LOG_PATH) -> dict | None:
    """周日时生成周报块，非周日返回 None。"""
    if d.weekday() != 6:
        return None

    # 读取本周日志（最近 7 天）
    logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                all_logs = json.load(f)
                cutoff = (d - timedelta(days=7)).isoformat()
                logs = [l for l in all_logs if l["date"] >= cutoff]
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    # 本周回顾
    week_days = []
    for i in range(7):
        day = d - timedelta(days=6 - i)
        dg, dz = day_ganzhi(day)
        log_entry = next((l for l in logs if l["date"] == day.isoformat()), None)
        summary = log_entry["summary"] if log_entry else "—"
        week_days.append({
            "weekday": ["一","二","三","四","五","六","日"][day.weekday()],
            "ganzhi": f"{dg}{dz}",
            "summary": summary,
        })

    # 下周预览（未来 7 天关键日）
    next_highlights = []
    for i in range(1, 8):
        nd = d + timedelta(days=i)
        dg, dz = day_ganzhi(nd)
        chong_zod, _ = get_chong_zodiac(dz)
        next_highlights.append({
            "date": nd.strftime("%m/%d"),
            "ganzhi": f"{dg}{dz}",
            "chong": chong_zod,
        })

    return {
        "week_days": week_days,
        "next_highlights": next_highlights,
    }
