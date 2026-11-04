"""Dane demonstracyjne (losowe, oznaczone w dashboardzie jako DEMO)."""
from __future__ import annotations

import random
from datetime import date, timedelta

CATALOG = {
    "Demo Shop A": [("Laptop UltraBook 14", 3299), ("Słuchawki bezprzewodowe NC-700", 899),
                    ("Smartfon Nova X 128 GB", 1799), ("Monitor 27 QHD", 1199)],
    "Demo Shop B": [("Klawiatura mechaniczna K8", 349), ("Mysz ergonomiczna ProGrip", 229),
                    ("Dysk SSD 1 TB NVMe", 389), ("Router Wi-Fi 6 AX3000", 429)],
    "Demo Shop C": [("Kamera internetowa 4K", 319), ("Powerbank 20000 mAh", 159),
                    ("Ekspres do kawy CaféPro", 1499), ("Odkurzacz bezprzewodowy V9", 1299)],
}


def make_demo_db(days: int = 45, seed: int = 7) -> dict:
    rnd, today = random.Random(seed), date.today()
    db = {"products": {}, "updated": today.isoformat(), "demo": True}
    n = 0
    for shop, items in CATALOG.items():
        for name, base in items:
            price, hist = float(base), []
            for d in range(days, -1, -1):
                price = max(base * 0.6, price * (1 + rnd.uniform(-0.025, 0.025)))
                if rnd.random() < 0.04:
                    price *= rnd.uniform(0.85, 0.95)
                hist.append([(today - timedelta(d)).isoformat(), round(price, 2)])
            if n % 3 == 0:      # czesc produktow tanieje "dzisiaj"
                hist[-1][1] = round(hist[-2][1] * rnd.uniform(0.84, 0.93), 2)
            elif n % 3 == 1:    # czesc drozeje
                hist[-1][1] = round(hist[-2][1] * rnd.uniform(1.01, 1.05), 2)
            db["products"][f"demo{n:02d}"] = {"title": name, "source": shop, "currency": "zł",
                                              "url": "#", "history": hist}
            n += 1
    return db
