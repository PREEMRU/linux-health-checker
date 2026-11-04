#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Error: run this script as root"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [[ -d /opt/linux-health-checker ]]; then
    echo "Directory already exists"
else
    mkdir -p /opt/linux-health-checker
    echo "Directory created"
fi

if id health-checker &>/dev/null; then
    echo "User exists"
else
    useradd --system --no-create-home --shell /usr/sbin/nologin health-checker
    echo "User created"
fi

install -o root -g root -m 644 "$PROJECT_DIR/health.py" /opt/linux-health-checker/health.py

install -o root -g root -m 644 \
    "$SCRIPT_DIR/linux-health-checker.service" \
    /etc/systemd/system/linux-health-checker.service

install -o root -g root -m 644 \
    "$SCRIPT_DIR/linux-health-checker.timer" \
    /etc/systemd/system/linux-health-checker.timer

systemctl daemon-reload
systemctl enable --now linux-health-checker.timer
echo "Installation completed"