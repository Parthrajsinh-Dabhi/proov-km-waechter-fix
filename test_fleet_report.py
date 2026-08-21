# test_fleet_report.py
from fleet_report import fleet_summary

SAMPLE = [
    {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
    {"id": "VOS-2210", "odometer": 48400, "last_service_km": 45000},
]


def test_summary_counts_due_cars():
    # Only VOS-4471 is nearly worn, so exactly one car is due.
    assert fleet_summary(SAMPLE)["due"] == 1


# TODO(you): with IBM Bob, ADD a test that fleet_summary does NOT crash when a car has no
# "last_service_km" reading (like VOS-7788 in fleet_sample.json). It crashes today. Make it pass.
def test_summary_no_crash_when_last_service_km_missing():
    # A car with no "last_service_km" must not crash fleet_summary.
    # With no history, km_since is 0, so the car counts as freshly serviced (not due).
    fleet = [{"id": "VOS-7788", "odometer": 92000}]
    result = fleet_summary(fleet)
    assert result["count"] == 1
    assert result["due"] == 0
