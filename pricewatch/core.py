"""Pobieranie cen, zapis historii i wykrywanie obnizek."""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml
from bs4 import BeautifulSoup

CURRENCY_RE = re.compile(r"[£$€]|zł|PLN|USD|EUR|GBP", re.I)


def load_config(path: str = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg.setdefault("settings", {})
    cfg.setdefault("sources", [])
    return cfg


def parse_price(text: str | None) -> float | None:
    """'£51.77', '$1,299.00', '1 299,00 zł' -> float."""
    m = re.search(r"\d[\d\s.,]*", text or "")
    if not m:
        return None
    s = re.sub(r"\s", "", m.group()).rstrip(".,")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):          # 1.299,00
            s = s.replace(".", "").replace(",", ".")
        else:                                     # 1,299.00
            s = s.replace(",", "")
    elif "," in s:
        head, _, tail = s.rpartition(",")
        s = s.replace(",", "") if len(tail) == 3 else f"{head.replace(',', '')}.{tail}"
    try:
        return float(s)
    except ValueError:
        return None


def pick(node, spec: str) -> str | None:
    """'selektor' -> tekst, 'selektor@attr' -> atrybut."""
    sel, _, attr = spec.partition("@")
    target = node.select_one(sel) if sel else node
    if target is None:
        return None
    return target.get(attr) if attr else target.get_text(" ", strip=True)


def parse_page(soup: BeautifulSoup, src: dict, base_url: str) -> list[dict]:
    out = []
    for el in soup.select(src["item"]):
        title, raw = pick(el, src["title"]), pick(el, src["price"])
        price = parse_price(raw)
        if not title or price is None:
            continue
        link = pick(el, src["link"]) if src.get("link") else None
        cur = CURRENCY_RE.search(raw)
        out.append({
            "id": hashlib.sha1(f"{src['name']}|{title}".encode()).hexdigest()[:10],
            "source": src["name"],
            "title": title.strip(),
            "price": price,
            "currency": cur.group() if cur else "",
            "url": urljoin(base_url, link) if link else base_url,
        })
    return out


def scrape_source(src: dict, settings: dict, session: requests.Session) -> list[dict]:
    url, items, pages = src["url"], [], 0
    while url and pages < settings.get("max_pages", 3):
        r = session.get(url, timeout=20)
        r.raise_for_status()
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        items += parse_page(soup, src, r.url)
        nxt = pick(soup, src["next"]) if src.get("next") else None
        url = urljoin(r.url, nxt) if nxt else None
        pages += 1
        if url:
            time.sleep(settings.get("delay_seconds", 1))
    return items


def scrape_all(cfg: dict) -> tuple[list[dict], dict[str, str]]:
    """Blad jednego sklepu nie przerywa calego przebiegu."""
    s = cfg["settings"]
    session = requests.Session()
    session.headers["User-Agent"] = s.get("user_agent", "PriceWatch/1.0")
    items, errors = [], {}
    for src in cfg["sources"]:
        if src.get("enabled", True) is False:
            continue
        try:
            got = scrape_source(src, s, session)
            if not got:
                raise RuntimeError("0 produktow: sprawdz selektory w config.yaml")
            items += got
        except Exception as exc:  # noqa: BLE001
            errors[src["name"]] = str(exc)
    return items, errors


# ---------- historia ----------

def load_db(path: str | Path) -> dict:
    p = Path(path)
    return json.loads(p.read_text("utf-8")) if p.exists() else {"products": {}}


def save_db(db: dict, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(db, ensure_ascii=False, indent=1), "utf-8")


def update_db(db: dict, items: list[dict], today: str | None = None) -> dict:
    today = today or date.today().isoformat()
    for it in items:
        p = db["products"].setdefault(it["id"], {"source": it["source"], "history": []})
        p.update(title=it["title"], url=it["url"], currency=it["currency"], source=it["source"])
        h = p["history"]
        if h and h[-1][0] == today:
            h[-1][1] = it["price"]
        else:
            h.append([today, it["price"]])
        del h[:-365]
    db["updated"] = today
    return db


def build_view(db: dict, threshold: float = 5.0, stale_days: int = 14) -> dict:
    """Dane gotowe dla dashboardu i powiadomien."""
    updated = db.get("updated") or date.today().isoformat()
    items = []
    for pid, p in db["products"].items():
        h = p["history"]
        if not h:
            continue
        age = (date.fromisoformat(updated) - date.fromisoformat(h[-1][0])).days
        if age > stale_days:
            continue
        prices = [x[1] for x in h]
        price, prev = prices[-1], (prices[-2] if len(prices) > 1 else None)
        change = round((price - prev) / prev * 100, 1) if prev else None
        fresh = h[-1][0] == updated
        items.append({
            "id": pid, "title": p["title"], "source": p["source"], "url": p["url"],
            "currency": p["currency"], "price": price, "prev": prev, "change": change,
            "min": min(prices), "max": max(prices), "first": prices[0],
            "is_low": fresh and len(prices) >= 3 and price <= min(prices) and price < (prev or price),
            "drop": fresh and change is not None and change <= -threshold,
            "history": h[-60:],
        })
    return {"updated": updated, "demo": bool(db.get("demo")), "items": items,
            "drops": sorted([i for i in items if i["drop"]], key=lambda i: i["change"])}
