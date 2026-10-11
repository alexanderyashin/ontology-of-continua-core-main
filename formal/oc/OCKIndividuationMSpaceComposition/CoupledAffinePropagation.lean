import Mathlib.Algebra.Group.Hom.End
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Abel
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

/-!
Exact finite-horizon propagation for a coupled affine discrete system.

The state type is intentionally abstract.  A vector, a service graph, a field
discretisation, or a collection of K-level observables becomes a domain model
only after supplying an additive state space, a coupling endomorphism, and an
explicit forcing term.
-/

variable {X : Type*} [AddCommGroup X]

/-- `x(t+1) = A x(t) + b`, with all coupling concentrated in `A`. -/
def coupledAffineTrajectory (A : X →+ X) (b x0 : X) : ℕ → X
  | 0 => x0
  | t + 1 => A (coupledAffineTrajectory A b x0 t) + b

@[simp] theorem coupledAffineTrajectory_zero
    (A : X →+ X) (b x0 : X) :
    coupledAffineTrajectory A b x0 0 = x0 := rfl

@[simp] theorem coupledAffineTrajectory_succ
    (A : X →+ X) (b x0 : X) (t : ℕ) :
    coupledAffineTrajectory A b x0 (t + 1) =
      A (coupledAffineTrajectory A b x0 t) + b := rfl

/-- The exact finite-horizon homogeneous propagation operator `P_t(A)`. -/
def couplingPower (A : X →+ X) : ℕ → X →+ X
  | 0 => AddMonoidHom.id X
  | t + 1 => A.comp (couplingPower A t)

/-- The exact accumulated affine forcing, defined without any convergence assumption. -/
def accumulatedCouplingForcing (A : X →+ X) (b : X) : ℕ → X
  | 0 => 0
  | t + 1 => A (accumulatedCouplingForcing A b t) + b

/-- Exact state decomposition `x_t = P_t(A) x_0 + g_t(A,b)`. -/
theorem coupledAffineTrajectory_exact_decomposition
    (A : X →+ X) (b x0 : X) (horizon : ℕ) :
    coupledAffineTrajectory A b x0 horizon =
      couplingPower A horizon x0 +
        accumulatedCouplingForcing A b horizon := by
  induction horizon with
  | zero => simp [coupledAffineTrajectory, couplingPower,
      accumulatedCouplingForcing]
  | succ horizon ih =>
      simp only [coupledAffineTrajectory_succ, couplingPower,
        accumulatedCouplingForcing, AddMonoidHom.comp_apply]
      rw [ih, A.map_add]
      abel

/-- With no forcing, the trajectory is exactly the propagated initial state. -/
theorem coupledAffineTrajectory_zero_forcing_eq_power
    (A : X →+ X) (x0 : X) (horizon : ℕ) :
    coupledAffineTrajectory A 0 x0 horizon =
      couplingPower A horizon x0 := by
  rw [coupledAffineTrajectory_exact_decomposition]
  have forcingZero : accumulatedCouplingForcing A 0 horizon = 0 := by
    induction horizon with
    | zero => rfl
    | succ horizon ih => simp [accumulatedCouplingForcing, ih]
  simp [forcingZero]

/--
Exact intervention law: under common forcing, the counterfactual difference
obeys the homogeneous coupled dynamics.  Thus an intervention `delta` has
finite-horizon effect obtained by iterating the same coupling operator.
-/
theorem coupledAffineTrajectory_initial_difference
    (A : X →+ X) (b first second : X) (horizon : ℕ) :
    coupledAffineTrajectory A b first horizon -
        coupledAffineTrajectory A b second horizon =
      coupledAffineTrajectory A 0 (first - second) horizon := by
  induction horizon with
  | zero => simp
  | succ horizon ih =>
      simp only [coupledAffineTrajectory_succ]
      calc
        (A (coupledAffineTrajectory A b first horizon) + b) -
            (A (coupledAffineTrajectory A b second horizon) + b) =
            A (coupledAffineTrajectory A b first horizon) -
              A (coupledAffineTrajectory A b second horizon) := by abel
        _ = A (coupledAffineTrajectory A b first horizon -
              coupledAffineTrajectory A b second horizon) := by
              rw [A.map_sub]
        _ = A (coupledAffineTrajectory A 0 (first - second) horizon) := by
              rw [ih]
        _ = A (coupledAffineTrajectory A 0 (first - second) horizon) + 0 := by
              simp

/-- Closed counterfactual form: `Delta x_t = P_t(A) Delta x_0`. -/
theorem coupledAffineTrajectory_initial_difference_eq_power
    (A : X →+ X) (b first second : X) (horizon : ℕ) :
    coupledAffineTrajectory A b first horizon -
        coupledAffineTrajectory A b second horizon =
      couplingPower A horizon (first - second) := by
  rw [coupledAffineTrajectory_initial_difference,
    coupledAffineTrajectory_zero_forcing_eq_power]

/-- Full affine superposition for simultaneous changes in initial state and forcing. -/
theorem coupledAffineTrajectory_full_difference
    (A : X →+ X) (firstForcing secondForcing first second : X)
    (horizon : ℕ) :
    coupledAffineTrajectory A firstForcing first horizon -
        coupledAffineTrajectory A secondForcing second horizon =
      coupledAffineTrajectory A (firstForcing - secondForcing)
        (first - second) horizon := by
  induction horizon with
  | zero => simp
  | succ horizon ih =>
      simp only [coupledAffineTrajectory_succ]
      calc
        (A (coupledAffineTrajectory A firstForcing first horizon) + firstForcing) -
            (A (coupledAffineTrajectory A secondForcing second horizon) +
              secondForcing) =
            (A (coupledAffineTrajectory A firstForcing first horizon) -
              A (coupledAffineTrajectory A secondForcing second horizon)) +
              (firstForcing - secondForcing) := by abel
        _ = A (coupledAffineTrajectory A firstForcing first horizon -
              coupledAffineTrajectory A secondForcing second horizon) +
              (firstForcing - secondForcing) := by
              rw [A.map_sub]
        _ = A (coupledAffineTrajectory A (firstForcing - secondForcing)
              (first - second) horizon) +
              (firstForcing - secondForcing) := by
              rw [ih]

/-- Every coupling produces the zero trajectory from zero without forcing. -/
theorem coupledAffineTrajectory_zero_state
    (A : X →+ X) (horizon : ℕ) :
    coupledAffineTrajectory A 0 0 horizon = 0 := by
  induction horizon with
  | zero => rfl
  | succ horizon ih => simp [coupledAffineTrajectory, ih]

/-- Two couplings agree on a declared set of intervention probes. -/
def CouplingProbeAgreement
    (probes : Set X) (A B : X →+ X) : Prop :=
  ∀ x, x ∈ probes → A x = B x

/-- A probe family is complete exactly when its one-step responses identify every coupling. -/
def CouplingProbeComplete (probes : Set X) : Prop :=
  ∀ A B : X →+ X, CouplingProbeAgreement probes A B → A = B

/-- A nonzero coupling perturbation that is invisible on every declared probe. -/
def InvisibleCouplingPerturbation
    (probes : Set X) (delta : X →+ X) : Prop :=
  delta ≠ 0 ∧ ∀ x, x ∈ probes → delta x = 0

/--
No-go theorem with a constructive repair condition: an invisible nonzero
perturbation makes `A` and `A + delta` observationally identical on the probe
set, although they are different operators.  Coupling identification therefore
requires a probe-complete design, not merely more repetitions of the same
unexciting trajectory.
-/
theorem invisibleCouplingPerturbation_blocks_identification
    (probes : Set X) (A delta : X →+ X)
    (invisible : InvisibleCouplingPerturbation probes delta) :
    CouplingProbeAgreement probes A (A + delta) ∧ A ≠ A + delta := by
  constructor
  · intro x observed
    simp [invisible.2 x observed]
  · intro equalOperators
    apply invisible.1
    ext x
    have atX := DFunLike.congr_fun equalOperators x
    have zeroAtX : (0 : X) = delta x := by
      simpa using congrArg (fun z : X => z - A x) atX
    exact zeroAtX.symm

/-- Probe completeness is sufficient for exact operator identification. -/
theorem coupling_eq_of_probe_complete
    (probes : Set X) (complete : CouplingProbeComplete probes)
    (A B : X →+ X) (agreement : CouplingProbeAgreement probes A B) :
    A = B :=
  complete A B agreement

/--
Reachable-state sufficiency: if two operators take the same step on every state
actually reached by the first system, their trajectories are identical.  This
also exposes the observational boundary: values off the reachable set are not
tested by that trajectory.
-/
theorem coupledAffineTrajectory_eq_of_reachable_step_agreement
    (A B : X →+ X) (b x0 : X)
    (agreement : ∀ t, A (coupledAffineTrajectory A b x0 t) =
      B (coupledAffineTrajectory A b x0 t)) :
    ∀ t, coupledAffineTrajectory A b x0 t =
      coupledAffineTrajectory B b x0 t := by
  intro t
  induction t with
  | zero => rfl
  | succ t ih =>
      rw [coupledAffineTrajectory_succ, coupledAffineTrajectory_succ,
        agreement t, ih]

/--
Concrete global no-go: the zero and identity couplings are different on `ℚ`,
yet the entire passive zero trajectory is identical at every horizon.
-/
theorem passive_zero_trajectory_does_not_identify_coupling :
    ∃ A B : ℚ →+ ℚ,
      A ≠ B ∧
      ∀ horizon,
        coupledAffineTrajectory A 0 0 horizon =
          coupledAffineTrajectory B 0 0 horizon := by
  refine ⟨0, AddMonoidHom.id ℚ, ?_, ?_⟩
  · intro equalOperators
    have atOne := DFunLike.congr_fun equalOperators (1 : ℚ)
    norm_num at atOne
  · intro horizon
    rw [coupledAffineTrajectory_zero_state,
      coupledAffineTrajectory_zero_state]

end OCKIndividuationMSpaceComposition
