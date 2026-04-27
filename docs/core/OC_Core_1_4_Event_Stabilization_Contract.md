# OC Core 1.4 Event Stabilization Contract

`Stability_A(E|H_t,R)=F(persistence, robustness, interobserver_agreement, predictive_gain, compression_gain, actionability)`.

`Fact_A,R(E,t) := Stability_A(E|H_t,R) >= tau_A,R AND no_active_falsifier(E,A,R)`.

Agreement:
`C_R(E)=1-mean_{i,j in R} D(P_i(E),P_j(E))`.

Allowed distances include total variation, KL/JS, Wasserstein, Bures/Fidelity, and task-specific regret.
