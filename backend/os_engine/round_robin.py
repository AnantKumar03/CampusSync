def round_robin(burst_time, quantum):
    remaining = burst_time[:]
    waiting = [0] * len(burst_time)
    turnaround = [0] * len(burst_time)

    current = 0

    while True:
        done = True

        for i in range(len(remaining)):
            if remaining[i] > 0:
                done = False

                if remaining[i] > quantum:
                    current += quantum
                    remaining[i] -= quantum
                else:
                    current += remaining[i]
                    waiting[i] = current - burst_time[i]
                    remaining[i] = 0
                    turnaround[i] = current

        if done:
            break

    return {
        "waiting_time": waiting,
        "turnaround_time": turnaround,
        "average_waiting_time": sum(waiting) / len(waiting),
        "average_turnaround_time": sum(turnaround) / len(turnaround)
    }