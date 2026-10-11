import OCKIndividuationMSpaceComposition.TomographicProjectionMatrix
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite regularized reconstruction objective

Tomographic inversion is often posed as a trade-off between a projection
residual and an explicit prior/complexity penalty.  This module records that
trade-off as a finite, source-level contract.  It proves only the elementary
order properties needed by an admission layer: nonnegative parameters yield a
nonnegative objective, zero regularization recovers the residual energy, and
increasing the parameter cannot decrease the objective for a fixed candidate.
No minimizer, uniqueness, convexity, or scientific validity is inferred here.
-/

section Regularization

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View] [DecidableEq View]

/-- A finite Tikhonov-style objective for a candidate state. -/
def tomographicRegularizedObjective
    (rows : View → Coordinate → ℝ)
    (target state : Coordinate → ℝ)
    (regularization : ℝ) : ℝ :=
  tomographicNormalEnergy rows (fun coordinate =>
    state coordinate - target coordinate) +
    regularization * tomographicEnergy state

theorem tomographicRegularizedObjective_nonnegative
    (rows : View → Coordinate → ℝ)
    (target state : Coordinate → ℝ)
    (regularization : ℝ)
    (regularization_nonnegative : 0 ≤ regularization) :
    0 ≤ tomographicRegularizedObjective rows target state regularization := by
  unfold tomographicRegularizedObjective
  exact add_nonneg
    (tomographicNormalEnergy_nonnegative rows
      (fun coordinate => state coordinate - target coordinate))
    (mul_nonneg regularization_nonnegative (tomographicEnergy_nonnegative state))

theorem tomographicRegularizedObjective_zero_parameter
    (rows : View → Coordinate → ℝ)
    (target state : Coordinate → ℝ) :
    tomographicRegularizedObjective rows target state 0 =
      tomographicNormalEnergy rows (fun coordinate =>
        state coordinate - target coordinate) := by
  simp [tomographicRegularizedObjective]

theorem tomographicRegularizedObjective_mono_parameter
    (rows : View → Coordinate → ℝ)
    (target state : Coordinate → ℝ)
    (first second : ℝ)
    (parameter_order : first ≤ second) :
    tomographicRegularizedObjective rows target state first ≤
      tomographicRegularizedObjective rows target state second := by
  unfold tomographicRegularizedObjective
  exact add_le_add (le_refl _)
    (mul_le_mul_of_nonneg_right parameter_order
      (tomographicEnergy_nonnegative state))

theorem tomographicRegularizedObjective_parameter_gap
    (rows : View → Coordinate → ℝ)
    (target state : Coordinate → ℝ)
    (first second : ℝ) :
    tomographicRegularizedObjective rows target state second -
        tomographicRegularizedObjective rows target state first =
      (second - first) * tomographicEnergy state := by
  unfold tomographicRegularizedObjective
  ring

theorem tomographicRegularizedObjective_strict_mono_parameter
    (rows : View → Coordinate → ℝ)
    (target state : Coordinate → ℝ)
    (first second : ℝ)
    (parameter_order : first < second)
    (state_energy_positive : 0 < tomographicEnergy state) :
    tomographicRegularizedObjective rows target state first <
      tomographicRegularizedObjective rows target state second := by
  apply sub_pos.mp
  rw [tomographicRegularizedObjective_parameter_gap]
  exact mul_pos (sub_pos.mpr parameter_order) state_energy_positive

theorem tomographicRegularizedObjective_parameter_invariant_of_zero_energy
    (rows : View → Coordinate → ℝ)
    (target state : Coordinate → ℝ)
    (first second : ℝ)
    (state_energy_zero : tomographicEnergy state = 0) :
    tomographicRegularizedObjective rows target state first =
      tomographicRegularizedObjective rows target state second := by
  unfold tomographicRegularizedObjective
  simp [state_energy_zero]

end Regularization

end OCKIndividuationMSpaceComposition
