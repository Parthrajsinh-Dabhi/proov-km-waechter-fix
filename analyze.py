# analyze.py
#
# SUMMARY (two lines):
# The single strongest predictor of breakdown is km_since_service: 81% of cars that
# broke down had driven more than 10,000 km since their last service, vs only 33% of
# cars that did not. Age and total odometer look obvious but turn out to be near-useless:
# the mean age is 5.88 years for breakers vs 5.89 years for non-breakers — essentially
# identical. The risk score below therefore weights km_since_service heavily (55%),
# with avg_daily_km (25%) and load_factor (20%) as secondary signals.

import csv

# ── 1. Load the history ────────────────────────────────────────────────────────

rows: list[dict] = []
with open("fleet_history.csv") as f:
    for r in csv.DictReader(f):
        rows.append({
            "car_id":            r["car_id"],
            "odometer_km":       float(r["odometer_km"]),
            "km_since_service":  float(r["km_since_service"]),
            "avg_daily_km":      float(r["avg_daily_km"]),
            "load_factor":       float(r["load_factor"]),
            "age_years":         float(r["age_years"]),
            "broke_down":        int(r["broke_down"]),
        })

# ── 2. Find which columns separate the two groups ─────────────────────────────

broke = [r for r in rows if r["broke_down"] == 1]
ok    = [r for r in rows if r["broke_down"] == 0]

print("Group sizes: %d breakdowns  /  %d no-breakdown" % (len(broke), len(ok)))
print()
print("Column-by-column comparison (mean values):")
print(f"  {'Column':<22}  {'Mean(broke)':>12}  {'Mean(ok)':>10}  {'Ratio b/ok':>10}")
print("  " + "-" * 58)

cols = ["odometer_km", "km_since_service", "avg_daily_km", "load_factor", "age_years"]
for c in cols:
    mb = sum(r[c] for r in broke) / len(broke)
    mo = sum(r[c] for r in ok)    / len(ok)
    ratio = mb / mo if mo else float("inf")
    print(f"  {c:<22}  {mb:>12.2f}  {mo:>10.2f}  {ratio:>10.3f}")

print()
# Threshold check — confirms km_since_service is the key signal
kss_t, lf_t, age_t = 10000, 0.60, 7
b_hi_kss = sum(1 for r in broke if r["km_since_service"] > kss_t)
o_hi_kss = sum(1 for r in ok    if r["km_since_service"] > kss_t)
print("km_since_service > %d km:  broke %d/%d (%d%%)   ok %d/%d (%d%%)" % (
    kss_t,
    b_hi_kss, len(broke), 100 * b_hi_kss // len(broke),
    o_hi_kss, len(ok),    100 * o_hi_kss // len(ok),
))
b_hi_lf  = sum(1 for r in broke if r["load_factor"] >= lf_t)
o_hi_lf  = sum(1 for r in ok    if r["load_factor"] >= lf_t)
print("load_factor >= %.2f:       broke %d/%d (%d%%)   ok %d/%d (%d%%)" % (
    lf_t,
    b_hi_lf, len(broke), 100 * b_hi_lf // len(broke),
    o_hi_lf, len(ok),    100 * o_hi_lf // len(ok),
))
b_hi_age = sum(1 for r in broke if r["age_years"] >= age_t)
o_hi_age = sum(1 for r in ok    if r["age_years"] >= age_t)
print("age_years >= %d:            broke %d/%d (%d%%)   ok %d/%d (%d%%)" % (
    age_t,
    b_hi_age, len(broke), 100 * b_hi_age // len(broke),
    o_hi_age, len(ok),    100 * o_hi_age // len(ok),
))

# ── 3. Build a risk score 0–100 ───────────────────────────────────────────────
#
# Weights reflect the separation power measured above:
#   km_since_service  55%  (ratio 1.61, threshold catch-rate 81%)
#   avg_daily_km      25%  (ratio 1.22 — harder-driven cars wear faster)
#   load_factor       20%  (ratio 1.19 — payload stress matters)
#   age_years          0%  (ratio 0.998 — statistically flat, ignored)
#   odometer_km        0%  (ratio 1.003 — flat, ignored)

max_kss   = max(r["km_since_service"] for r in rows)
max_daily = max(r["avg_daily_km"]     for r in rows)
max_lf    = max(r["load_factor"]      for r in rows)


def risk_score(r: dict) -> float:
    """Return a 0–100 breakdown-risk score. Higher = more urgent."""
    s = (0.55 * r["km_since_service"] / max_kss
       + 0.25 * r["avg_daily_km"]      / max_daily
       + 0.20 * r["load_factor"]       / max_lf)
    return round(s * 100, 1)


# ── 4. Print cars ranked by risk ──────────────────────────────────────────────

ranked = sorted(rows, key=risk_score, reverse=True)

print()
print("Cars ranked by breakdown risk (highest first):")
print(f"  {'Rank':<5} {'Car ID':<12} {'Score':>6}  {'BD':>3}  {'km_since':>9}  {'daily_km':>8}  {'load':>5}  {'age':>4}")
print("  " + "-" * 68)
for i, r in enumerate(ranked, 1):
    bd_marker = " !" if r["broke_down"] else "  "
    print(f"  {i:<5} {r['car_id']:<12} {risk_score(r):>6.1f}{bd_marker}  {r['km_since_service']:>9.0f}  {r['avg_daily_km']:>8.0f}  {r['load_factor']:>5.2f}  {r['age_years']:>4.0f}")
