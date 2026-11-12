"""Browser tests pinning the 4th UX review (r10/r11/r12, 2026-11-13). 390x844 touch phone."""
import re
from tests.test_ui import UiTest as Base


class V3e(Base):
    def short_page(self, hash_=""):
        # a 390x640 phone: the numbers screen is taller than the window, so scroll position is observable
        ctx = self.br.new_context(viewport={"width": 390, "height": 640}, has_touch=True, is_mobile=True)
        p = ctx.new_page(); p.goto(self.url + hash_); p.wait_for_selector("#go"); p.wait_for_timeout(150); return p

    def verdict(self, p):
        p.wait_for_selector(".verdict"); return p.locator(".verdict").inner_text()

    def ratio(self, p):
        return float(re.search(r"([\d.]+)×", self.verdict(p)).group(1))

    # 1 Hybrid source note: part of the existing rule only as a required fact, never a number in the ratio
    def test_dry_basis_is_a_source_note_not_a_number(self):
        p = self.page("#/?method=liquid")
        lab = p.locator("label", has=p.locator("#f-dry_basis")).inner_text()
        self.assertIn("Source", lab); self.assertIn("does not change the ratio", lab)
        self.assertNotRegex(p.input_value("#f-dry_basis"), r"\d+\s*%")

    def test_changing_dry_basis_never_changes_ratio_and_blank_holds(self):
        a = self.page("#/result?method=liquid&dry_basis=Maker+sheet+A"); ra = self.ratio(a)
        b = self.page("#/result?method=liquid&dry_basis=Other+source"); rb = self.ratio(b)
        self.assertEqual(ra, rb)
        self.assertIn("Other source", b.inner_text(".why"))
        c = self.page("#/result?method=liquid&dry_basis="); self.assertIn("Hold", self.verdict(c))

    # 2 the example line never breaks between the number and its unit, with or without Reset
    def test_example_line_one_row(self):
        p = self.page()
        self.assertEqual(p.locator("#example span").evaluate("e=>e.getClientRects().length"), 1)
        h = p.locator("#example span").evaluate("e=>e.getBoundingClientRect().height")
        self.assertLess(h, 24, h)
        p.fill("#f-net_supply_m3", "1000"); p.tap("#go"); self.verdict(p); p.tap("#change"); p.wait_for_selector("#go")
        self.assertLess(p.locator("#example span").evaluate("e=>e.getBoundingClientRect().height"), 24)

    # 3 a chip changes the method in place: same scroll position, no page-wide fade
    def test_chip_keeps_scroll_position(self):
        p = self.short_page(); p.evaluate("window.scrollTo(0, 200)")
        y0 = p.evaluate("window.scrollY"); self.assertGreater(y0, 100)
        p.locator("[role=radio]", has_text="Hybrid").tap(); p.wait_for_selector("#f-dry_basis")
        self.assertEqual(p.evaluate("window.scrollY"), y0)
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('.view')).animationName"), "none")

    # 4 Back and Change numbers return to where the person left the numbers
    def test_return_restores_scroll(self):
        p = self.short_page("#/?method=hydrothermal"); p.evaluate("window.scrollTo(0, 120)"); y0 = p.evaluate("window.scrollY")
        self.assertGreater(y0, 60)
        p.tap("#go"); self.verdict(p); p.tap("#change"); p.wait_for_selector("#go"); p.wait_for_timeout(300)
        self.assertEqual(p.evaluate("window.scrollY"), y0)
        p.tap("#go"); self.verdict(p); p.go_back(); p.wait_for_selector("#go"); p.wait_for_timeout(300)
        self.assertEqual(p.evaluate("window.scrollY"), y0)

    # 5 shared findings: blank placeholder, hint hidden under its own error, one rule line, graphic on Check
    def test_blank_placeholder_and_error_hides_hint(self):
        p = self.page()
        self.assertEqual(p.get_attribute("#f-net_supply_m3", "placeholder"), "Not measured yet")
        p.fill("#f-cycles", "1"); p.tap("#go"); p.wait_for_selector(".ferr")
        self.assertEqual(p.locator("label", has=p.locator("#f-cycles")).locator(".hint").count(), 0)

    def test_rule_is_its_own_short_line(self):
        p = self.page("#/result?method=evaporative"); self.verdict(p)
        self.assertNotIn("Rule:", p.locator(".why li").nth(1).inner_text())
        self.assertIn("Rule:", p.locator(".rule").inner_text())

    def test_check_screen_has_one_graphic(self):
        p = self.page()
        self.assertEqual(p.locator("#app img.gfx").count(), 1)
        self.assertLessEqual(p.locator("#app img.gfx").bounding_box()["height"], 48)
