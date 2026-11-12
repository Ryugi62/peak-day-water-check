import unittest, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from demo_app import render


class DemoTest(unittest.TestCase):
    def test_preset_matches_v9_scenario1(self):   # Jangseong 3630/2610 = 1.39x conditional
        h = render({})
        self.assertIn("1.39x", h)
        self.assertIn('id="r-evaporative"', h)
        self.assertIn("Conditional", h)

    def test_user_input_changes_verdict(self):      # reviewer input 5000/2000 = 2.5x fit
        h = render({"net_supply_m3": ["5000"], "peak_day_m3": ["2000"], "cycles": ["4"], "weather_station": ["108"], "opt": ["evaporative"]})
        self.assertIn("2.50x", h); self.assertIn("Fit", h)

    def test_blank_gives_hold_and_missing_list(self):
        h = render({"opt": ["evaporative"]})
        self.assertIn("Hold", h); self.assertIn("Measure next", h); self.assertNotIn("x</span>", h)

    def test_bad_number_reported(self):
        self.assertIn('id="error"', render({"net_supply_m3": ["abc"], "opt": ["evaporative"]}))

    def test_zero_peak_value_error_shown(self):
        h = render({"net_supply_m3": ["10"], "peak_day_m3": ["0"], "cycles": ["3"], "weather_station": ["1"], "opt": ["evaporative"]})
        self.assertIn('id="error"', h)

    def test_direct_air_out_of_scope(self):
        self.assertIn("no water-use physics", render({"opt": ["direct_air"]}))

    def test_screen_is_english_only(self):             # zero Hangul on any screen state
        for qs in ({}, {"opt": ["evaporative", "liquid", "hydrothermal", "direct_air"]}, {"net_supply_m3": ["abc"], "opt": ["liquid"]},
                   {"net_supply_m3": ["10"], "peak_day_m3": ["0"], "cycles": ["3"], "weather_station": ["1"], "opt": ["evaporative"]}):
            self.assertIsNone(re.search(r"[가-힣ㄱ-ㆎ]", render(qs)), qs)

    def test_product_name_and_no_banned_name(self):
        h = render({})
        self.assertIn("Peak-Day Water Check", h); self.assertNotIn("Water Navigator", h)


if __name__ == "__main__":
    unittest.main()
