"""五行每日播报 — 主入口。

编排所有模块，生成报表，发送邮件，推送通知。
通过 GitHub Actions cron 触发: 每天 7:00 BJT (UTC 23:00)。
"""

import json, os, sys
from datetime import date, datetime, timezone, timedelta

from email_report import build_report_data, render_html, render_plain, send_email
from week_report import build_weekly_section, append_daily_log
from month_report import build_monthly_section
from wuxing import calc_wuxing

BEIJING = timezone(timedelta(hours=8))


def load_users() -> list:
    """从 USERS 环境变量加载用户列表。"""
    raw = os.getenv("USERS") or "[]"
    try:
        users = json.loads(raw)
        if not isinstance(users, list):
            print("⚠️ USERS 格式错误，应为 JSON 数组")
            return []
        return users
    except json.JSONDecodeError as e:
        print(f"⚠️ USERS JSON 解析失败: {e}")
        return []


def main():
    today = date.today()
    beijing_now = datetime.now(BEIJING)
    print(f"🎋 五行每日播报 — {today} {beijing_now.strftime('%H:%M')} BJT")

    # 加载用户
    users = load_users()
    if not users:
        print("❌ 没有配置用户。请在 GitHub Secrets 中设置 USERS 环境变量。")
        sys.exit(1)
    print(f"  用户: {len(users)} 人")

    # 构建报表
    print("  生成报表...")
    report = build_report_data(today, users)

    # 追加周报
    weekly = build_weekly_section(today)
    if weekly:
        report["weekly"] = weekly
        print("  📊 周报已附加")

    # 追加月报
    monthly = build_monthly_section(today, users)
    if monthly:
        report["monthly"] = monthly
        print("  📆 月报已附加")

    # 生成邮件内容
    html = render_html(report)
    plain = render_plain(report)

    # 发送邮件（每人独立）
    subj = f"🎋 {today.strftime('%Y年%m月%d日')} 五行日报"
    if report.get("jieqi_name"):
        subj = f"🌾 {report['jieqi_name']} | {subj}"

    print("  发送邮件...")
    for user in users:
        email = user.get("email", "")
        if email:
            send_email(email, subj, html, plain)
        else:
            print(f"  ⚠️ {user['name']} 没有配置 email，跳过")

    # 推送通知
    try:
        from channels import push_all
        report["_plain_text"] = plain
        push_all(report)
    except ImportError:
        pass

    # 追加今日日志（供周报使用）
    wuxing_scores = calc_wuxing(today)
    append_daily_log(today, wuxing_scores)

    print("✅ 完成")


if __name__ == "__main__":
    main()
