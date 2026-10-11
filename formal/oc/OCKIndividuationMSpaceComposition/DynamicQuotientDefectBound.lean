import OCKIndividuationMSpaceComposition.OpenDiscreteDynamics

namespace OCKIndividuationMSpaceComposition

/-!
Quantitative extension of the deterministic quotient boundary.  This module
proves a transition-perturbation theorem: an implementation may differ from a
contractive reference transition by a declared one-step defect, and that local
defect yields a finite-horizon operational forecast envelope.  The theorem is
not, by itself, a structural quotient theorem: a quotient/fibre residual must
be connected to this transition premise by an explicit observation map and
representative/section contract (see `QuotientTransitionDefectBridge`).  No
hidden stochastic or oracle premise is smuggled into the bound.
-/

/-- Uniform one-step discrepancy of an approximate transition from a reference. -/
def UniformTransitionDefect
    (reference approximate : ℚ → ℚ) (defect : ℚ) : Prop :=
  ∀ state, |approximate state - reference state| ≤ defect

/-!
If the reference transition is contractive and the approximate transition has
uniform defect `defect`, the two finite trajectories starting at the same state
are separated by the robust envelope with zero initial error.  This is the
explicit transition-perturbation law; it becomes an approximate task-quotient
forecast only after the separate structural bridge has been registered.
-/
theorem approximate_transition_error_bound
    (reference approximate : ℚ → ℚ) (rho defect : ℚ)
    (rhoNonnegative : 0 ≤ rho)
    (contractive : IsContraction rho reference)
    (defectBound : UniformTransitionDefect reference approximate defect)
    (horizon : ℕ) (initial : ℚ) :
    |iterateState approximate horizon initial -
        iterateState reference horizon initial| ≤
      robustErrorEnvelope rho defect 0 horizon := by
  induction horizon with
  | zero =>
      simp [iterateState, robustErrorEnvelope]
  | succ horizon ih =>
      have triangle :
          |approximate (iterateState approximate horizon initial) -
              reference (iterateState reference horizon initial)| ≤
            |reference (iterateState approximate horizon initial) -
                reference (iterateState reference horizon initial)| +
              |approximate (iterateState approximate horizon initial) -
                reference (iterateState approximate horizon initial)| := by
        rw [show
          approximate (iterateState approximate horizon initial) -
              reference (iterateState reference horizon initial) =
            (reference (iterateState approximate horizon initial) -
              reference (iterateState reference horizon initial)) +
            (approximate (iterateState approximate horizon initial) -
              reference (iterateState approximate horizon initial)) by ring]
        exact abs_add_le _ _
      calc
        |iterateState approximate (horizon + 1) initial -
            iterateState reference (horizon + 1) initial| =
            |approximate (iterateState approximate horizon initial) -
              reference (iterateState reference horizon initial)| := by rfl
        _ ≤ |reference (iterateState approximate horizon initial) -
              reference (iterateState reference horizon initial)| +
            |approximate (iterateState approximate horizon initial) -
              reference (iterateState approximate horizon initial)| := triangle
        _ ≤ rho * |iterateState approximate horizon initial -
              iterateState reference horizon initial| + defect := by
          exact add_le_add (contractive _ _)
            (defectBound (iterateState approximate horizon initial))
        _ ≤ rho * robustErrorEnvelope rho defect 0 horizon + defect := by
          simpa [add_comm, add_left_comm, add_assoc] using
            (add_le_add_right (mul_le_mul_of_nonneg_left ih rhoNonnegative) defect)
        _ = robustErrorEnvelope rho defect 0 (horizon + 1) := by rfl

/-- The zero-initial-error envelope has the closed finite geometric form. -/
theorem zero_initial_error_envelope_eq_geometric_sum
    (rho defect : ℚ) (horizon : ℕ) :
    robustErrorEnvelope rho defect 0 horizon =
      defect * (∑ k ∈ Finset.range horizon, rho ^ k) := by
  rw [robustErrorEnvelope_eq_geometric_sum]
  ring

/-- Under `0 ≤ rho < 1`, approximate quotient error reaches a finite plateau. -/
theorem approximate_transition_error_le_plateau
    (reference approximate : ℚ → ℚ) (rho defect : ℚ)
    (rhoNonnegative : 0 ≤ rho)
    (rhoLessThanOne : rho < 1)
    (contractive : IsContraction rho reference)
    (defectNonnegative : 0 ≤ defect)
    (defectBound : UniformTransitionDefect reference approximate defect)
    (horizon : ℕ) (initial : ℚ) :
    |iterateState approximate horizon initial -
        iterateState reference horizon initial| ≤ defect / (1 - rho) := by
  have envelope := approximate_transition_error_bound reference approximate rho defect
    rhoNonnegative contractive defectBound horizon initial
  calc
    |iterateState approximate horizon initial -
        iterateState reference horizon initial| ≤
        robustErrorEnvelope rho defect 0 horizon := envelope
    _ ≤ 0 + defect / (1 - rho) :=
      robustErrorEnvelope_le_contracting_plateau rho defect 0
        rhoNonnegative rhoLessThanOne defectNonnegative (by norm_num) horizon
    _ = defect / (1 - rho) := by ring

end OCKIndividuationMSpaceComposition
