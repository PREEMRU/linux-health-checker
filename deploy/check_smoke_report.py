import json
import sys


def read_runs(path):
    runs = {}

    with open(path) as lines:
        for line in lines:
            entry = json.loads(line)

            invocation_id = entry.get("_SYSTEMD_INVOCATION_ID")
            message = entry.get("MESSAGE")

            if not invocation_id or not isinstance(message, str):
                continue

            if invocation_id not in runs:
                runs[invocation_id] = []
            runs[invocation_id].extend(message.splitlines())

    return runs

if len(sys.argv) != 3:
    sys.exit("Usage: check_smoke_report.py <before.json> <after.json>")

dict_before = read_runs(sys.argv[1])
dict_after = read_runs(sys.argv[2])

diff = dict_after.keys() - dict_before.keys()

if len(diff) != 1:
    sys.exit(1)

new_launch = dict_after[next(iter(diff))]

if "=== SERVER HEALTH REPORT ===" not in new_launch:
    sys.exit("Missing report header")

report_lines = [line.lstrip() for line in new_launch]
stats_lines = ["SSH:", "CPU:", "RAM:", "Disk:"]

for stat in stats_lines:
    if not any(line.startswith(stat) for line in report_lines):
        sys.exit(f"Missing report field: {stat}")