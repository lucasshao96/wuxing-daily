"""HTML 邮件生成器 -- 五行日报。

复用 fund-daily-tracker 已验证的 QQ邮箱兼容 CSS 模板。
每人独立邮件，内容完全个性化。
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timezone, timedelta

from ganzhi import day_ganzhi, year_ganzhi, month_ganzhi, hour_ganzhi, get_nayin, get_jieqi
from wuxing import calc_wuxing
from shensha import get_chong_zodiac, get_ji_shi, get_tianyi_gui_ren
from huangli import get_yi_ji, get_jieqi_detail, get_pengzu_bai_ji, get_next_jieqi
from personalize import generate_advice, generate_colors, check_annual_alert, generate_lifestyle
from week_report import build_weekly_section
from month_report import build_monthly_section

# -- QQ邮箱兼容 CSS (源自 fund-daily-tracker) ----------
CSS = """
body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
       background:#f5f6fa; margin:0; padding:20px; color:#2d3436; }
.card { max-width:680px; margin:0 auto; background:#fff; border-radius:12px;
        box-shadow:0 2px 12px rgba(0,0,0,.08); overflow:hidden; }
.header { background:linear-gradient(135deg,#2d5016,#5a8f3d); color:#fff;
          padding:28px 32px; text-align:center; }
.header h1 { margin:0 0 8px; font-size:22px; }
.header p { margin:0; opacity:.85; font-size:14px; }
.section { padding:0 32px 20px; }
.section h2 { font-size:16px; margin:20px 0 12px; padding-bottom:6px;
              border-bottom:2px solid #5a8f3d; display:inline-block; }
.pillar-row { display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin:8px 0; }
.pillar { background:#f8f9ff; border-radius:8px; padding:10px 14px; text-align:center;
          min-width:70px; }
.pillar .ganzhi { font-size:18px; font-weight:700; color:#2d5016; }
.pillar .nayin { font-size:10px; color:#636e72; margin-top:2px; }
.wuxing-bar { margin:6px 0; display:flex; align-items:center; gap:8px; }
.wuxing-label { width:24px; font-size:13px; font-weight:600; text-align:right; }
.wuxing-track { flex:1; background:#eee; border-radius:4px; height:18px; overflow:hidden; }
.wuxing-fill { height:100%; border-radius:4px; transition:width 0.3s; }
.wuxing-score { width:60px; font-size:11px; text-align:left; color:#636e72; }
.wuxing-level { width:36px; font-size:11px; text-align:left; }
.chongsha-box { background:#fff8e1; border-left:4px solid #f39c12; border-radius:8px;
                padding:12px 16px; margin:8px 0; font-size:14px; }
.jishi-box { background:#f0fff4; border-radius:8px; padding:10px 16px; margin:8px 0;
             font-size:13px; }
.guiren-box { background:#f3e8ff; border-radius:8px; padding:10px 16px; margin:8px 0;
              font-size:13px; }
.yiji-box { background:#fafafa; border-radius:8px; padding:12px 16px; margin:8px 0; }
.yi { color:#00b894; } .ji { color:#d63031; }
.pengzu-box { background:#fef9e7; border-radius:8px; padding:10px 16px; margin:8px 0;
              font-size:13px; color:#7d6608; }
.jieqi-countdown { background:#e8f8f5; border-radius:8px; padding:10px 16px; margin:8px 0;
                   font-size:13px; color:#0e6655; }
.personal-card { background:#fafafa; border-radius:8px; padding:20px; margin:16px 0;
                 border-left:4px solid #5a8f3d; }
.personal-card h3 { margin:0 0 12px; font-size:16px; }
.advice-fit { color:#00b894; } .advice-avoid { color:#e17055; }
.color-box { display:flex; gap:16px; margin:8px 0; flex-wrap:wrap; }
.color-rec { background:#f0fff4; border-radius:6px; padding:8px 14px; font-size:13px; }
.color-avoid { background:#fff0f0; border-radius:6px; padding:8px 14px; font-size:13px; }
.alert-box { background:#ffe0e0; border-left:4px solid #d63031; border-radius:8px;
             padding:12px 16px; margin:8px 0; font-size:13px; }
.jieqi-card { background:#f0f8ff; border-radius:8px; padding:20px; margin:16px 0;
              border-left:4px solid #0984e3; }
.footer { text-align:center; padding:16px; font-size:11px; color:#b2bec3;
          border-top:1px solid #eee; }
.divider { border:none; border-top:1px dashed #ddd; margin:16px 0; }
.footer a { color:#b2bec3; }
"""

# -- SMTP 配置 ------------------------------------------
EMAIL_SENDER   = os.getenv("EMAIL_SENDER") or ""
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") or ""
EMAIL_SMTP     = os.getenv("EMAIL_SMTP") or "smtp.qq.com"
EMAIL_PORT     = int(os.getenv("EMAIL_PORT") or "587")

BEIJING = timezone(timedelta(hours=8))


# -- 纯文本渲染 ----------------------------------------
def render_plain(report: dict) -> str:
    """生成纯文本版邮件"""
    today = report["date"]
    lines = [
        f"🎋 {today.strftime('%Y年%m月%d日')} {report['weekday']} 明日五行预报",
        "=" * 40,
        f"📅 明日四柱: {report['year_ganzhi']}年 {report['month_ganzhi']}月 {report['day_ganzhi']}日 {report['hour_ganzhi']}时",
        f"   纳音: 年柱{report['nayin_year']} 月柱{report['nayin_month']} 日柱{report['nayin_day']} 时柱{report['nayin_hour']}",
        "",
        "🔥 五行旺衰:",
    ]
    for wx, data in report["wuxing"].items():
        bar = "█" * int(data["score"] * 1.5) if data["score"] > 0 else "░" * 3
        lines.append(f"   {wx}: {bar} {data['level']} ({data['score']})")

    lines += [
        "",
        f"⚡ 明日冲煞: 冲{report['chong_zodiac']} 煞{report['sha_direction']}",
        f"⏰ 吉时: {', '.join(f'{z}({t})' for z,t in report['ji_shi'])}",
    ]
    if report.get("gui_ren"):
        lines.append(f"👤 天乙贵人: {'、'.join(report['gui_ren'])}")

    lines += [
        f"📜 宜: {'、'.join(report['yi'])}  |  忌: {'、'.join(report['ji'])}",
    ]
    if report.get("pengzu"):
        lines.append("⚠️ 彭祖百忌（传统说法，仅供参考）:")
        pz = report['pengzu']
        lines.append(f"   「{pz['gan']}」")
        lines.append(f"   → {pz.get('gan_explain', '')}")
        lines.append(f"   「{pz['zhi']}」")
        lines.append(f"   → {pz.get('zhi_explain', '')}")

    if report.get("next_jieqi"):
        nj = report["next_jieqi"]
        lines.append(f"🌾 下一个节气: {nj['name']} ({nj['date']})，还有 {nj['days']} 天")

    for user_block in report["users"]:
        lines += [
            "",
            f"━━━ {user_block['name']} ━━━",
            f"🎯 你的建议: {user_block['advice']['shi_shen_main']}日",
        ]
        if user_block["advice"].get("daily_reading"):
            lines.append(f"   📖 {user_block['advice']['daily_reading']}")
        if user_block["advice"].get("cang_gan"):
            cg_text = " · ".join(f'{c["gan"]}→{c["shi_shen"]}({c["meaning"]})' for c in user_block["advice"]["cang_gan"])
            lines.append(f"   藏干: {cg_text}")
        lines += [
            f"   🌕 适合: {'、'.join(user_block['advice']['fit'])}",
            f"   🌑 注意: {user_block['advice']['avoid']}",
            f"   🎨 {user_block['colors']['reason']}",
        ]
        if user_block["advice"].get("zodiac_alert"):
            lines.append(f"   {user_block['advice']['zodiac_alert']}")
        ls = user_block.get("lifestyle", {})
        if ls:
            lines += [
                f"   💪 健康: {ls['health']}",
                f"   🍽️ 饮食: {'、'.join(ls['diet'])}",
                f"   🚗 出行: {ls['travel']}",
                f"   ⏰ 作息: {ls['routine']}",
            ]
        if user_block.get("alert"):
            lines.append(f"   {user_block['alert']}")

    if report.get("jieqi_detail"):
        jq = report["jieqi_detail"]
        lines += [
            "",
            f"🌾 {jq['title']}",
            f"   {jq['meaning']}",
            f"   五行: {jq['wuxing_shift']}",
            f"   养生: {jq['health']}",
            f"   饮食: {jq['food']}",
            f"   {jq['daily_tip']}",
        ]

    if report.get("weekly"):
        w = report["weekly"]
        lines += [
            "",
            "=" * 40,
            f"📊 下周运势预报 ({w['period']})",
            "=" * 40,
            f"   本周主导: {w['dominant']}气",
            f"   基调: {w['mood']}",
        ]
        if w["last_week_trend"]:
            lines.append(f"   {w['last_week_trend']}")
        lines += ["", "   📋 每日速览:"]
        for day in w["daily"]:
            flags = []
            if day["chong"]: flags.append(f"冲{day['chong']}")
            if day["jieqi"]: flags.append(f"🌾{day['jieqi']}")
            flag_text = f" ({', '.join(flags)})" if flags else ""
            lines.append(f"   {day['date']} {day['weekday']} {day['ganzhi']} {day['strongest']}旺{flag_text}")
        if w.get("key_days"):
            lines.append("")
            for kd in w["key_days"]:
                lines.append(f"   ⚡ {kd['date']} {kd['weekday']} {kd['ganzhi']}: {', '.join(kd['reasons'])}")
        adv = w["advice"]
        lines += [
            "",
            f"   ✅ 适合: {' · '.join(adv['do'])}",
            f"   ❌ 不适合: {' · '.join(adv['avoid'])}",
            f"   ⚠️ 注意: {' · '.join(adv['watch'])}",
        ]
        ls = w.get("lifestyle", {})
        if ls:
            lines += [
                "",
                f"   💪 健康: {ls.get('health', '')}",
                f"   🍽️ 饮食: {'、'.join(ls.get('diet', []))}",
                f"   ⏰ 作息: {ls.get('routine', '')}",
                f"   🚗 出行: {ls.get('travel', '')}",
            ]
        if w.get("user_tips"):
            lines.append("")
            for ut in w["user_tips"]:
                lines.append(f"   👤 {ut['name']}: {ut['tip']}")

    if report.get("monthly"):
        m = report["monthly"]
        lines += [
            "",
            "=" * 40,
            f"📆 月运总览 ({m['period']})",
            "=" * 40,
            f"   月令: {m['month_ganzhi']} | {m['dominant']}气当令",
            f"   基调: {m['mood']}",
            f"   {m['energy_curve']}",
        ]
        if m.get("key_dates"):
            lines.append("")
            for kd in m["key_dates"]:
                lines.append(f"   ⚡ {kd['date']} {kd['ganzhi']}: {', '.join(kd['reasons'])}")
        adv = m["advice"]
        lines += [
            "",
            f"   ✅ 适合: {' · '.join(adv['do'])}",
            f"   ❌ 不适合: {' · '.join(adv['avoid'])}",
            f"   💪 健康: {adv['health']}",
        ]
        if m.get("user_guides"):
            lines.append("")
            for ug in m["user_guides"]:
                lines += [
                    f"   👤 {ug['name']}: {ug['overview']}",
                    f"      重点: {ug['focus']}",
                    f"      注意: {ug['caution']}",
                ]

    lines += [
        "",
        "-" * 40,
        "基于中国传统干支历法的数学计算，仅供文化参考和娱乐用途。",
        "不构成任何形式的预测、建议或指导。",
    ]
    return "\n".join(lines)


# -- HTML 渲染 ------------------------------------------

def _wuxing_bar_color(wx: str) -> str:
    colors = {"木": "#00b894", "火": "#e17055", "土": "#fdcb6e",
              "金": "#dfe6e9", "水": "#0984e3"}
    return colors.get(wx, "#636e72")


def render_html(report: dict) -> str:
    """生成 HTML 版邮件"""
    today = report["today"]
    parts = [f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{CSS}</style></head><body>
<div class="card">
<div class="header">
  <h1>🎋 {today.strftime('%Y年%m月%d日')} {report['weekday']} 明日五行预报</h1>
  <p>晚上看明天的，早上照着穿</p>
</div>"""]

    # -- 干支区（四柱）--
    parts.append('<div class="section"><h2>📅 明日四柱</h2>')
    parts.append('<div class="pillar-row">')
    for label, gz, nayin in [
        ("年柱", report["year_ganzhi"], report["nayin_year"]),
        ("月柱", report["month_ganzhi"], report["nayin_month"]),
        ("日柱", report["day_ganzhi"], report["nayin_day"]),
        ("时柱", report["hour_ganzhi"], report["nayin_hour"]),
    ]:
        parts.append(f'<div class="pillar"><div style="font-size:10px;color:#636e72">{label}</div>'
                     f'<div class="ganzhi">{gz}</div>'
                     f'<div class="nayin">{nayin}</div></div>')
    parts.append('</div></div>')

    # -- 五行旺衰（带分数）--
    parts.append('<div class="section"><h2>🔥 五行旺衰</h2>')
    for wx in ["木","火","土","金","水"]:
        data = report["wuxing"].get(wx, {"score":0,"level":"平"})
        s = data["score"]
        pct = min(100, max(5, (s + 2) * 10))  # map [-2, 8] -> [0%, 100%], min 5%
        color = _wuxing_bar_color(wx)
        parts.append(f'<div class="wuxing-bar">'
                     f'<div class="wuxing-label">{wx}</div>'
                     f'<div class="wuxing-track"><div class="wuxing-fill" style="width:{pct}%;background:{color}"></div></div>'
                     f'<div class="wuxing-score">{s}</div>'
                     f'<div class="wuxing-level">{data["level"]}</div>'
                     f'</div>')
    parts.append('</div>')

    # -- 冲煞 + 吉时 + 贵人 --
    parts.append('<div class="section"><h2>⚡ 明日冲煞</h2>')
    parts.append(f'<div class="chongsha-box">'
                 f'🐒 <b>寅申相冲（冲{report["chong_zodiac"]}）</b> — 属{report["chong_zodiac"]}的人今天重要决策多加留意<br>'
                 f'🧭 <b>煞{report["sha_direction"]}</b> -- 重要事情避开此方位</div>')

    ji_shi_text = " · ".join(f"{z}时({t})" for z, t in report["ji_shi"])
    parts.append(f'<div class="jishi-box">⏰ 吉时: {ji_shi_text}</div>')

    if report.get("gui_ren"):
        gui_ren_text = "、".join(report["gui_ren"])
        parts.append(f'<div class="guiren-box">👤 天乙贵人: <b>{gui_ren_text}</b> — 明日求助可找属{"、".join(report["gui_ren_zodiac"])}的朋友</div>')

    parts.append('</div>')

    # -- 宜忌 + 彭祖百忌 --
    yi_text = " · ".join(f'<span class="yi">✅ {y}</span>' for y in report["yi"])
    ji_text = " · ".join(f'<span class="ji">❌ {j}</span>' for j in report["ji"])
    parts.append('<div class="section"><h2>📜 明日宜忌</h2>')
    parts.append(f'<div class="yiji-box">{yi_text}<br>{ji_text}</div>')

    if report.get("pengzu"):
        pz = report["pengzu"]
        parts.append(f'<div class="pengzu-box">'
                     f'<div style="font-weight:600;margin-bottom:4px">⚠️ 彭祖百忌 <span style="font-weight:400;color:#999;font-size:11px">— 传统说法，仅供参考</span></div>'
                     f'<div style="margin-bottom:4px"><b>「{pz["gan"]}」</b></div>'
                     f'<div style="font-size:12px;color:#666;margin-bottom:8px">→ {pz.get("gan_explain", "")}</div>'
                     f'<div style="margin-bottom:4px"><b>「{pz["zhi"]}」</b></div>'
                     f'<div style="font-size:12px;color:#666">→ {pz.get("zhi_explain", "")}</div>'
                     f'</div>')
    parts.append('</div>')

    # -- 节气倒计时 --
    if report.get("next_jieqi"):
        nj = report["next_jieqi"]
        parts.append('<div class="section">')
        parts.append(f'<div class="jieqi-countdown">🌾 下一个节气: <b>{nj["name"]}</b> ({nj["date"].strftime("%m/%d")})，还有 <b>{nj["days"]}</b> 天</div>')
        parts.append('</div>')

    # -- 个性化建议 --
    parts.append('<div class="section"><h2>🎯 给你的建议</h2>')
    for user_block in report["users"]:
        a = user_block["advice"]
        parts.append(f'<div class="personal-card">'
                     f'<h3>{user_block["name"]} — {a["day_master"]}日主 · 明日{report["day_ganzhi"]}日</h3>'
                     f'<div style="font-size:15px;font-weight:600;color:#2d5016">→ {a["shi_shen_main"]}日</div>')

        # 综合解读
        if a.get("daily_reading"):
            parts.append(f'<div style="margin:10px 0;font-size:14px;line-height:1.7;color:#555">'
                         f'📖 {a["daily_reading"]}</div>')

        # 藏干分析
        if a.get("cang_gan"):
            parts.append('<div style="margin:8px 0;font-size:13px;color:#636e72">')
            parts.append('日支藏干: ')
            cg_text = " · ".join(f'{c["gan"]}→{c["shi_shen"]}({c["meaning"]})' for c in a["cang_gan"])
            parts.append(cg_text)
            parts.append('</div>')

        fit_text = " · ".join(a["fit"])
        parts.append(f'<div class="advice-fit" style="margin-top:10px">🌕 适合: {fit_text}</div>')
        parts.append(f'<div class="advice-avoid">🌑 注意: {a["avoid"]}</div>')

        if a.get("zodiac_alert"):
            parts.append(f'<div style="margin-top:8px;color:#e17055;font-size:13px">{a["zodiac_alert"]}</div>')

        # 配色
        c = user_block["colors"]
        parts.append('<div style="margin-top:10px"><b>🎨 明日配色</b></div>')
        parts.append('<div class="color-box">')
        for rec in c["recommend"]:
            parts.append(f'<div class="color-rec">✅ {rec}</div>')
        for av in c["avoid"]:
            parts.append(f'<div class="color-avoid">❌ {av}</div>')
        parts.append('</div>')
        parts.append(f'<div style="font-size:12px;color:#636e72;margin-top:4px">💡 {c["reason"]}</div>')

        # 生活建议
        ls = user_block.get("lifestyle", {})
        if ls:
            parts.append('<div style="margin-top:12px;background:#f9fafb;border-radius:8px;padding:12px 16px;font-size:13px;line-height:1.8">')
            parts.append(f'<div style="font-weight:600;margin-bottom:6px">🏠 明日生活建议</div>')
            parts.append(f'<div>💪 <b>健康:</b> {ls["health"]}</div>')
            parts.append(f'<div>🍽️ <b>饮食:</b> {"、".join(ls["diet"])}</div>')
            parts.append(f'<div>🚗 <b>出行:</b> {ls["travel"]}</div>')
            parts.append(f'<div>⏰ <b>作息:</b> {ls["routine"]}</div>')
            parts.append('</div>')

        # 年度策略警报
        if user_block.get("alert"):
            parts.append(f'<div class="alert-box">{user_block["alert"]}</div>')

        parts.append('</div>')
    parts.append('</div>')

    # -- 节气长版（仅节气日）--
    if report.get("jieqi_detail"):
        jq = report["jieqi_detail"]
        parts.append(f'<div class="section"><div class="jieqi-card">'
                     f'<h3>{jq["title"]}</h3>'
                     f'<p><b>含义:</b> {jq["meaning"]}</p>'
                     f'<p><b>五行转换:</b> {jq["wuxing_shift"]}</p>'
                     f'<p><b>养生:</b> {jq["health"]}</p>'
                     f'<p><b>饮食:</b> {jq["food"]}</p>'
                     f'<p>💡 {jq["daily_tip"]}</p>'
                     f'</div></div>')

    # -- 周报（仅周日）--
    if report.get("weekly"):
        w = report["weekly"]
        parts.append(f'<div class="section"><h2>📊 下周运势预报 ({w["period"]})</h2>')
        parts.append(f'<div style="background:#f8f9ff;border-radius:8px;padding:16px;margin:8px 0;font-size:14px;line-height:1.8">'
                     f'<div style="font-size:16px;font-weight:700;color:#2d5016;margin-bottom:8px">本周主导: {w["dominant"]}气</div>'
                     f'<div style="color:#555">{w["mood"]}</div>')
        if w.get("last_week_trend"):
            parts.append(f'<div style="color:#636e72;font-size:12px;margin-top:6px">{w["last_week_trend"]}</div>')
        parts.append('</div>')

        # 每日速览
        parts.append('<div style="font-size:13px;line-height:1.8;margin:8px 0"><b>📋 每日速览</b></div>')
        for day in w["daily"]:
            flags = []
            if day["chong"]: flags.append(f'冲{day["chong"]}')
            if day["jieqi"]: flags.append(f'🌾{day["jieqi"]}')
            flag_text = f' <span style="color:#e17055;font-size:11px">({" · ".join(flags)})</span>' if flags else ""
            parts.append(f'<div style="font-size:13px;padding:3px 0">'
                         f'{day["date"]} 周{day["weekday"]} · {day["ganzhi"]} · {day["strongest"]}旺{flag_text}</div>')

        # 关键日
        if w.get("key_days"):
            parts.append('<div style="font-size:13px;margin-top:8px"><b>⚡ 重点关注日</b></div>')
            for kd in w["key_days"]:
                parts.append(f'<div style="font-size:12px;padding:3px 0;color:#e17055">'
                             f'{kd["date"]} 周{kd["weekday"]} {kd["ganzhi"]}: {", ".join(kd["reasons"])}</div>')

        # 行动建议
        adv = w["advice"]
        parts.append(f'<div style="background:#f0fff4;border-radius:8px;padding:12px;margin:12px 0;font-size:13px;line-height:1.8">'
                     f'<div>✅ <b>适合:</b> {" · ".join(adv["do"])}</div>'
                     f'<div style="color:#e17055">❌ <b>不适合:</b> {" · ".join(adv["avoid"])}</div>'
                     f'<div>⚠️ <b>注意:</b> {" · ".join(adv["watch"])}</div>'
                     f'</div>')

        # 整周生活建议
        ls = w.get("lifestyle", {})
        if ls:
            parts.append(f'<div style="background:#f9fafb;border-radius:8px;padding:12px 16px;margin:8px 0;font-size:13px;line-height:1.8">'
                         f'<div style="font-weight:600;margin-bottom:6px">🏠 整周生活指南</div>'
                         f'<div>💪 <b>健康:</b> {ls.get("health", "")}</div>'
                         f'<div>🍽️ <b>饮食推荐:</b> {"、".join(ls.get("diet", []))}</div>'
                         f'<div>⏰ <b>作息:</b> {ls.get("routine", "")}</div>'
                         f'<div>🚗 <b>出行:</b> {ls.get("travel", "")}</div>'
                         f'</div>')

        # 每人周度建议
        if w.get("user_tips"):
            parts.append('<div style="background:#fafafa;border-radius:8px;padding:12px 16px;margin:8px 0;font-size:13px;line-height:1.8">')
            for ut in w["user_tips"]:
                parts.append(f'<div style="padding:4px 0"><b>👤 {ut["name"]}</b>: {ut["tip"]}</div>')
            parts.append('</div>')
        parts.append('</div>')

    # -- 月报（仅节气换月日）--
    if report.get("monthly"):
        m = report["monthly"]
        parts.append(f'<div class="section"><h2>📆 月运总览 ({m["period"]})</h2>')
        parts.append(f'<div style="background:#f0f8ff;border-left:4px solid #0984e3;border-radius:8px;padding:16px;margin:8px 0;font-size:14px;line-height:1.8">'
                     f'<div style="font-size:16px;font-weight:700;color:#0747a6;margin-bottom:8px">{m["month_ganzhi"]} · {m["dominant"]}气当令</div>'
                     f'<div style="color:#555">{m["mood"]}</div>'
                     f'<div style="color:#636e72;font-size:12px;margin-top:6px">{m["energy_curve"]}</div>'
                     f'</div>')

        # 关键日
        if m.get("key_dates"):
            parts.append('<div style="font-size:13px;margin:8px 0"><b>⚡ 本月关键日</b></div>')
            for kd in m["key_dates"]:
                parts.append(f'<div style="font-size:12px;padding:2px 0;color:#e17055">'
                             f'{kd["date"]} {kd["ganzhi"]}: {", ".join(kd["reasons"])}</div>')

        # 月度建议
        adv = m["advice"]
        parts.append(f'<div style="background:#f0fff4;border-radius:8px;padding:12px;margin:12px 0;font-size:13px;line-height:1.8">'
                     f'<div>✅ <b>适合:</b> {" · ".join(adv["do"])}</div>'
                     f'<div style="color:#e17055">❌ <b>不适合:</b> {" · ".join(adv["avoid"])}</div>'
                     f'<div>💪 <b>健康:</b> {adv["health"]}</div>'
                     f'</div>')

        # 每人月度指南
        if m.get("user_guides"):
            parts.append('<div style="background:#fafafa;border-radius:8px;padding:12px 16px;margin:8px 0;font-size:13px;line-height:1.8">')
            for ug in m["user_guides"]:
                parts.append(f'<div style="padding:6px 0;border-bottom:1px solid #eee">'
                             f'<div style="font-weight:600">👤 {ug["name"]}</div>'
                             f'<div style="color:#555">{ug["overview"]}</div>'
                             f'<div style="color:#00b894">✅ 重点: {ug["focus"]}</div>'
                             f'<div style="color:#e17055">⚠️ 注意: {ug["caution"]}</div>'
                             f'</div>')
            parts.append('</div>')
        parts.append('</div>')

    # -- Footer --
    parts.append(f'<div class="footer">⏰ {datetime.now(BEIJING).strftime("%H:%M:%S")} BJT | '
                 f'基于中国传统干支历法的数学计算，仅供文化参考和娱乐用途。'
                 f'<br>不构成任何形式的预测、建议或指导。'
                 f'</div></div></body></html>')

    return "\n".join(parts)


# -- 报表数据聚合 ---------------------------------------
def build_report_data(d: date, users: list) -> dict:
    """聚合所有模块数据，生成邮件渲染用的完整数据结构。"""
    # 干支
    yg, yz = year_ganzhi(d)
    mg, mz = month_ganzhi(d)
    dg, dz = day_ganzhi(d)
    hg, hz = hour_ganzhi(9, dg)  # 辰时(9点)代表当日

    wd = ["一","二","三","四","五","六","日"][d.weekday()]

    # 五行
    wuxing_scores = calc_wuxing(d)

    # 神煞
    chong_zod, sha_dir = get_chong_zodiac(dz)
    ji_shi = get_ji_shi(dz)
    gui_ren_zhi = get_tianyi_gui_ren(dg)
    from ganzhi import get_zodiac
    gui_ren_zodiac = [get_zodiac(z) for z in gui_ren_zhi]

    # 宜忌 + 彭祖百忌
    yi_ji = get_yi_ji(dg, dz)
    pengzu = get_pengzu_bai_ji(dg, dz)

    # 节气
    jieqi_name = get_jieqi(d)
    jieqi_detail = get_jieqi_detail(jieqi_name) if jieqi_name else None
    next_jieqi = get_next_jieqi(d)

    # 用户
    user_blocks = []
    for u in users:
        advice = generate_advice(u, d)
        colors = generate_colors(wuxing_scores)
        alert = check_annual_alert(d)
        lifestyle = generate_lifestyle(u.get("day_master", "丁"), dz, wuxing_scores, u.get("zodiac", ""))
        user_blocks.append({
            "name": u["name"],
            "advice": advice,
            "colors": colors,
            "alert": alert,
            "lifestyle": lifestyle,
        })

    report = {
        "date": d,
        "today": d,
        "weekday": f"周{wd}" if wd != "日" else "周日",
        "year_ganzhi": f"{yg}{yz}",
        "month_ganzhi": f"{mg}{mz}",
        "day_ganzhi": f"{dg}{dz}",
        "hour_ganzhi": f"{hg}{hz}",
        "nayin_year": get_nayin(yg, yz),
        "nayin_month": get_nayin(mg, mz),
        "nayin_day": get_nayin(dg, dz),
        "nayin_hour": get_nayin(hg, hz),
        "wuxing": wuxing_scores,
        "chong_zodiac": chong_zod,
        "sha_direction": sha_dir,
        "ji_shi": ji_shi,
        "gui_ren": gui_ren_zhi,
        "gui_ren_zodiac": gui_ren_zodiac,
        "yi": yi_ji["yi"],
        "ji": yi_ji["ji"],
        "pengzu": pengzu,
        "jieqi_detail": jieqi_detail,
        "jieqi_name": jieqi_name,
        "next_jieqi": next_jieqi,
        "users": user_blocks,
    }

    # -- 周报（仅周日）--
    weekly = build_weekly_section(d, users)
    if weekly:
        report["weekly"] = weekly

    # -- 月报（仅节气换月日）--
    monthly = build_monthly_section(d, users)
    if monthly:
        report["monthly"] = monthly

    return report


# -- 邮件发送 -------------------------------------------
def send_email(recipient: str, subject: str, html_body: str, plain_body: str) -> bool:
    """发送 HTML + 纯文本双格式邮件。"""
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, recipient]):
        print(f"[DRY RUN] To: {recipient}\n{plain_body[:200]}...")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT, timeout=15) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(EMAIL_SENDER, EMAIL_PASSWORD)
            s.send_message(msg)
        print(f"✅ 已发送 -> {recipient}")
        return True
    except Exception as e:
        print(f"❌ 发送失败 -> {recipient}: {e}")
        return False
