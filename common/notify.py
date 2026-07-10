"""Telegram alerts. No token configured -> prints to stdout instead (never crashes a job)."""
import json
import urllib.request

from common import config


def send(text: str) -> bool:
    token = config.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"[notify:stdout] {text}")
        return False
    try:
        body = json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": True}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:  # noqa: BLE001 - alerts must never take down a job
        print(f"[notify:error] {e}: {text}")
        return False
