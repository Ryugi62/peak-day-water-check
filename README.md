# Peak-Day Water Check

Will a new data center have enough water on its hottest day? Enter site numbers and a cooling method; get a verdict (Fit / Conditional / Not fit / Hold) and the list of measurements still needed. Missing numbers are never guessed: the answer is **Hold** plus what to measure.

Live demo (static, runs in your browser, no login, no data sent): https://ryugi62.github.io/peak-day-water-check/

- `index.html` + `verdict.js`: public page (Check -> Result -> back).
- `domain/verdict.py`: the engine's rule; `verdict.js` is a port, and `tests/test_parity.py` runs both on 1,000+ input combinations.
- `demo_app.py`: the same screen as a local Python server (`python3 demo_app.py`).
- Rule: net supply / peak-day need >= 2 is Fit, 1 to 2 is Conditional, under 1 is Not fit. Example input: a 40 MW site in Jangseong, Korea.

Test: `python3 -m unittest discover -s tests -t .`

Not to be confused with Ecolab's Water Navigator IQ: that tool manages water at facilities already running; this one gives a pre-permit verdict for one new site.
