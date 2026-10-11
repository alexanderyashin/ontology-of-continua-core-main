import OCKIndividuationMSpaceComposition.TomographicProjectionMatrix
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Certified inverse / filtered-backprojection boundary

A filtered backprojection or normal-equation solver earns an exact
reconstruction claim only when its operator is supplied with a left-inverse
certificate for the declared finite projection map.  The certificate below is
an explicit contract: it does not construct the inverse, select a filter,
prove conditioning, or infer completeness from a small residual.
-/

section InverseCertificate

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View]

structure TomographicLeftInverse
    (rows : View → Coordinate → ℝ) where
  reconstruct : (View → ℝ) → Coordinate → ℝ
  left_inverse : ∀ state,
    reconstruct (tomographicProjection rows state) = state

theorem tomographicLeftInverse_reconstruct_exact
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicLeftInverse rows)
    (state : Coordinate → ℝ) :
    certificate.reconstruct (tomographicProjection rows state) = state :=
  certificate.left_inverse state

theorem tomographicProjection_injective_of_left_inverse
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicLeftInverse rows) :
    Function.Injective (tomographicProjection rows) := by
  intro left right same
  calc
    left = certificate.reconstruct (tomographicProjection rows left) :=
      (certificate.left_inverse left).symm
    _ = certificate.reconstruct (tomographicProjection rows right) :=
      congrArg certificate.reconstruct same
    _ = right := certificate.left_inverse right

theorem tomographicLeftInverse_unique_on_observations
    {rows : View → Coordinate → ℝ}
    (first second : TomographicLeftInverse rows)
    (state : Coordinate → ℝ) :
    first.reconstruct (tomographicProjection rows state) =
      second.reconstruct (tomographicProjection rows state) := by
  rw [first.left_inverse, second.left_inverse]

/-! A noisy inverse needs a separate continuity budget. -/

structure TomographicStableLeftInverse
    (rows : View → Coordinate → ℝ) where
  reconstruct : (View → ℝ) → Coordinate → ℝ
  left_inverse : ∀ state,
    reconstruct (tomographicProjection rows state) = state
  lipschitzConstant : ℝ
  lipschitz_nonnegative : 0 ≤ lipschitzConstant
  reconstruct_lipschitz : ∀ first second,
    dist (reconstruct first) (reconstruct second) ≤
      lipschitzConstant * dist first second

theorem tomographicStableInverse_error_bound
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicStableLeftInverse rows)
    (state : Coordinate → ℝ) (data : View → ℝ) (budget : ℝ)
    (measurementBound : dist data (tomographicProjection rows state) ≤ budget) :
    dist (certificate.reconstruct data) state ≤
      certificate.lipschitzConstant * budget := by
  calc
    dist (certificate.reconstruct data) state =
        dist (certificate.reconstruct data)
          (certificate.reconstruct (tomographicProjection rows state)) := by
      rw [certificate.left_inverse]
    _ ≤ certificate.lipschitzConstant *
        dist data (tomographicProjection rows state) :=
      certificate.reconstruct_lipschitz data
        (tomographicProjection rows state)
    _ ≤ certificate.lipschitzConstant * budget := by
      exact mul_le_mul_of_nonneg_left measurementBound
        certificate.lipschitz_nonnegative

end InverseCertificate

end OCKIndividuationMSpaceComposition