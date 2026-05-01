# OC Core 1.3.3 Modern Science Benchmark Lanes

The benchmark lanes in this directory are predicate specifications, not certified benchmark wins.

Each lane names the incumbent modern-science source, the OC artifact that may be evaluated, the comparator result, the metric family, the required negative control, the uncertainty/fairness role, and the predicate that would have to pass before any bounded superiority statement could be considered.

The per-domain role separation is materialized by `tools/oc133_modern_science_comparator_factory.py` and validated by `validate_modern_science_register.py`.

Current status: all superiority lanes are blocked for release promotion. Existing OC artifacts may support bounded reconstruction or QA claims only.
