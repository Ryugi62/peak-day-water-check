"""Browser tests pinning the 3rd UX review (r7/r8/r9, 2026-11-13). 390x844 touch phone."""
import re, unittest
from tests.test_ui import UiTest as Base


class V3d(Base):
    def verdict(self, p):
        p.wait_for_selector(".verdict"); return p.locator(".verdict").inner_text()

    def ratio(self, p):
        return float(re.search(r"([\d.]+)×", self.verdict(p)).group(1))

    # 1 example values per method read as a believable site, with a one-line reason
    def test_river_example_is_not_a_broken_looking_ratio(self):
        p = self.page("#/result?method=hydrothermal")
        r = self.ratio(p)
        self.assertTrue(1.0 <= r < 3.0, r)
        self.assertRegex(p.inner_text(".why"), r"Why (Fit|Conditional|Not fit)")

    def test_hybrid_differs_from_evaporative_and_explains_dry_basis(self):
        pe = self.page("#/result?method=evaporative"); re_ = self.ratio(pe)
        ph = self.page("#/result?method=liquid"); rh = self.ratio(ph)
        self.assertNotEqual(re_, rh)
        self.assertIn("dry", ph.inner_text(".why").lower())

    def test_why_line_names_ratio_for_every_status(self):
        for q, word in (("net_supply_m3=5000&peak_day_m3=2000", "Fit"), ("net_supply_m3=3630", "Conditional"), ("net_supply_m3=1000", "Not fit")):
            p = self.page("#/result?method=evaporative&" + q)
            self.assertIn("Why " + word, p.inner_text(".why"))

    def test_edited_example_still_shows_in_hybrid_switch(self):
        p = self.page(); p.locator("[role=radio]", has_text="Hybrid").tap()
        self.assertEqual(p.input_value("#f-peak_day_m3"), "1566")
        p.locator("[role=radio]", has_text="Evaporative").tap()
        self.assertEqual(p.input_value("#f-peak_day_m3"), "2610")

    # 2 bottom primary action takes the result away; Change numbers is secondary
    def test_primary_cta_copies_result_link(self):
        ctx = self.br.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True,
                                  permissions=["clipboard-read", "clipboard-write"])
        p = ctx.new_page(); p.goto(self.url + "#/result?method=evaporative"); self.verdict(p)
        self.assertEqual(p.locator(".cta").inner_text(), "Copy this result link")
        self.assertEqual(p.locator("#change").inner_text(), "Change numbers")
        self.assertFalse(p.locator("#change").evaluate("e=>e.classList.contains('cta')"))
        p.tap("#copy")
        p.wait_for_function("document.getElementById('copy').innerText.indexOf('copied')>=0")
        self.assertEqual(p.evaluate("navigator.clipboard.readText()"), p.url)

    def test_change_numbers_still_returns(self):
        p = self.page("#/result?method=evaporative"); self.verdict(p)
        p.tap("#change"); p.wait_for_selector("#go")

    # 3 coming back lands at the top with the title fully visible
    def test_return_scrolls_to_top_with_title_visible(self):
        p = self._fresh()
        p.fill("#f-net_supply_m3", "9000"); p.tap("#go"); self.verdict(p)
        p.evaluate("window.scrollTo(0, 300)")
        p.tap("#change"); p.wait_for_selector("#go"); p.wait_for_timeout(400)
        self.assertEqual(p.evaluate("window.scrollY"), 0)
        self.assertGreaterEqual(p.locator("h1").bounding_box()["y"], 56)
        p.tap("#go"); self.verdict(p); p.evaluate("window.scrollTo(0, 300)")
        p.go_back(); p.wait_for_selector("#go"); p.wait_for_timeout(400)
        self.assertEqual(p.evaluate("window.scrollY"), 0)
        self.assertGreaterEqual(p.locator("h1").bounding_box()["y"], 56)

    def _fresh(self):
        ctx = self.br.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
        p = ctx.new_page(); p.goto("about:blank"); p.goto(self.url); p.wait_for_selector("#go"); return p

    # 4 the Reset slot is reserved: nothing moves when it appears
    def test_reset_slot_reserved_no_layout_shift(self):
        p = self.page()
        ys0 = [p.locator(s).bounding_box()["y"] for s in (".chips", "#f-net_supply_m3")]
        self.assertEqual(p.locator("#reset").evaluate("e=>getComputedStyle(e).visibility"), "hidden")
        p.fill("#f-net_supply_m3", "1000"); p.tap("#go"); self.verdict(p); p.tap("#change"); p.wait_for_selector("#go")
        self.assertEqual(p.locator("#reset").evaluate("e=>getComputedStyle(e).visibility"), "visible")
        ys1 = [p.locator(s).bounding_box()["y"] for s in (".chips", "#f-net_supply_m3")]
        self.assertEqual(ys0, ys1)

    # 5 Direct air result: no "Next step" with nothing under it
    def test_direct_air_result_copy_is_consistent(self):
        p = self.page("#/result?method=direct_air"); self.verdict(p)
        t = p.inner_text("#app")
        self.assertNotIn("Nothing to measure", t); self.assertNotIn("Next step", t)
        self.assertNotIn("evaporative air cooling", t)
        self.assertIn("Pick Evaporative, Hybrid, or River or dam", t)
        self.assertEqual(p.locator(".cta").inner_text(), "Pick another method")

    # 6 text never shows through the fixed bottom bar
    def test_bottom_bar_is_opaque(self):
        for h in ("", "#/result?method=evaporative"):
            p = self.page(h); p.wait_for_selector(".cta-wrap")
            st = p.locator(".cta-wrap").evaluate("e=>{const s=getComputedStyle(e);return [s.backgroundColor,s.backgroundImage]}")
            self.assertEqual(st[0], "rgb(255, 255, 255)"); self.assertEqual(st[1], "none")

    def test_content_clears_bottom_bar(self):
        p = self.page("#/result?method=evaporative"); self.verdict(p)
        p.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        last = p.locator(".src").bounding_box(); bar = p.locator(".cta-wrap").bounding_box()
        self.assertLessEqual(last["y"] + last["height"], bar["y"])


if __name__ == "__main__":
    unittest.main()
