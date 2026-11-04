# PriceWatch

Bot w Pythonie, który **codziennie sam** pobiera ceny z publicznych sklepów, zapisuje historię, wykrywa obniżki, wysyła alert (e-mail / Telegram) i publikuje przejrzysty dashboard z wykresami cen.

Działa w całości na darmowym GitHubie: bez serwera, bez bazy danych, bez Twojej opieki.

**Podgląd na żywo (dane demo):** `https://TWOJ-LOGIN.github.io/pricewatch/demo.html`

## Jak to działa

```
GitHub Actions (cron, raz dziennie)
   └─ python -m pricewatch run
        ├─ pobiera ceny ze sklepów z config.yaml
        ├─ dopisuje je do data/history.json
        ├─ buduje docs/index.html (dashboard)
        └─ wysyła alert, gdy cena spadła o co najmniej X%
   └─ commit zmian do repo  →  GitHub Pages publikuje dashboard
```

Błąd jednego sklepu nie zatrzymuje reszty. Jeśli nie uda się pobrać nic, przebieg kończy się błędem, a GitHub wyśle Ci o tym e-mail.

## Uruchomienie lokalne (2 minuty)

```bash
pip install -r requirements.txt
python -m pricewatch demo      # dashboard z danymi pokazowymi -> docs/demo.html
python -m pricewatch run       # prawdziwe ceny -> docs/index.html
python -m unittest discover -s tests
```

## Wdrożenie na GitHub (bez kosztów)

1. Utwórz **publiczne** repozytorium `pricewatch` i wgraj do niego całą zawartość tego folderu (razem z `.github/`).
2. **Settings → Actions → General → Workflow permissions** → *Read and write permissions* → Save.
3. Zakładka **Actions** → *PriceWatch* → **Run workflow** (pierwszy przebieg ręcznie). Po minucie w repo pojawią się `data/history.json` i `docs/index.html`.
4. **Settings → Pages** → Source: *Deploy from a branch* → branch `main`, folder `/docs` → Save.
5. Po chwili dashboard jest pod `https://TWOJ-LOGIN.github.io/pricewatch/`.

Od teraz bot odpala się codziennie o ok. 6:00 UTC. Publiczne repozytoria mają darmowe minuty Actions bez limitu, a każdy przebieg zajmuje ok. minutę. Ponieważ bot codziennie zapisuje nową datę w historii, repozytorium ma stałą aktywność i harmonogram nie wygasa z powodu bezczynności.

> Wykresy zaczynają się układać po kilku dniach działania. Do pokazania od razu służy `demo.html`.

## Alerty (opcjonalnie)

**E-mail:** w *Settings → Secrets and variables → Actions → Secrets* dodaj `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `MAIL_TO`. Dla Gmaila: `smtp.gmail.com`, port `587`, a jako hasło użyj *hasła aplikacji* (wymaga włączonej weryfikacji dwuetapowej).

**Telegram:** utwórz bota u `@BotFather`, dodaj sekrety `TELEGRAM_TOKEN` i `TELEGRAM_CHAT_ID`.

**Link do dashboardu w alercie:** w zakładce *Variables* dodaj `DASHBOARD_URL`.

Kanały bez konfiguracji są po prostu pomijane.

## Dodawanie sklepu bez programowania

Dopisz blok w `config.yaml`. Selektory CSS znajdziesz, klikając element prawym przyciskiem → *Zbadaj*.

```yaml
- name: Mój sklep
  url: https://sklep.pl/kategoria/laptopy
  item: div.product-card        # jeden produkt na liście
  title: h2.name                # tekst nazwy (lub  a.title@title  = atrybut)
  price: span.price
  link: a.name@href
  next: a.pagination-next@href  # opcjonalnie: następna strona
```

Jeśli selektory są błędne, w logu przebiegu zobaczysz konkretny komunikat, a pozostałe sklepy nadal się zaktualizują.

## Uwagi prawne i etyka

- Skrypt używa grzecznego tempa (`delay_seconds`) i podpisuje się własnym User-Agentem. Wpisz tam swój kontakt.
- Domyślne źródła (`books.toscrape.com`, `webscraper.io/test-sites`) to piaskownice stworzone do nauki scrapingu.
- Przed dodaniem prawdziwego sklepu sprawdź jego regulamin i `robots.txt`, a najlepiej użyj oficjalnego API lub feedu. Dla klienta zbieraj tylko dane publiczne.

## Scenariusz filmu demo (60–90 s)

1. Otwórz `demo.html`: pokaż karty z żółtym paskiem obniżki, filtr sklepów i wyszukiwarkę.
2. Rozwiń jedną kartę: wykres historii i najniższa cena.
3. Pokaż `config.yaml`: „nowy sklep = kilka linijek”.
4. Pokaż zakładkę *Actions* z zielonymi, codziennymi przebiegami.
5. Pokaż przykładowy alert w mailu lub na Telegramie.
6. Zakończ zdaniem: „Działa sam, kosztuje 0 zł miesięcznie, a Ty dostajesz tylko informację, że coś stanieje.”

## Struktura

```
pricewatch/core.py       pobieranie, historia, wykrywanie obniżek
pricewatch/notify.py     e-mail i Telegram
pricewatch/dashboard.py  generator dashboardu (jeden plik HTML)
pricewatch/demo.py       dane pokazowe
tests/                   testy jednostkowe
.github/workflows/       harmonogram dzienny
```
