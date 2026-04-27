# OC Core 1.4 Formal Spec

Status: `RC1_NO_SEND`.

## Core Objects

**State Space Omega.** A typed space of possible system, observer, and environment states used by a bounded observation architecture.

**ObservationArchitecture A.** A tuple
`A=(input_channels, transformation_stack, memory_state, noise_model, threshold_policy, decision_rule, feedback_rule, calibration_profile, cost_constraints, reference_class)`.

**ObservationOperation O_A.** An operation that maps state/history into an observation likelihood, output candidate, and update trace under architecture `A`.

**Event Candidate e.** A proposed stabilized output before fact status.

**Event History H_t.** The time-indexed evidence, decisions, updates, perturbations, and falsifier checks available before or at `t`.

**StabilizationFunctional S_A,R.** A bounded functional over persistence, robustness, interobserver agreement, predictive gain, compression gain, and actionability.

**FactContract F_A,R.** `Fact_A,R(E,t)` holds only when `Stability_A(E|H_t,R) >= tau_A,R` and no active falsifier is present.

**SupportClass SC(claim).** Each claim is labeled from S0 through S5 and cannot be worded above its class.

**Falsifier phi.** A condition that breaks a claim, lowers its class, or routes it to research obligation.

**ArchitecturePerturbation Pi(A).** A structured change to architecture `A` used to test robustness and overfit.

**ObjectivityMetric C_R.** `C_R(E)=1-mean_{i,j in R} D(P_i(E),P_j(E))`, where `D` may be TV, KL/JS, Wasserstein, Bures/Fidelity, or task-specific regret.

## Claim Ceiling

OC 1.4 is an operational framework for stabilized events/facts under bounded observation architectures. It does not replace quantum mechanics, prove physical collapse, or promote benchmark behavior into empirical physics without separate evidence.
