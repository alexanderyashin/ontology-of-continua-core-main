import OCKIndividuationMSpaceComposition.TomographicAutofocus
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Bounded-noise autofocus envelope

This is the smallest robust extension of the deterministic focus update.  A
declared additive disturbance is propagated explicitly, and an invariant error
tube is proved under a gain and disturbance budget.  The result is a bounded
control contract only: it does not identify a physical contrast function,
prove global optimization, or estimate the disturbance from data.
-/

section NoisyAutofocus

def tomographicNoisyFocusUpdate
    (optimum gain current disturbance : ℝ) : ℝ :=
  optimum + gain * (current - optimum) + disturbance

theorem tomographicNoisyFocusUpdate_error
    (optimum gain current disturbance : ℝ) :
    tomographicNoisyFocusUpdate optimum gain current disturbance - optimum =
      gain * (current - optimum) + disturbance := by
  unfold tomographicNoisyFocusUpdate
  ring

theorem tomographicNoisyFocusUpdate_abs_error_bound
    (optimum gain current disturbance : ℝ)
    (gain_nonnegative : 0 ≤ gain) :
    |tomographicNoisyFocusUpdate optimum gain current disturbance - optimum| ≤
      gain * |current - optimum| + |disturbance| := by
  rw [tomographicNoisyFocusUpdate_error]
  calc
    |gain * (current - optimum) + disturbance| ≤
        |gain * (current - optimum)| + |disturbance| := abs_add_le _ _
    _ = gain * |current - optimum| + |disturbance| := by
      rw [abs_mul, abs_of_nonneg gain_nonnegative]

theorem tomographicNoisyFocusUpdate_error_tube_invariant
    (optimum gain current disturbance radius : ℝ)
    (gain_nonnegative : 0 ≤ gain)
    (gain_at_most_one : gain ≤ 1)
    (radius_nonnegative : 0 ≤ radius)
    (current_in_tube : |current - optimum| ≤ radius)
    (disturbance_budget : |disturbance| ≤ (1 - gain) * radius) :
    |tomographicNoisyFocusUpdate optimum gain current disturbance - optimum| ≤
      radius := by
  calc
    |tomographicNoisyFocusUpdate optimum gain current disturbance - optimum| ≤
        gain * |current - optimum| + |disturbance| :=
      tomographicNoisyFocusUpdate_abs_error_bound optimum gain current disturbance
        gain_nonnegative
    _ ≤ gain * radius + |disturbance| := by
      simpa using (add_le_add_right
        (mul_le_mul_of_nonneg_left current_in_tube gain_nonnegative)
        |disturbance|)
    _ ≤ gain * radius + (1 - gain) * radius :=
      by
        simpa [add_comm] using
          (add_le_add_left disturbance_budget (gain * radius))
    _ = radius := by ring

end NoisyAutofocus

end OCKIndividuationMSpaceComposition
