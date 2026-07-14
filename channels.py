"""推送渠道 — Server酱 + Telegram Bot。

可选功能。从 GitHub Secrets 读取配置，不配就不推，邮件始终发送。
"""

import os, requests

def push_serverchan(sckey: str, title: str, content: str) -> bool:
    """Server酱 (https://sct.ftqq.com/) 推送。"""
    try:
        r = requests.post(
            f"https://sctapi.ftqq.com/{sckey}.send",
            data={"title": title[:32], "desp": content[:500]},
            timeout=10,
        )
        if r.status_code == 200:
            print("  📲 Server酱 推送成功")
            return True
        print(f"  ⚠️ Server酱 推送失败: {r.status_code}")
        return False
    except Exception as e:
        print(f"  ⚠️ Server酱 推送异常: {e}")
        return False

def push_telegram(bot_token: str, chat_id: str, text: str) -> bool:
    """Telegram Bot 推送。"""
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text[:1000], "parse_mode": "HTML"},
            timeout=10,
        )
        if r.status_code == 200 and r.json().get("ok"):
            print("  📲 Telegram 推送成功")
            return True
        print(f"  ⚠️ Telegram 推送失败: {r.status_code}")
        return False
    except Exception as e:
        print(f"  ⚠️ Telegram 推送异常: {e}")
        return False

def push_all(report: dict) -> None:
    """读取所有已配置的推送渠道并广播。"""
    plain_text = report.get("_plain_text", "")

    # Server酱
    sckey = os.getenv("SERVERCHAN_SCKEY") or ""
    if sckey:
        title = f"🎋 {report.get('day_ganzhi','')} 五行日报"
        push_serverchan(sckey, title, plain_text)

    # Telegram
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or ""
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or ""
    if bot_token and chat_id:
        push_telegram(bot_token, chat_id, plain_text)
