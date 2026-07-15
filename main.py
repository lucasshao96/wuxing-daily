"""五行每日播报 — 主入口。

编排所有模块，生成报表，发送邮件，推送通知。
通过 GitHub Actions cron 触发: 每天 7:00 BJT (UTC 23:00)。
"""

import json, os, sys
from datetime import date, datetime, timezone, timedelta

# Windows GBK 终端兼容: GitHub Actions (Ubuntu) 不受影响
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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

    # 生成邮件内容 每人独立邮件 — 只含自己的个性化卡片
    print("  发送邮件...")
    for user in users:
        email = user.get("email", "")
        if not email:
            print(f"  ⚠️ {user['name']} 没有配置 email，跳过")
            continue

        # 构建单用户报表
        user_report = build_report_data(today, [user])
        if weekly:
            user_report["weekly"] = weekly
        if monthly:
            user_report["monthly"] = monthly

        user_html = render_html(user_report)
        user_plain = render_plain(user_report)

        subj = f"🎋 {today.strftime('%Y年%m月%d日')} 五行日报"
        if report.get("jieqi_name"):
            subj = f"🌾 {report['jieqi_name']} | {subj}"

        send_email(email, subj, user_html, user_plain)

    # 推送通知
    try:
        from channels import push_all
        report["_plain_text"] = plain
        push_all(report)
    except ImportError:
        pass

    # 追加今日日志（供周报使用）— 必须 commit + push 才能在每日间持久化
    wuxing_scores = calc_wuxing(today)
    append_daily_log(today, wuxing_scores)
    _commit_and_push_log()

    print("✅ 完成")


def _commit_and_push_log() -> None:
    """在 GitHub Actions 中提交并推送 week_log.json，保证跨天持久化。"""
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
    if not token:
        print("  ⚠️ 未找到 GH_TOKEN，跳过周报日志持久化")
        return

    import subprocess

    remote = f"https://x-access-token:{token}@github.com/{os.getenv('GITHUB_REPOSITORY', 'lucasshao96/wuxing-daily')}.git"
    log_path = "data/week_log.json"

    try:
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True, capture_output=True)
        subprocess.run(["git", "add", log_path], check=True, capture_output=True)
        # 如果有变更才提交
        r = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if r.returncode == 0:
            print("  📋 week_log 无变更，跳过提交")
            return
        subprocess.run(["git", "commit", "-m", "data: update week_log"], check=True, capture_output=True)
        subprocess.run(["git", "push", remote, "master"], check=True, capture_output=True)
        print("  📋 week_log 已提交并推送")
    except Exception as e:
        print(f"  ⚠️ week_log 持久化失败: {e}")


if __name__ == "__main__":
    main()
