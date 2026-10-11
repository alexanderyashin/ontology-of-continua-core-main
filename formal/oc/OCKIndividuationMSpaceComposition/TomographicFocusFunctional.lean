import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Local focus-quality functional

This is a deliberately bounded mathematical counterpart of the physical
focus-error functional.  It gives the controller a declared local objective
and an auditable minimizer boundary; it does not claim that a measured image
contrast, phase score, or enterprise loss is quadratic without a calibration
receipt.
-/

/-- Quadratic local focus-risk around a declared optimum. -/
def tomographicQuadraticFocusError
    (curvature optimum setting : ℝ) : ℝ :=
  curvature * (setting - optimum) ^ 2

theorem tomographicQuadraticFocusError_nonnegative
    (curvature optimum setting : ℝ)
    (curvature_nonnegative : 0 ≤ curvature) :
    0 ≤ tomographicQuadraticFocusError curvature optimum setting := by
  unfold tomographicQuadraticFocusError
  exact mul_nonneg curvature_nonnegative (sq_nonneg _)

theorem tomographicQuadraticFocusError_at_optimum
    (curvature optimum : ℝ) :
    tomographicQuadraticFocusError curvature optimum optimum = 0 := by
  simp [tomographicQuadraticFocusError]

theorem tomographicQuadraticFocusError_minimizer
    (curvature optimum setting : ℝ)
    (curvature_nonnegative : 0 ≤ curvature) :
    tomographicQuadraticFocusError curvature optimum optimum ≤
      tomographicQuadraticFocusError curvature optimum setting := by
  rw [tomographicQuadraticFocusError_at_optimum]
  exact tomographicQuadraticFocusError_nonnegative curvature optimum setting
    curvature_nonnegative

theorem tomographicQuadraticFocusError_unique_minimizer
    (curvature optimum setting : ℝ)
    (curvature_positive : 0 < curvature)
    (equal_error :
      tomographicQuadraticFocusError curvature optimum optimum =
        tomographicQuadraticFocusError curvature optimum setting) :
    setting = optimum := by
  rw [tomographicQuadraticFocusError_at_optimum] at equal_error
  unfold tomographicQuadraticFocusError at equal_error
  have curvature_nonzero : curvature ≠ 0 := ne_of_gt curvature_positive
  have product_zero : curvature * (setting - optimum) ^ 2 = 0 :=
    equal_error.symm
  have square_zero : (setting - optimum) ^ 2 = 0 := by
    rcases mul_eq_zero.mp product_zero with curvature_zero | square_zero
    · exact False.elim (curvature_nonzero curvature_zero)
    · exact square_zero
  nlinarith

end OCKIndividuationMSpaceComposition