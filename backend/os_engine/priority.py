def priority_scheduling(burst_time, priority):
    processes = list(range(len(burst_time)))

    # Smaller priority number means higher priority.
    processes.sort(key=lambda i: priority[i])

    waiting = [0] * len(burst_time)
    turnaround = [0] * len(burst_time)

    current = 0

    for i in processes:
        waiting[i] = current
        current += burst_time[i]
        turnaround[i] = current

    return {
        "order": [i + 1 for i in processes],
        "waiting_time": waiting,
        "turnaround_time": turnaround,
        "average_waiting_time": sum(waiting) / len(waiting),
        "average_turnaround_time": sum(turnaround) / len(turnaround)
    }