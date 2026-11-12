"""Browser tests pinning the 5th UX review (r13/r14, 2026-11-13): 3D emoji graphic, Reset margin,
Hold primary button fills the blank, three fields above the bar, 360px width."""
import os, unittest
from tests.test_ui import UiTest as Base, ROOT

HOLD = "#/result?method=evaporative&net_supply_m3=&peak_day_m3=2610&cycles=3"


class V3f(unittest.TestCase):
    setUpClass = classmethod(Base.setUpClass.__func__)
    tearDownClass = classmethod(Base.tearDownClass.__func__)

    def page(self, hash_="", w=390, h=844):
        ctx = self.br.new_context(viewport={"width": w, "height": h}, has_touch=True, is_mobile=True)
        p = ctx.new_page(); p.goto(self.url + hash_); return p

    # 1 one 3D-emoji image per screen, shipped in the repo (no external request), loaded
    def test_one_emoji_graphic_per_screen(self):
        for h in ("", "#/result?method=evaporative&net_supply_m3=5000&peak_day_m3=2000",
                  "#/result?method=evaporative", "#/result?method=evaporative&net_supply_m3=1000", HOLD):
            p = self.page(h); p.wait_for_selector("img.gfx")
            g = p.locator("#app img.gfx"); self.assertEqual(g.count(), 1, h)
            self.assertEqual(p.locator("#app svg.gfx").count(), 0)
            self.assertTrue(g.evaluate("e=>e.complete&&e.naturalWidth>0"), h)
            self.assertTrue(g.get_attribute("src").startswith("assets/e-"))
        srcs = set()
        for h in ("#/result?method=evaporative&net_supply_m3=5000&peak_day_m3=2000", "#/result?method=evaporative",
                  "#/result?method=evaporative&net_supply_m3=1000", HOLD):
            srcs.add(self.page(h).get_attribute("img.gfx", "src"))
        self.assertEqual(len(srcs), 4)
        for s in srcs | {"assets/e-idle.png"}: self.assertTrue(os.path.exists(os.path.join(ROOT, s)))

    # 2 Reset to example keeps the 20px right margin at 390 and 360, and nothing scrolls sideways
    def test_reset_keeps_margin_and_no_overflow(self):
        for w in (390, 375, 360):
            p = self.page("", w); p.fill("#f-net_supply_m3", "1200"); p.tap("#go"); p.wait_for_selector(".verdict")
            p.tap("#change"); p.wait_for_selector("#reset:not([disabled])")
            r = p.locator("#reset").bounding_box()
            self.assertLessEqual(r["x"] + r["width"], w - 20, (w, r))
            self.assertEqual(p.evaluate("document.documentElement.scrollWidth"), w, w)

    def test_no_horizontal_overflow_at_360_everywhere(self):
        for h in ("", "#/?method=liquid", "#/?method=hydrothermal", "#/?method=direct_air", HOLD,
                  "#/result?method=hydrothermal&permit_flow_m3d=200000", "#/result?method=direct_air"):
            p = self.page(h, 360); p.wait_for_selector("h1")
            self.assertEqual(p.evaluate("document.documentElement.scrollWidth"), 360, h)

    # 3 Hold: main button fills the blank (goes to that field, focused); copy is secondary
    def test_hold_main_button_fills_the_blank(self):
        p = self.page(HOLD); p.wait_for_selector(".verdict")
        main = p.locator(".cta"); self.assertEqual(main.count(), 1)
        self.assertEqual(main.inner_text(), "Fill in the blank")
        self.assertEqual(p.locator("#copy").count(), 1)
        self.assertFalse(p.locator("#copy").evaluate("e=>e.classList.contains('cta')"))
        main.tap(); p.wait_for_selector("#go")
        self.assertEqual(p.evaluate("document.activeElement.id"), "f-net_supply_m3")
        b = p.locator("#f-net_supply_m3").bounding_box(); bar = p.locator(".cta-wrap").bounding_box()
        self.assertLess(b["y"] + b["height"], bar["y"]); self.assertGreater(b["y"], 56)
        self.assertEqual(p.locator(".ferr").count(), 0)

    def test_hold_copy_still_works_and_other_verdicts_keep_copy_main(self):
        p = self.page(HOLD); p.tap("#copy"); p.wait_for_function("document.getElementById('copy').textContent!='Copy this result link'")
        for q in ("net_supply_m3=5000&peak_day_m3=2000", "net_supply_m3=3630&peak_day_m3=2610", "net_supply_m3=1000"):
            p = self.page("#/result?method=evaporative&" + q); p.wait_for_selector(".verdict")
            self.assertEqual(p.locator(".cta").inner_text(), "Copy this result link")

    def test_hold_with_several_blanks_goes_to_first_blank(self):
        p = self.page("#/result?method=evaporative&net_supply_m3=&peak_day_m3="); p.wait_for_selector(".verdict")
        self.assertEqual(p.locator(".cta").inner_text(), "Fill in the blanks")
        p.tap(".cta"); p.wait_for_selector("#go")
        self.assertEqual(p.evaluate("document.activeElement.id"), "f-net_supply_m3")

    # 4 the first screen shows all three number fields above the fixed bar (390x844)
    def test_three_fields_above_the_bar_on_first_screen(self):
        p = self.page(); bar = p.locator(".cta-wrap").bounding_box()
        for k in ("net_supply_m3", "peak_day_m3", "cycles"):
            b = p.locator("#f-" + k).bounding_box()
            self.assertLessEqual(b["y"] + b["height"], bar["y"], (k, b, bar))

    # 5 the Hold copy button is a quiet text button like Change numbers, and the title never wraps at 360
    def test_hold_copy_is_quiet_and_title_one_line_at_360(self):
        p = self.page(HOLD, 360); p.wait_for_selector(".verdict")
        st = p.locator("#copy").evaluate("e=>{const s=getComputedStyle(e);return [s.borderTopWidth,s.backgroundColor,e.getBoundingClientRect().width]}")
        self.assertEqual(st[0], "0px"); self.assertEqual(st[1], "rgba(0, 0, 0, 0)"); self.assertGreater(st[2], 300)
        self.assertLess(p.locator(".bar-title").bounding_box()["height"], 30)
