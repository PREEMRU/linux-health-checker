import argparse
import shutil
import subprocess
import sys
import time


def read_cpu_stats():
    with open('/proc/stat', 'r') as file:
        line = file.readline()

        values = [int(i) for i in line.split()[1:]]
        return values

def get_cpu_usage():
    first = read_cpu_stats()
    time.sleep(1)
    second = read_cpu_stats()

    total_delta = sum(second[:8]) - sum(first[:8])
    if total_delta == 0:
        return None
    
    idle_delta = sum(second[3:5]) - sum(first[3:5])

    return round(100 * (1 - idle_delta / total_delta), 2)

def get_memory_usage():
    memtotal = None
    memav = None
    with open('/proc/meminfo', 'r') as file:

        for line in file:
            if line.startswith('MemTotal'):
                memtotal = int(line.split()[1])

            if line.startswith('MemAvailable'):
                memav = int(line.split()[1])

        if memav is None or memtotal is None or memtotal == 0:
            return None

        return round(100 * (memtotal - memav) / memtotal, 2)

def get_disk_usage():
    disk = shutil.disk_usage('/')

    if disk.total == 0:
        return None
    
    return round(100 * disk.used / disk.total, 2)

def check_service(service_name: str) -> bool:
    result = subprocess.run(
        ['systemctl', 'is-active', service_name],
        capture_output=True, text=True, check=False
    )

    return result.returncode == 0

def get_status(usage: float | None,
               warning: float=80,
               critical: float=90) -> str:
    if usage is None:
        return "UNKNOWN"

    if usage >= critical:
        return "CRITICAL"
    elif usage >= warning:
        return "WARNING"
    else:
        return "OK"

def get_exit_code(status: str) -> int:
    stats = {
        "OK": 0,
        "WARNING": 1,
        "CRITICAL": 2,
        "UNKNOWN": 3
    }

    return stats[status]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Linux Server Health Checker"
    )

    parser.add_argument(
        "--warning",
        type=float,
        default=80,
        help="Warning threshold (default: 80)"
    )

    parser.add_argument(
        "--critical",
        type=float,
        default=90,
        help="Critical threshold (default: 90)"
    )

    args = parser.parse_args()

    if not (0 <= args.warning < args.critical <= 100):
        parser.error(
            "Thresholds must satisfy: 0 <= warning < critical <= 100"
        )

    return args

def main(warning=80, critical=90):
    cpu = get_cpu_usage()
    ram = get_memory_usage()
    disk = get_disk_usage()
    ssh = check_service('ssh')

    cpu_status = get_status(cpu, warning, critical)
    ram_status = get_status(ram, warning, critical)
    disk_status = get_status(disk, warning, critical)

    cpu_code = get_exit_code(cpu_status)
    ram_code = get_exit_code(ram_status)
    disk_code = get_exit_code(disk_status)
    ssh_code = 0 if ssh else 2

    overall_code = max(cpu_code, ram_code, disk_code, ssh_code)

    print(f'''=== SERVER HEALTH REPORT ===
    CPU:    {cpu}% [{cpu_status}]
    RAM:    {ram}% [{ram_status}]
    Disk:   {disk}% [{disk_status}]
    SSH:    {"ACTIVE" if ssh else "INACTIVE"}''')

    sys.exit(overall_code)


if __name__ == '__main__':
    args = parse_args()
    main(args.warning, args.critical)