#!/usr/bin/env bash

set -e

sudo -n /usr/bin/journalctl -u linux-health-checker-smoke.service -b -n 100 -o json --no-pager > before.json

sudo -n /usr/bin/systemctl start linux-health-checker-smoke.service

sudo -n /usr/bin/journalctl -u linux-health-checker-smoke.service -b -n 100 -o json --no-pager > after.json

python3 deploy/check_smoke_report.py before.json after.json