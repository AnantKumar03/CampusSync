def fcfs(burst_time):
    waiting = []
    turnaround = []
    current = 0

    for burst in burst_time:
        waiting.append(current)
        current += burst
        turnaround.append(current)

    return {
        "waiting_time": waiting,
        "turnaround_time": turnaround,
        "average_waiting_time": sum(waiting) / len(waiting),
        "average_turnaround_time": sum(turnaround) / len(turnaround)
    }