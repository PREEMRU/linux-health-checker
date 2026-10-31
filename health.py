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


if __name__ == '__main__':
    print(f"CPU Usage: {get_cpu_usage()}%")
    print(f"RAM Usage: {get_memory_usage()}%")