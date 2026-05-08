def update(p, **kwargs):
    total = sum(p)
    return [x / total for x in p]

BASELINE_ID = "replicator_dynamics"
