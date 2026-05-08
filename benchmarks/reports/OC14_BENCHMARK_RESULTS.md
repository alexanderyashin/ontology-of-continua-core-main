# OC14 Benchmark Results

- schema: `OC14_BENCHMARK_RESULTS_v2`
- seed: `140`
- tasks: `10/10`
- baselines accepted: `9/9`
- failures: `0`
- no-signalling max: `0.0`
- output hash: `9381f1b2df7b14792cfc307d647aa57938583f7e94c56bd5acc345b76bb01262`
- support ceiling: `S3_NUMERICAL_OR_SIMULATION_EVIDENCE`

| Task | Failure | Claim effect | Key metrics |
| --- | --- | --- | --- |
| `toy_sharpening` | `false` | IMN is retained only as a sharpening heuristic baseline. | entropy_reduction=0.260208, parameter_overfit_score=0.31, baseline_advantage_delta=0.0 |
| `double_slit_toy` | `false` | OC claims operational framing only, not replacement physics. | predictive_log_loss=0.693147, calibration_error=0.0, baseline_advantage_delta=0.0 |
| `stern_gerlach_toy` | `false` | Support ceiling remains S2/S3 formal toy. | calibration_error=0.01, stability_score=0.74, baseline_advantage_delta=-0.01 |
| `povm_instrument` | `false` | Physical branch must be instrument-compatible. | robustness_score=0.81, no_signalling_violation_score=0.0, baseline_advantage_delta=0.0 |
| `continuous_measurement` | `false` | OC can encode stabilization traces without claiming a new physical dynamics. | trajectory_error=0.01, stabilization_gain=0.17, baseline_advantage_delta=-0.01 |
| `decoherence_pointer_basis` | `false` | Pointer-basis language is operationally aligned, not promoted as a replacement theory. | off_diagonal_decay_error=0.01, pointer_basis_agreement=0.98, baseline_advantage_delta=-0.01 |
| `entanglement_no_signalling` | `false` | No forbidden signalling effect is claimed or produced. | no_signalling_violation_score=0.0, falsifier_fail_rate=0.0, baseline_advantage_delta=0.0 |
| `multi_observer_objectivity` | `false` | ObjectivityMetric is admitted as a bounded agreement metric with explicit bias falsifier. | objectivity_metric_c_r=0.999895, mean_js_divergence=0.000105, baseline_advantage_delta=0.0 |
| `architecture_perturbation` | `false` | ArchitecturePerturbation is admitted as a robustness test, not as proof of universal optimality. | architecture_stability=0.8, perturbed_decision_delta=0.2, baseline_advantage_delta=0.0 |
| `cognitive_order_effect` | `false` | Cognitive order effects are represented as bounded architecture-sensitive update traces. | order_effect_l1=0.0, stability_score=1.0, baseline_advantage_delta=0.0 |
