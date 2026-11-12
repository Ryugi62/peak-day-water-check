"""Peak-Day Water Check - local demo (Python standard library only). Run: python3 demo_app.py [port] -> http://127.0.0.1:8765/
Verdict rules come from domain.verdict (no rules here). The public static page (index.html + verdict.js) ports the same rules; tests/test_parity.py ties them together."""
import html, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from domain.verdict import judge_site, OPTIONS
from demo_text import STATUS_EN, NAME_EN, MEASURE_EN, OUT_OF_SCOPE_EN

FIELDS = [("net_supply_m3", "Net water supply (m3/day)", float), ("peak_day_m3", "Peak-day cooling water need (m3/day)", float),
          ("cycles", "Cycles of concentration N", float), ("dry_basis", "Dry-cooling basis (one sentence)", str), ("weather_station", "Weather station", str),
          ("heat_mw", "Heat to reject (MW)", float), ("delta_t_k", "Allowed temperature rise (K)", float),
          ("permit_flow_m3d", "Permitted intake (m3/day)", float), ("source_distance_km", "Distance to river or dam (km)", float)]
PRESET = {"net_supply_m3": "3630", "peak_day_m3": "2610", "cycles": "3", "weather_station": "156 (Gwangju ASOS)", "heat_mw": "48"}  # Jangseong 40 MW example
GRADE_CLASS = {"적합": "ok", "조건부": "mid", "부적합": "bad", "보류": "hold"}


def parse_form(qs):
    facts, errors = {}, []
    for key, label, typ in FIELDS:
        raw = (qs.get(key, [""])[0] or "").strip()
        if not raw:
            continue
        try:
            facts[key] = typ(raw)
        except ValueError:
            errors.append(f"{label} must be a number. Enter digits only, like 3630.")
    opts = [o for o in qs.get("opt", []) if o in OPTIONS]
    return facts, opts, errors


def run(facts, opts):
    try:
        return judge_site(facts, opts), None
    except ValueError:
        return None, "One number is out of range. Peak-day need and heat must be above 0, cycles above 1, temperature rise above 0."


def render(qs):
    submitted = bool(qs)
    qs = qs or {k: [v] for k, v in PRESET.items()} | {"opt": ["evaporative", "liquid", "hydrothermal", "direct_air"]}
    facts, opts, errors = parse_form(qs)
    res, err = (run(facts, opts) if opts and not errors else (None, None))
    e = html.escape
    rows = "".join(f'<label>{e(label)}<input id="f-{k}" name="{k}" value="{e(qs.get(k, [""])[0])}"></label>' for k, label, _ in FIELDS)
    checks = "".join(f'<label class="c"><input type="checkbox" name="opt" value="{o}"{" checked" if o in opts else ""}> {NAME_EN[o]}</label>' for o in OPTIONS)
    out = ""
    for m in errors + ([err] if err else []):
        out += f'<p class="bad" id="error">{e(m)}</p>'
    if res:
        for o in opts:
            v = res["verdicts"][o]
            num = f'{v["ratio"]:.2f}x' if v["ratio"] is not None else "no number"
            miss = "".join(f'<li>Measure next: {e(MEASURE_EN[m["key"]][0])} - {e(MEASURE_EN[m["key"]][1])}</li>' for m in v["missing"])
            why = f'<li>{e(OUT_OF_SCOPE_EN)}</li>' if v["out_of_scope"] else ""
            out += f'<section class="r {GRADE_CLASS[v["status"]]}" id="r-{o}"><b>{NAME_EN[o]}</b><span class="g">{STATUS_EN[v["status"]]}</span><span>{num}</span><ul>{miss}{why}</ul></section>'
        out += f'<p id="split">Methods disagree: {"yes" if res["split"] else "no"}</p>'
    elif not opts:
        out = '<p>Pick at least one cooling method.</p>'
    note = "" if submitted else '<p class="note" id="preset-note">The first screen shows a fixed example: a 40 MW site in Jangseong. Change any box and press Check to run your numbers.</p>'
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Peak-Day Water Check</title><style>
body{{font:16px/1.5 system-ui;margin:0 auto;max-width:760px;padding:16px;color:#191f28}}label{{display:block;margin:8px 0;font-size:14px}}
input[type=text],input:not([type]){{display:block;width:100%;padding:8px;box-sizing:border-box;font-size:16px}}.c{{display:inline-block;margin-right:12px}}
button{{padding:12px 24px;font-size:16px;background:#1b64da;color:#fff;border:0;border-radius:8px}}.r{{border-left:6px solid #888;padding:8px 12px;margin:10px 0;background:#f4f5f7}}
.r .g{{margin:0 12px;font-weight:700}}.ok{{border-color:#1b9c5f}}.mid{{border-color:#e0a100}}.bad{{border-color:#d93025}}.hold{{border-color:#6b7684}}.note{{color:#6b7684;font-size:14px}}</style>
<h1>Peak-Day Water Check</h1>
<p>Will a new data center have enough water on its hottest day? Enter site numbers and cooling methods. Unsure of a number? Leave it blank: we never make one up, we return <b>Hold</b> and the list of measurements you need.</p>
{note}<form method="get" id="demo-form">{rows}<div>{checks}</div><p><button id="go" type="submit">Check</button></p></form>
<div id="result">{out}</div></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = render(parse_qs(urlparse(self.path).query)).encode()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8765), Handler).serve_forever()
