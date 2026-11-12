"""Browser tests pinning the 2nd UX review (r4/r5, 2026-11-13). 390x844 touch phone."""
import re, unittest
from tests.test_ui import UiTest as Base

STATUS = r"(Fit|Conditional|Not fit)"


class V3c(Base):
    def verdict(self, p):
        p.wait_for_selector(".verdict"); return p.locator(".verdict").inner_text()

    # 1 every chip fills its own example values; numeric methods judge in one tap
    def test_each_method_judges_with_example_values(self):
        for label, field in (("Evaporative", "net_supply_m3"), ("Hybrid", "net_supply_m3"), ("River", "heat_mw")):
            p = self.page()
            p.locator("[role=radio]", has_text=label).tap()
            self.assertNotEqual(p.input_value("#f-" + field), "", label)
            p.tap("#go")
            self.assertRegex(self.verdict(p), STATUS + r".*×", label)
        p = self.page(); p.locator("[role=radio]", has_text="Direct").tap(); p.tap("#go")
        self.assertIn("not judged", self.verdict(p))

    # 2 edited value survives a method round trip; untouched ones come from the examples
    def test_user_value_kept_across_method_switch(self):
        p = self.page()
        p.fill("#f-net_supply_m3", "1000")
        p.locator("[role=radio]", has_text="River").tap()
        self.assertEqual(p.input_value("#f-heat_mw"), "48")
        p.fill("#f-heat_mw", "60")
        p.locator("[role=radio]", has_text="Evaporative").tap()
        self.assertEqual(p.input_value("#f-net_supply_m3"), "1000")
        self.assertEqual(p.input_value("#f-peak_day_m3"), "2610")
        p.locator("[role=radio]", has_text="River").tap()
        self.assertEqual(p.input_value("#f-heat_mw"), "60")
        # a field the user blanked stays blank
        p.locator("[role=radio]", has_text="Evaporative").tap()
        p.fill("#f-cycles", ""); p.locator("[role=radio]", has_text="Hybrid").tap()
        self.assertEqual(p.input_value("#f-cycles"), "")

    # 3 reset-to-example link: hidden until something differs, then restores everything
    def test_reset_to_example(self):
        p = self.page()
        self.assertEqual(p.locator("#reset").evaluate("e=>getComputedStyle(e).display"), "none")
        p.fill("#f-net_supply_m3", "1"); p.locator("[role=radio]", has_text="River").tap()
        p.fill("#f-heat_mw", "5")
        p.tap("#reset")
        self.assertEqual(p.input_value("#f-heat_mw"), "48")
        p.locator("[role=radio]", has_text="Evaporative").tap()
        self.assertEqual(p.input_value("#f-net_supply_m3"), "3630")
        self.assertEqual(p.locator("#reset").evaluate("e=>getComputedStyle(e).display"), "none")

    # 4 explicit blank still means Hold
    def test_blank_is_hold(self):
        p = self.page()
        p.fill("#f-net_supply_m3", ""); p.fill("#f-cycles", ""); p.tap("#go")
        self.assertIn("Hold", self.verdict(p))
        self.assertIn("Net supply", p.inner_text(".todo"))

    # 5 error sentence is visible above the fixed CTA, for format and range errors
    def _assert_error_visible(self, p, field):
        p.wait_for_selector("#f-%s-err" % field)
        err = p.locator("#f-%s-err" % field).bounding_box()
        cta = p.locator(".cta-wrap").bounding_box()
        self.assertGreaterEqual(err["y"], 56)  # below top bar
        self.assertLessEqual(err["y"] + err["height"], cta["y"] + 1)
        self.assertEqual(p.evaluate("document.activeElement.id"), "f-" + field)

    def test_format_error_not_hidden_by_cta(self):
        p = self.page(); p.fill("#f-cycles", "ab"); p.tap("#go"); self._assert_error_visible(p, "cycles")

    def test_range_error_points_at_field(self):
        p = self.page(); p.fill("#f-cycles", "1"); p.tap("#go")
        self._assert_error_visible(p, "cycles")
        self.assertIn("above 1", p.inner_text("#f-cycles-err"))
        self.assertEqual(p.locator("#error").count(), 0)
        p = self.page(); p.fill("#f-peak_day_m3", "0"); p.tap("#go"); self._assert_error_visible(p, "peak_day_m3")
        p = self.page(); p.locator("[role=radio]", has_text="River").tap(); p.fill("#f-delta_t_k", "0"); p.tap("#go")
        self._assert_error_visible(p, "delta_t_k")

    # 6 history: input -> result is one step; in-app Back and browser back do the same thing
    def _fresh(self):
        ctx = self.br.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
        p = ctx.new_page(); p.goto("about:blank"); p.goto(self.url); p.wait_for_selector("#go"); return p

    def test_in_app_back_does_not_loop(self):
        p = self._fresh()
        p.tap("#go"); self.verdict(p)
        p.tap("#back"); p.wait_for_selector("#go")
        p.go_back()
        self.assertEqual(p.url, "about:blank")

    def test_change_numbers_does_not_loop(self):
        p = self._fresh()
        p.tap("#go"); self.verdict(p)
        p.tap("#change"); p.wait_for_selector("#go")
        p.go_back()
        self.assertEqual(p.url, "about:blank")

    def test_browser_back_twice_leaves_app(self):
        p = self._fresh()
        p.locator("[role=radio]", has_text="River").tap(); p.tap("#go"); self.verdict(p)
        p.go_back(); p.wait_for_selector("#go")
        self.assertEqual(p.input_value("#f-heat_mw"), "48")
        p.go_back(); self.assertEqual(p.url, "about:blank")

    def test_error_adds_no_history_entry(self):
        p = self._fresh()
        p.fill("#f-cycles", "ab"); p.tap("#go"); p.wait_for_selector("#f-cycles-err")
        p.go_back(); self.assertEqual(p.url, "about:blank")

    def test_result_deep_link_back_goes_to_check(self):
        p = self.page("#/result?method=evaporative")
        self.verdict(p); p.tap("#back"); p.wait_for_selector("#go")

    # 7 one graphic per verdict, 64-96px, four different shapes
    def test_verdict_graphic(self):
        seen = set()
        for q in ("net_supply_m3=5000&peak_day_m3=2000", "", "net_supply_m3=1000", "net_supply_m3="):
            p = self.page("#/result?method=evaporative&" + q)
            g = p.locator(".gfx"); b = g.bounding_box()
            self.assertTrue(64 <= b["width"] <= 96 and 64 <= b["height"] <= 96, b)
            seen.add(g.inner_html())
        self.assertEqual(len(seen), 4)

    # 8 hold word is dark, pill is an outline (not status colored), pill = chip name
    def test_hold_dark_and_pill_name(self):
        p = self.page("#/result?method=hydrothermal&heat_mw=")
        self.assertEqual(p.locator(".vw").evaluate("e=>getComputedStyle(e).color"), "rgb(51, 61, 75)")
        self.assertEqual(p.locator(".pill").inner_text(), "River or dam")

    # 9 first screen: example line sits above the CTA fold, h1 24px
    def test_example_line_on_first_screen(self):
        p = self.page()
        b = p.locator("#example").bounding_box(); self.assertLess(b["y"] + b["height"], 400)
        self.assertEqual(p.locator("h1").evaluate("e=>getComputedStyle(e).fontSize"), "24px")

    # 10 writing: the don't-guess promise appears once on the input screen, selected chip has hover style
    def test_promise_once_and_selected_hover(self):
        p = self.page()
        self.assertEqual(len(re.findall(r"Unknown\? Leave blank", p.content())), 0)
        self.assertEqual(len(re.findall("instead of guessing", p.inner_text("#app"))), 1)
        self.assertIn("water quality", p.inner_text("#app"))
        self.assertIn("[aria-checked=true]:hover", open("index.html").read())


if __name__ == "__main__":
    unittest.main()
