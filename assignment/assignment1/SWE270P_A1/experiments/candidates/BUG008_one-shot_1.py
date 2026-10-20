def detect_cycle(node):
    hare = tortoise = node

    while node:
        if hare is None:
            return False

        tortoise = tortoise.successor
        hare = hare.successor

        if hare is tortoise:
            return True

    return False
