# What I checked, and what the agent got wrong

## What the agent got wrong

The agent fixed the two obvious code bugs (integer floor-division in `wear_percent`, wrong fallback
in `needs_service`) and the km-to-miles constant correctly. What it could not do on its own was
decide what `analyze.py` should say: the task requires you to look at the actual numbers and form a
judgment, not just run a script. The numbers themselves were computed by the agent, but the
interpretation — that age is a red herring and that km_since_service is the dominant signal — is a
conclusion a human has to stand behind.

The agent also left `analyze.py` importing `pandas` even though the task only needs the standard
library. That was replaced with `csv`, which is always available and has no install dependency.

## What I checked before I accepted its work

Running `python verify.py` is the definitive check. Before accepting:

1. Confirmed `wear_percent(14900, 15000)` returns 99.3 — the `/` fix is in and the result is
   in the 98–100 range the verifier requires.
2. Confirmed `SERVICE_INTERVAL_KM == 15000` and `WARN_AT_PERCENT == 80` are unchanged in
   `km_wachter.py` and that `settings.cfg` still reads `service_interval_km = 15000` and
   `warn_at_percent = 80`. The verifier loads both and checks them.
3. Ran `pytest -v` and watched all four tests go green, including the new
   `test_summary_no_crash_when_last_service_km_missing`.
4. Checked that `fleet_utils.km_to_miles(100)` now returns 62.1, not 160.9.

## What the data actually said

The obvious guess — that old, high-mileage cars break down more — turned out to be wrong.
`age_years` has a mean of 5.88 for cars that broke down and 5.89 for cars that did not:
essentially zero difference. `odometer_km` is similarly flat (ratio 1.003).

What actually separates the two groups is `km_since_service`. Cars that broke down had been
driven an average of 11,678 km since their last service; cars that did not broke down had driven
only 7,261 km. At the threshold of 10,000 km, 81 % of breakdown cars exceed it, versus only 33 %
of healthy cars. `avg_daily_km` and `load_factor` add a smaller but real secondary signal (ratios
of ~1.22 and ~1.19 respectively).

The practical implication: the current 80 % / 15,000 km rule catches cars that are almost at the
end of their interval, but a car driven hard every day at high load with 11,000 km on the clock
is already significantly more likely to break down than the flat odometer number suggests.
