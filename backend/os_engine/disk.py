def disk_fcfs(requests, head):
    movement = 0
    current = head

    for request in requests:
        movement += abs(current - request)
        current = request

    return {
        "order": requests,
        "total_head_movement": movement
    }


def sstf(requests, head):
    requests = requests[:]
    order = []
    movement = 0
    current = head

    while requests:
        nearest = min(requests, key=lambda x: abs(x - current))
        movement += abs(current - nearest)
        current = nearest
        order.append(nearest)
        requests.remove(nearest)

    return {
        "order": order,
        "total_head_movement": movement
    }


def scan(requests, head, disk_size):
    left = sorted([x for x in requests if x < head])
    right = sorted([x for x in requests if x >= head])

    order = right + [disk_size - 1] + left[::-1]

    movement = 0
    current = head

    for request in order:
        movement += abs(current - request)
        current = request

    return {
        "order": order,
        "total_head_movement": movement
    }