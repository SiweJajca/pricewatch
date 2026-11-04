"""CLI: python -m pricewatch run | dashboard | demo"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import build_view, load_config, load_db, save_db, scrape_all, update_db
from .dashboard import render
from .demo import make_demo_db
from .notify import notify


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pricewatch", description="Monitoring cen w publicznych sklepach")
    ap.add_argument("command", choices=["run", "dashboard", "demo"],
                    help="run = pobierz ceny + dashboard + alerty; dashboard = przebuduj z historii; demo = dane pokazowe")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--no-notify", action="store_true", help="nie wysylaj powiadomien")
    a = ap.parse_args(argv)

    cfg = load_config(a.config)
    st = cfg["settings"]
    lang, thr = st.get("language", "pl"), float(st.get("drop_alert_percent", 5))
    data_file, out = Path(st.get("data_file", "data/history.json")), Path(st.get("output_dir", "docs"))
    out.mkdir(parents=True, exist_ok=True)

    if a.command == "demo":
        (out / "demo.html").write_text(render(build_view(make_demo_db(), thr), lang), "utf-8")
        print(f"Zapisano {out / 'demo.html'}")
        return 0

    db = load_db(data_file)
    if a.command == "run":
        items, errors = scrape_all(cfg)
        for name, err in errors.items():
            print(f"[blad] {name}: {err}", file=sys.stderr)
        if not items:
            print("Nie pobrano zadnych cen.", file=sys.stderr)
            return 1                     # czerwony status w GitHub Actions = mail od GitHuba
        update_db(db, items)
        save_db(db, data_file)
        print(f"Pobrano {len(items)} produktow z {len(cfg['sources']) - len(errors)} sklepow.")

    view = build_view(db, thr)
    (out / "index.html").write_text(render(view, lang), "utf-8")
    print(f"Dashboard: {out / 'index.html'} ({len(view['items'])} produktow, {len(view['drops'])} obnizek)")
    if a.command == "run" and not a.no_notify:
        sent = notify(view["drops"], lang)
        print("Powiadomienia:", ", ".join(sent) if sent else "brak (brak obnizek lub nieskonfigurowane kanaly)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
