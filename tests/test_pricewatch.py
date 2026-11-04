import json
import re
import unittest

from bs4 import BeautifulSoup

from pricewatch.core import build_view, parse_page, parse_price, pick, update_db
from pricewatch.dashboard import render
from pricewatch.demo import make_demo_db
from pricewatch.notify import build_message

BOOKS = """
<ol><li><article class="product_pod">
  <h3><a href="a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in ...</a></h3>
  <div class="product_price"><p class="price_color">Â£51.77</p></div></article></li>
<li><article class="product_pod">
  <h3><a href="tipping-the-velvet_999/index.html" title="Tipping the Velvet">Tipping ...</a></h3>
  <div class="product_price"><p class="price_color">£53.74</p></div></article></li></ol>
<ul class="pager"><li class="next"><a href="page-2.html">next</a></li></ul>
"""
SRC = {"name": "Books", "item": "article.product_pod", "title": "h3 a@title",
       "price": "p.price_color", "link": "h3 a@href", "next": "li.next a@href"}


class PriceTests(unittest.TestCase):
    def test_parse_price_formats(self):
        for text, want in [("£51.77", 51.77), ("$1,299.00", 1299.0), ("1 299,00 zł", 1299.0),
                           ("1.299,50 €", 1299.5), ("1,299", 1299.0), ("249,99 zł", 249.99), ("brak", None)]:
            self.assertEqual(parse_price(text), want, text)

    def test_parse_page_and_next(self):
        soup = BeautifulSoup(BOOKS, "html.parser")
        items = parse_page(soup, SRC, "https://books.toscrape.com/catalogue/page-1.html")
        self.assertEqual([i["title"] for i in items], ["A Light in the Attic", "Tipping the Velvet"])
        self.assertEqual(items[0]["price"], 51.77)
        self.assertEqual(items[0]["currency"], "£")
        self.assertTrue(items[0]["url"].startswith("https://books.toscrape.com/catalogue/a-light"))
        self.assertEqual(pick(soup, SRC["next"]), "page-2.html")

    def test_drop_detection(self):
        item = {"id": "x1", "source": "S", "title": "T", "price": 100.0, "currency": "zł", "url": "#"}
        db = {"products": {}}
        for day, price in [("2026-01-01", 100.0), ("2026-01-02", 98.0), ("2026-01-03", 80.0)]:
            update_db(db, [{**item, "price": price}], today=day)
        view = build_view(db, threshold=5)
        self.assertEqual(len(view["drops"]), 1)
        self.assertEqual(view["drops"][0]["change"], -18.4)
        self.assertTrue(view["drops"][0]["is_low"])

    def test_same_day_overwrites(self):
        item = {"id": "x1", "source": "S", "title": "T", "price": 100.0, "currency": "", "url": "#"}
        db = update_db({"products": {}}, [item], today="2026-01-01")
        update_db(db, [{**item, "price": 90.0}], today="2026-01-01")
        self.assertEqual(db["products"]["x1"]["history"], [["2026-01-01", 90.0]])

    def test_demo_dashboard_renders_valid_data(self):
        html = render(build_view(make_demo_db()), "pl")
        data = json.loads(re.search(r"const D=(\{.*?\}), T=", html, re.S).group(1))
        self.assertTrue(data["demo"])
        self.assertEqual(len(data["items"]), 12)
        self.assertGreaterEqual(len(data["drops"]), 3)
        self.assertNotIn("__DATA__", html)

    def test_message(self):
        drops = build_view(make_demo_db())["drops"]
        subject, text, body = build_message(drops, "pl")
        self.assertIn("obniżek", subject)
        self.assertIn("<table", body)


if __name__ == "__main__":
    unittest.main()
