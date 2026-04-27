# OC Core 1.4 Observation Architecture

`A=(input_channels, transformation_stack, memory_state, noise_model, threshold_policy, decision_rule, feedback_rule, calibration_profile, cost_constraints, reference_class)`.

Quantum branch:
- `A -> I_A={I_y^A}_y`;
- `I_y^A` is a completely positive map;
- `sum_y I_y^A` is trace-preserving;
- `p(y|rho,A)=Tr[I_y^A(rho)]`;
- `rho_y=I_y^A(rho)/p(y|rho,A)`.

Cognition/AI branch:
- `A -> U_A(y,h_t,s_t)`;
- `p(y|s_t,A)` is an observation likelihood;
- `s_{t+1}=U_A(s_t,y,h_t)`;
- `E_t=decision_rule_A(h_t,s_t)`.
