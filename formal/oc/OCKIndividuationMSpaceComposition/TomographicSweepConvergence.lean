import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Conditional finite-sweep convergence envelope

The row-action layer proves exact one-step identities but does not assume that
successive rows cover every task-relevant direction.  This module isolates the
additional contract needed for a finite geometric envelope: every step must
obey the same nonnegative contraction factor.  The result is conditional and
finite-horizon; it is not a coverage theorem, a schedule-optimality theorem,
or a claim about a numerical implementation.
-/

/-- A declared per-step contraction of a nonnegative error sequence. -/
def TomographicSweepContraction
    (error : ℕ → ℝ)
    (factor : ℝ) : Prop :=
  (∀ step, 0 ≤ error step) ∧
    (∀ step, error (step + 1) ≤ factor * error step)

/-- A finite sweep obeying a uniform contraction has a geometric error bound. -/
theorem tomographicSweep_error_geometric_bound
    (error : ℕ → ℝ)
    (factor : ℝ)
    (factor_nonnegative : 0 ≤ factor)
    (contraction : TomographicSweepContraction error factor) :
    ∀ steps, error steps ≤ factor ^ steps * error 0 := by
  intro steps
  induction steps with
  | zero => simp
  | succ steps ih =>
      calc
        error (steps + 1) ≤ factor * error steps :=
          contraction.2 steps
        _ ≤ factor * (factor ^ steps * error 0) := by
          exact mul_le_mul_of_nonneg_left ih factor_nonnegative
        _ = factor ^ (steps + 1) * error 0 := by
          rw [pow_succ]
          ring

/-- The zero-factor special case reaches zero after one contracted step. -/
theorem tomographicSweep_zero_factor_step
    (error : ℕ → ℝ)
    (contraction : TomographicSweepContraction error 0) :
    ∀ steps, 0 < steps → error steps ≤ 0 := by
  intro steps positive
  have bound := tomographicSweep_error_geometric_bound error 0 (by exact le_refl 0)
    contraction steps
  have power_zero : (0 : ℝ) ^ steps = 0 :=
    zero_pow (Nat.ne_of_gt positive)
  simpa [power_zero] using bound

end OCKIndividuationMSpaceComposition