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

def get_status(usage: float | None) -> str:
    if usage is None:
        return "UNKNOWN"

    if usage >= 90:
        return "CRITICAL"
    elif usage >= 80:
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

def main():
    cpu = get_cpu_usage()
    ram = get_memory_usage()
    disk = get_disk_usage()
    ssh = check_service('ssh')

    cpu_code = get_exit_code(get_status(cpu))
    ram_code = get_exit_code(get_status(ram))
    disk_code = get_exit_code(get_status(disk))
    ssh_code = 0 if ssh else 2

    overall_code = max(cpu_code, ram_code, disk_code, ssh_code)

    print(f'''=== SERVER HEALTH REPORT ===
    CPU:    {cpu}% [{get_status(cpu)}]
    RAM:    {ram}% [{get_status(ram)}]
    Disk:   {disk}% [{get_status(disk)}]
    SSH:    {"ACTIVE" if ssh else "INACTIVE"}''')

    sys.exit(overall_code)


if __name__ == '__main__':
    main()