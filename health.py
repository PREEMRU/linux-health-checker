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


if __name__ == '__main__':
    print(f"CPU Usage: {get_cpu_usage()}%")