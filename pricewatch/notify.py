"""Powiadomienia: e-mail (SMTP) i Telegram. Kanaly bez konfiguracji sa pomijane."""
from __future__ import annotations

import html
import json
import os
import smtplib
import urllib.request
from email.message import EmailMessage

TEXTS = {
    "pl": {"subject": "PriceWatch: {n} obniżek cen", "intro": "Wykryte obniżki cen:",
           "now": "teraz", "was": "było", "open": "Zobacz dashboard"},
    "en": {"subject": "PriceWatch: {n} price drops", "intro": "Price drops detected:",
           "now": "now", "was": "was", "open": "Open dashboard"},
}


def _money(v: float, cur: str) -> str:
    return f"{v:,.2f} {cur}".replace(",", " ").strip()


def build_message(drops: list[dict], lang: str = "pl") -> tuple[str, str, str]:
    t = TEXTS.get(lang, TEXTS["pl"])
    url = os.getenv("DASHBOARD_URL", "")
    lines, rows = [], []
    for d in drops[:20]:
        now, was = _money(d["price"], d["currency"]), _money(d["prev"], d["currency"])
        lines.append(f"{d['change']:+.1f}%  {d['title']} ({d['source']}): {t['was']} {was}, {t['now']} {now}\n{d['url']}")
        rows.append(
            f"<tr><td style='padding:6px 12px 6px 0'><a href='{html.escape(d['url'])}'>{html.escape(d['title'])}</a>"
            f"<br><small>{html.escape(d['source'])}</small></td>"
            f"<td style='padding:6px 0;white-space:nowrap'><s>{was}</s> → <b>{now}</b> "
            f"<span style='color:#0a8754'>{d['change']:+.1f}%</span></td></tr>")
    text = t["intro"] + "\n\n" + "\n\n".join(lines) + (f"\n\n{t['open']}: {url}" if url else "")
    link = f"<p><a href='{html.escape(url)}'>{t['open']}</a></p>" if url else ""
    body = f"<p>{t['intro']}</p><table style='font-family:sans-serif;font-size:14px'>{''.join(rows)}</table>{link}"
    return t["subject"].format(n=len(drops)), text, body


def send_email(subject: str, text: str, body_html: str) -> bool:
    host, user, pwd, to = (os.getenv(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "MAIL_TO"))
    if not all((host, user, pwd, to)):
        return False
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, os.getenv("MAIL_FROM", user), to
    msg.set_content(text)
    msg.add_alternative(body_html, subtype="html")
    port = int(os.getenv("SMTP_PORT", "587"))
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=30) as s:
            s.login(user, pwd); s.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls(); s.login(user, pwd); s.send_message(msg)
    return True


def send_telegram(text: str) -> bool:
    token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (token and chat):
        return False
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True}).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).read()
    return True


def notify(drops: list[dict], lang: str = "pl") -> list[str]:
    """Zwraca liste kanalow, ktorymi wyslano powiadomienie."""
    if not drops:
        return []
    subject, text, body = build_message(drops, lang)
    sent = []
    for name, fn in (("email", lambda: send_email(subject, text, body)),
                     ("telegram", lambda: send_telegram(f"{subject}\n\n{text}"))):
        try:
            if fn():
                sent.append(name)
        except Exception as exc:  # noqa: BLE001
            print(f"[notify] {name} nie zadzialal: {exc}")
    return sent
