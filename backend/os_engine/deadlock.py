def deadlock_check(allocation, request):
    # Simple deadlock detection for a small project demonstration.
    n = len(allocation)
    work = [1] * len(allocation[0])
    finish = [False] * n

    changed = True

    while changed:
        changed = False

        for i in range(n):
            if not finish[i]:
                possible = True

                for j in range(len(work)):
                    if request[i][j] > work[j]:
                        possible = False
                        break

                if possible:
                    for j in range(len(work)):
                        work[j] += allocation[i][j]

                    finish[i] = True
                    changed = True

    deadlocked = [i for i in range(n) if not finish[i]]

    return {
        "deadlock": len(deadlocked) > 0,
        "processes": deadlocked
    }