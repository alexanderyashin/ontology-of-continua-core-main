import OCKIndividuationMSpaceComposition.TomographicNormalOperator
import OCKIndividuationMSpaceComposition.TomographicInverseCertificate
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Filtered backprojection adapter

Filtered backprojection is represented as an explicitly registered view-space
filter followed by the existing finite adjoint.  The filter is not assumed to
be a physical ramp, Fourier multiplier, or inverse.  Exact reconstruction is
available only through the explicit certificate below, which is convertible to
the existing left-inverse contract.
-/


section FilteredBackprojection

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View] [DecidableEq View]

/-- A finite filter acting on the registered view/sinogram coordinates. -/
def tomographicFilterApply
    (filter : View → View → ℝ)
    (data : View → ℝ) : View → ℝ :=
  fun view => ∑ source, filter view source * data source

/-- Filtered backprojection: filter in view space, then apply the adjoint. -/
def tomographicFilteredBackprojection
    (rows : View → Coordinate → ℝ)
    (filter : View → View → ℝ)
    (data : View → ℝ) : Coordinate → ℝ :=
  tomographicBackprojection rows (tomographicFilterApply filter data)

theorem tomographicFilterApply_zero
    (filter : View → View → ℝ) :
    tomographicFilterApply filter (0 : View → ℝ) = 0 := by
  funext view
  simp [tomographicFilterApply]

theorem tomographicFilterApply_add
    (filter : View → View → ℝ)
    (left right : View → ℝ) :
    tomographicFilterApply filter (fun view => left view + right view) =
      fun view => tomographicFilterApply filter left view +
        tomographicFilterApply filter right view := by
  funext view
  simp [tomographicFilterApply, mul_add, Finset.sum_add_distrib]

theorem tomographicFilterApply_smul
    (filter : View → View → ℝ)
    (scalar : ℝ) (data : View → ℝ) :
    tomographicFilterApply filter (fun view => scalar * data view) =
      fun view => scalar * tomographicFilterApply filter data view := by
  funext view
  unfold tomographicFilterApply
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro source _
  ring

theorem tomographicFilteredBackprojection_zero_of_zero_data
    (rows : View → Coordinate → ℝ)
    (filter : View → View → ℝ)
    (data : View → ℝ)
    (zero_data : tomographicFilterApply filter data = 0) :
    tomographicFilteredBackprojection rows filter data = 0 := by
  unfold tomographicFilteredBackprojection
  exact tomographicBackprojection_zero_of_zero_residual rows _
    (fun view => congrFun zero_data view)

/-! A source-bound exactness receipt is the only route to inverse claims. -/

structure TomographicFilteredBackprojectionCertificate
    (rows : View → Coordinate → ℝ) where
  filter : View → View → ℝ
  exact_reconstruction : ∀ state,
    tomographicFilteredBackprojection rows filter
        (tomographicProjection rows state) = state

def tomographicFilteredBackprojectionCertificate_as_left_inverse
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFilteredBackprojectionCertificate rows) :
    TomographicLeftInverse rows :=
  { reconstruct := tomographicFilteredBackprojection rows certificate.filter
    left_inverse := certificate.exact_reconstruction }

theorem tomographicFilteredBackprojection_exact
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFilteredBackprojectionCertificate rows)
    (state : Coordinate → ℝ) :
    tomographicFilteredBackprojection rows certificate.filter
        (tomographicProjection rows state) = state :=
  certificate.exact_reconstruction state

theorem tomographicFilteredBackprojection_target_decoder_of_certificate
    {Answer : Type*}
    (certificate : TomographicFilteredBackprojectionCertificate rows)
    (target : (Coordinate → ℝ) → Answer) :
    ∃ decode : (View → ℝ) → Answer, ∀ state,
      decode (tomographicProjection rows state) = target state := by
  refine ⟨fun data => target
      (tomographicFilteredBackprojection rows certificate.filter data), ?_⟩
  intro state
  simp [certificate.exact_reconstruction]

end FilteredBackprojection

end OCKIndividuationMSpaceComposition
