def update(p, alpha=0.7):
    raw = [x ** (1 + 2 * alpha) for x in p]
    total = sum(raw)
    return [x / total for x in raw]
