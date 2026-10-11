import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-! Contractive task-relative autofocus with an explicit quadratic quality proxy.
The proxy is a local algebraic contract, not a global controller claim. -/

def tomographicFocusUpdate (optimum gain current : ℝ) : ℝ :=
  optimum + gain * (current - optimum)

theorem tomographicFocusUpdate_error
    (optimum gain current : ℝ) :
    tomographicFocusUpdate optimum gain current - optimum =
      gain * (current - optimum) := by
  unfold tomographicFocusUpdate
  ring

theorem tomographicFocusUpdate_fixed_point
    (optimum gain : ℝ) :
    tomographicFocusUpdate optimum gain optimum = optimum := by
  simp [tomographicFocusUpdate]

theorem tomographicFocusUpdate_abs_error_contract
    (optimum gain current : ℝ)
    (gain_nonnegative : 0 ≤ gain)
    (gain_below_one : gain < 1)
    (current_ne_optimum : current ≠ optimum) :
    |tomographicFocusUpdate optimum gain current - optimum| <
      |current - optimum| := by
  have error_positive : 0 < |current - optimum| :=
    abs_pos.mpr (sub_ne_zero.mpr current_ne_optimum)
  rw [tomographicFocusUpdate_error, abs_mul, abs_of_nonneg gain_nonnegative]
  simpa using (mul_lt_mul_of_pos_right gain_below_one error_positive)

def tomographicFocusQuadraticRisk
    (optimum curvature focus : ℝ) : ℝ :=
  curvature * (focus - optimum) ^ 2

theorem tomographicFocusQuadraticRisk_nonnegative
    (optimum curvature focus : ℝ) (curvature_nonnegative : 0 ≤ curvature) :
    0 ≤ tomographicFocusQuadraticRisk optimum curvature focus := by
  exact mul_nonneg curvature_nonnegative (sq_nonneg _)

theorem tomographicFocusUpdate_quadratic_risk_identity
    (optimum gain current curvature : ℝ) :
    tomographicFocusQuadraticRisk optimum curvature
        (tomographicFocusUpdate optimum gain current) =
      gain ^ 2 * tomographicFocusQuadraticRisk optimum curvature current := by
  unfold tomographicFocusQuadraticRisk
  rw [tomographicFocusUpdate_error]
  ring

/-- Under positive curvature and a contractive nonnegative gain, a non-fixed
focus has strictly smaller quadratic risk after one update. -/
theorem tomographicFocusUpdate_quadratic_risk_strict_decrease
    (optimum gain current curvature : ℝ)
    (curvature_positive : 0 < curvature)
    (gain_nonnegative : 0 ≤ gain)
    (gain_below_one : gain < 1)
    (current_ne_optimum : current ≠ optimum) :
    tomographicFocusQuadraticRisk optimum curvature
        (tomographicFocusUpdate optimum gain current) <
      tomographicFocusQuadraticRisk optimum curvature current := by
  have error_nonzero : current - optimum ≠ 0 :=
    sub_ne_zero.mpr current_ne_optimum
  have current_risk_positive :
      0 < tomographicFocusQuadraticRisk optimum curvature current := by
    unfold tomographicFocusQuadraticRisk
    exact mul_pos curvature_positive (sq_pos_of_ne_zero error_nonzero)
  have gain_square_lt_one : gain ^ 2 < 1 := by
    nlinarith
  rw [tomographicFocusUpdate_quadratic_risk_identity]
  nlinarith

/-! A finite trajectory makes the controller contract explicit without
claiming an asymptotic or global optimisation result. -/

/-- Repeated application of the declared focus update. -/
def tomographicFocusTrajectory
    (optimum gain initial : ℝ) : ℕ → ℝ
  | 0 => initial
  | steps + 1 =>
      tomographicFocusUpdate optimum gain
        (tomographicFocusTrajectory optimum gain initial steps)

/-- Exact finite-horizon focus-error formula for the contractive update. -/
theorem tomographicFocusTrajectory_error
    (optimum gain initial : ℝ) (steps : ℕ) :
    tomographicFocusTrajectory optimum gain initial steps - optimum =
      gain ^ steps * (initial - optimum) := by
  induction steps with
  | zero => simp [tomographicFocusTrajectory]
  | succ steps ih =>
      change tomographicFocusUpdate optimum gain
          (tomographicFocusTrajectory optimum gain initial steps) - optimum =
        gain ^ (steps + 1) * (initial - optimum)
      rw [tomographicFocusUpdate_error, ih, pow_succ]
      ring

/-- With zero gain, every positive finite trajectory reaches the declared
optimum exactly.  This is a finite identity, not a general convergence claim.
-/
theorem tomographicFocusTrajectory_zero_gain_after_positive_steps
    (optimum initial : ℝ) (steps : ℕ)
    (positive_steps : 0 < steps) :
    tomographicFocusTrajectory optimum 0 initial steps = optimum := by
  have error_zero :
      tomographicFocusTrajectory optimum 0 initial steps - optimum = 0 := by
    rw [tomographicFocusTrajectory_error]
    simp [zero_pow (Nat.ne_of_gt positive_steps)]
  exact sub_eq_zero.mp error_zero

/-- A gain in the closed unit interval keeps every finite focus iterate inside
the interval containing both the initial setting and the declared optimum. -/
theorem tomographicFocusTrajectory_interval_invariant
    (lower upper optimum gain initial : ℝ)
    (lower_le_upper : lower ≤ upper)
    (optimum_in_interval : lower ≤ optimum ∧ optimum ≤ upper)
    (initial_in_interval : lower ≤ initial ∧ initial ≤ upper)
    (gain_nonnegative : 0 ≤ gain)
    (gain_le_one : gain ≤ 1) :
    ∀ steps, lower ≤ tomographicFocusTrajectory optimum gain initial steps ∧
      tomographicFocusTrajectory optimum gain initial steps ≤ upper := by
  intro steps
  induction steps with
  | zero => exact initial_in_interval
  | succ steps ih =>
      have one_minus_gain_nonnegative : 0 ≤ 1 - gain :=
        sub_nonneg.mpr gain_le_one
      have update_as_combo :
          tomographicFocusUpdate optimum gain
              (tomographicFocusTrajectory optimum gain initial steps) =
            (1 - gain) * optimum +
              gain * tomographicFocusTrajectory optimum gain initial steps := by
        unfold tomographicFocusUpdate
        ring
      change lower ≤ tomographicFocusUpdate optimum gain
          (tomographicFocusTrajectory optimum gain initial steps) ∧
        tomographicFocusUpdate optimum gain
          (tomographicFocusTrajectory optimum gain initial steps) ≤ upper
      rw [update_as_combo]
      constructor
      · calc
          lower = (1 - gain) * lower + gain * lower := by ring
          _ ≤ (1 - gain) * optimum +
              gain * tomographicFocusTrajectory optimum gain initial steps := by
            exact add_le_add
              (mul_le_mul_of_nonneg_left optimum_in_interval.1
                one_minus_gain_nonnegative)
              (mul_le_mul_of_nonneg_left ih.1 gain_nonnegative)
      · calc
          (1 - gain) * optimum +
              gain * tomographicFocusTrajectory optimum gain initial steps ≤
              (1 - gain) * upper + gain * upper := by
            exact add_le_add
              (mul_le_mul_of_nonneg_left optimum_in_interval.2
                one_minus_gain_nonnegative)
              (mul_le_mul_of_nonneg_left ih.2 gain_nonnegative)
          _ = upper := by ring

end OCKIndividuationMSpaceComposition