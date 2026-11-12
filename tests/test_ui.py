"""Browser tests for index.html (390x844 phone). Each test pins one UX review finding (r1/r2, 2026-11-13)."""
import functools, http.server, os, threading, unittest
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class UiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
        h.log_message = lambda *a, **k: None
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = "http://127.0.0.1:%d/index.html" % cls.srv.server_address[1]
        cls.pw = sync_playwright().start()
        cls.br = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.br.close(); cls.pw.stop(); cls.srv.shutdown()

    def page(self, hash_=""):
        ctx = self.br.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
        p = ctx.new_page(); p.goto(self.url + hash_); return p

    # 1 promise is visible text on the first screen, not a placeholder
    def test_promise_line_visible_on_first_screen(self):
        p = self.page()
        el = p.locator("#promise")
        self.assertIn("instead of guessing", el.inner_text())
        box = el.bounding_box(); self.assertLess(box["y"] + box["height"], 844)

    # 2 status color sits on the verdict word; method pill is neutral
    def test_verdict_word_colored_method_neutral(self):
        colors = {}
        for status, q in (("Fit", "net_supply_m3=5000&peak_day_m3=2000&cycles=4"),
                          ("Conditional", "net_supply_m3=3630&peak_day_m3=2610&cycles=3"),
                          ("Not fit", "net_supply_m3=1000&peak_day_m3=2610&cycles=3"),
                          ("Hold", "cycles=3")):
            p = self.page("#/result?method=evaporative&" + q)
            w = p.locator(".verdict .vw")
            self.assertEqual(w.inner_text(), status)
            colors[status] = w.evaluate("e=>getComputedStyle(e).color")
            self.assertEqual(p.locator(".pill").evaluate("e=>getComputedStyle(e).backgroundColor"), "rgb(242, 244, 246)")
        self.assertEqual(len(set(colors.values())), 4, colors)

    # 3 method = chips (<=5), nothing clipped at 390
    def test_method_chips_no_clipping(self):
        p = self.page()
        chips = p.locator("[role=radio]")
        self.assertTrue(2 <= chips.count() <= 5)
        for i in range(chips.count()):
            b = chips.nth(i).bounding_box()
            self.assertGreaterEqual(b["x"], 0); self.assertLessEqual(b["x"] + b["width"], 390)
            self.assertTrue(chips.nth(i).evaluate("e=>e.scrollWidth<=e.clientWidth+1"))
        self.assertEqual(p.evaluate("document.documentElement.scrollWidth"), 390)
        p.locator("[role=radio]", has_text="River").tap()
        self.assertIn("Heat to reject", p.locator("#app").inner_text())

    # 4 browser back keeps typed values
    def test_browser_back_keeps_values(self):
        p = self.page()
        p.fill("#f-net_supply_m3", "1000")
        p.tap("#go")
        p.wait_for_selector(".verdict")
        p.go_back()
        p.wait_for_selector("#f-net_supply_m3")
        self.assertEqual(p.input_value("#f-net_supply_m3"), "1000")

    # field error attaches to the field and gets focus
    def test_error_on_field(self):
        p = self.page()
        p.fill("#f-cycles", "3x"); p.tap("#go")
        p.wait_for_selector("#f-cycles-err")
        self.assertIn("like 3", p.inner_text("#f-cycles-err"))
        self.assertEqual(p.evaluate("document.activeElement.id"), "f-cycles")

    # no custom shadow (design-system rule), units unified, no bare abbreviations
    def test_no_box_shadow_and_units(self):
        src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        self.assertNotIn("box-shadow", src)
        p = self.page("#/result?method=evaporative&cycles=3")
        t = p.locator("#app").inner_text()
        self.assertNotIn("m3/day", t); self.assertNotIn("TMS", t); self.assertNotIn("ASOS", t)

    def test_direct_air_cta(self):
        p = self.page("#/result?method=direct_air")
        self.assertEqual(p.locator("#change").inner_text(), "Pick another method")

    def test_single_h1_title(self):
        p = self.page()
        self.assertNotEqual(p.locator("h1").inner_text(), p.locator(".bar-title").inner_text())


if __name__ == "__main__":
    unittest.main()
