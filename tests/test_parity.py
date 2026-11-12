"""The public page runs verdict.js; the engine is domain/verdict.py. Same inputs must give the same status, ratio and missing list."""
import json, os, shutil, subprocess, sys, unittest, itertools
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from domain.verdict import judge_option
from demo_text import STATUS_EN, MEASURE_EN

NODE = shutil.which("node")
NUM = {"net_supply_m3": [None, 3630, 5000, 0], "peak_day_m3": [None, 2610, 2000, 0, 8000], "cycles": [None, 3, 1, 4],
       "dry_basis": [None, "vendor sheet"], "weather_station": [None, "156"],
       "heat_mw": [None, 48, 0], "delta_t_k": [None, 7, 0, 5], "permit_flow_m3d": [None, 30000, 0, 90000], "source_distance_km": [None, 3, -1]}


def cases():
    keys = list(NUM)
    base = {"net_supply_m3": 3630, "peak_day_m3": 2610, "cycles": 3, "weather_station": "156", "dry_basis": "x",
            "heat_mw": 48, "delta_t_k": 7, "permit_flow_m3d": 30000, "source_distance_km": 3}
    out = [dict(base)]
    for k in keys:                       # vary one field at a time over all values
        for v in NUM[k]:
            c = dict(base); c[k] = v; out.append({a: b for a, b in c.items() if b is not None})
    for a, b in itertools.combinations(keys, 2):   # and pairs
        for va in NUM[a]:
            for vb in NUM[b]:
                c = dict(base); c[a] = va; c[b] = vb; out.append({x: y for x, y in c.items() if y is not None})
    return out


@unittest.skipUnless(NODE, "node not installed")
class Parity(unittest.TestCase):
    def test_same_verdicts(self):
        cs = cases()
        js = subprocess.run([NODE, "-e", "const P=require('./verdict.js');const cs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
                             "const out=cs.map(f=>P.OPTIONS.map(o=>{try{const r=P.judgeOption(o,f);return {s:r.status,r:r.ratio,m:r.missing.map(x=>[x.key,x.name,x.how])}}catch(e){return {err:1}}}));"
                             "console.log(JSON.stringify(out))"], input=json.dumps(cs), capture_output=True, text=True, cwd=ROOT, check=True)
        got = json.loads(js.stdout)
        n = 0
        for facts, row in zip(cs, got):
            for opt, g in zip(("evaporative", "liquid", "hydrothermal", "direct_air"), row):
                try:
                    p = judge_option(opt, facts)
                except ValueError:
                    self.assertEqual(g, {"err": 1}, (opt, facts)); n += 1; continue
                self.assertNotIn("err", g, (opt, facts))
                self.assertEqual(g["s"], STATUS_EN[p["status"]], (opt, facts))
                if p["ratio"] is None:
                    self.assertIsNone(g["r"])
                else:
                    self.assertAlmostEqual(g["r"], p["ratio"], places=9)
                self.assertEqual([m[0] for m in g["m"]], [m["key"] for m in p["missing"]], (opt, facts))
                for key, name, how in g["m"]:
                    self.assertEqual((name, how), MEASURE_EN[key])
                n += 1
        self.assertGreater(n, 1000)


if __name__ == "__main__":
    unittest.main()
