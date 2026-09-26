def fifo(pages, frames):
    memory = []
    faults = 0
    states = []

    for page in pages:
        if page not in memory:
            faults += 1

            if len(memory) < frames:
                memory.append(page)
            else:
                memory.pop(0)
                memory.append(page)

        states.append(memory[:])

    return {
        "page_faults": faults,
        "hits": len(pages) - faults,
        "states": states
    }


def lru(pages, frames):
    memory = []
    faults = 0
    states = []

    for page in pages:
        if page in memory:
            memory.remove(page)
            memory.append(page)
        else:
            faults += 1

            if len(memory) == frames:
                memory.pop(0)

            memory.append(page)

        states.append(memory[:])

    return {
        "page_faults": faults,
        "hits": len(pages) - faults,
        "states": states
    }


def optimal(pages, frames):
    memory = []
    faults = 0
    states = []

    for i, page in enumerate(pages):
        if page not in memory:
            faults += 1

            if len(memory) < frames:
                memory.append(page)
            else:
                future = pages[i + 1:]
                distances = []

                for old_page in memory:
                    if old_page in future:
                        distances.append(future.index(old_page))
                    else:
                        distances.append(9999)

                replace_index = distances.index(max(distances))
                memory[replace_index] = page

        states.append(memory[:])

    return {
        "page_faults": faults,
        "hits": len(pages) - faults,
        "states": states
    }