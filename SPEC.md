---
id: 20261113T0100-spec-peak-day-water-check
title: "SPEC - Peak-Day Water Check public demo"
type: reference
status: seedling
created: 2026-11-13
updated: 2026-11-13
links: ["[[projects/xylem-student-innovation-2026]]"]
private: false
---
# Peak-Day Water Check - SPEC (v0.1 2026-11-13)

kind: service

## 0. 목적 (Purpose, one line)
A reviewer opens one public link and, within 30 seconds, enters site numbers, gets a verdict (Fit, Conditional, Not fit, Hold) and the list of measurements still needed. Missing numbers are never guessed.

## 1. 성공 조건 · 마감 · 비목표 (Success, deadline, non-goals)
- 성공 조건 (Success): public URL returns 200 with the product name; Check -> Result -> back works on a 390x844 touch profile; Hangul on screen = 0; verdict.js equals domain/verdict.py on 1,000+ inputs (tests/test_parity.py).
- Deadline: Xylem Student Innovation Challenge submission 2026-11-20.
- 비목표 (Non-goals): login, payment, data upload, a new cooling-physics engine (the demo only applies the existing verdict rule).

## 2. Constraints
- Product name is Peak-Day Water Check (not Ecolab's Water Navigator). Static hosting, no cost, no external fonts or CDNs, no data leaves the browser.

## 3. Ubiquitous language
| Term | Meaning | Code name |
|---|---|---|
| Peak-day need | cooling make-up water on the hottest day (m3/day) | peak_day_m3 |
| Net supply | reclaimed water usable in dry season (m3/day) | net_supply_m3 |
| Ratio | net supply / peak-day need | ratio |
| Verdict | Fit (>=2x), Conditional (1-2x), Not fit (<1x), Hold | status |

## 4. Context and domain
- Domain (pure): domain/verdict.py `judge_option`, `judge_site`; supply.grade; hydrothermal.passthrough_flow_m3_per_day.
- Presentation: demo_text.py (English labels), demo_app.py (local server), index.html + verdict.js (public static page).

## 5. Use cases
| UC | Input | Output | Rule |
|---|---|---|---|
| Check a site | method + up to 4 numbers | verdict line, 2 reasons, measurements list | blank number -> Hold + what to measure; bad number -> error with the fix |

## 6. Given / When / Then
- Given the Jangseong example (3630 / 2610, N=3), When Check this site, Then "Conditional 1.39x".
- Given 5000 / 2000, Then "Fit 2.50x". Given all blanks, Then "Hold" and a list of missing measurements.

## UI 수용기준 (UI acceptance)
One task per screen, input fields <= 4 with defaults, fixed bottom CTA >= 52px, body >= 16px, spacing multiples of 4, status pairs light background + dark text, no external dependency.
