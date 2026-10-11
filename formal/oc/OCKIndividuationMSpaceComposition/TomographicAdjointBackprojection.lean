import OCKIndividuationMSpaceComposition.TomographicRowAction
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite adjoint/backprojection bridge

For a finite registered family of scalar rows, the backprojection is the
transpose (adjoint for the standard finite inner product). This is the algebraic
core behind filtered backprojection and normal-equation methods. It is only a
directional identity: it does not assert that the normal operator is invertible,
that a filter is unbiased, or that a small residual implies semantic recovery.
-/


section FiniteAdjoint

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View]

def tomographicInner (x y : Coordinate → ℝ) : ℝ :=
  ∑ coordinate, x coordinate * y coordinate

def tomographicBackprojection
    (rows : View → Coordinate → ℝ) (residual : View → ℝ) : Coordinate → ℝ :=
  fun coordinate => ∑ view, residual view * rows view coordinate

/-! A confidence-weighted adjoint keeps acquisition confidence inside the
    normal direction.  It is a finite algebraic adapter: weights are explicit
    inputs and are not interpreted as a calibrated probability or an inverse
    variance without an external contract. -/

def tomographicWeightedBackprojection
    (rows : View → Coordinate → ℝ)
    (weight residual : View → ℝ) : Coordinate → ℝ :=
  fun coordinate => ∑ view, weight view * residual view * rows view coordinate

theorem tomographicInner_nonnegative (x : Coordinate → ℝ) :
    0 ≤ tomographicInner x x := by
  simp only [tomographicInner]
  exact Finset.sum_nonneg (fun coordinate _ => by
    simpa [pow_two] using sq_nonneg (x coordinate))

/-- The finite backprojection is adjoint to the forward row map. -/
theorem tomographicBackprojection_adjoint
    (rows : View → Coordinate → ℝ) (residual : View → ℝ)
    (direction : Coordinate → ℝ) :
    tomographicInner (tomographicBackprojection rows residual) direction =
      ∑ view, residual view * tomographicDot (rows view) direction := by
  classical
  unfold tomographicInner tomographicBackprojection
  simp_rw [Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro view _
  calc
    (∑ coordinate, (residual view * rows view coordinate) * direction coordinate) =
        ∑ coordinate, residual view *
          (rows view coordinate * direction coordinate) := by
      apply Finset.sum_congr rfl
      intro coordinate _
      ring
    _ = residual view * ∑ coordinate,
        rows view coordinate * direction coordinate := by
      rw [Finset.mul_sum]

theorem tomographicWeightedBackprojection_adjoint
    (rows : View → Coordinate → ℝ) (weight residual : View → ℝ)
    (direction : Coordinate → ℝ) :
    tomographicInner
        (tomographicWeightedBackprojection rows weight residual) direction =
      ∑ view, weight view * residual view *
        tomographicDot (rows view) direction := by
  classical
  unfold tomographicInner tomographicWeightedBackprojection
  simp_rw [Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro view _
  calc
    (∑ coordinate,
        (weight view * residual view * rows view coordinate) *
          direction coordinate) =
        ∑ coordinate, (weight view * residual view) *
          (rows view coordinate * direction coordinate) := by
      apply Finset.sum_congr rfl
      intro coordinate _
      ring
    _ = (weight view * residual view) * ∑ coordinate,
        rows view coordinate * direction coordinate := by
      rw [Finset.mul_sum]

/-- Applying the adjoint to the vector of forward residuals yields a nonnegative
directional pairing with the current error; it is the sum of squared residuals.
This is a certificate for the linearized direction, not a convergence theorem. -/
theorem tomographicResidual_backprojection_energy
    (rows : View → Coordinate → ℝ) (error : Coordinate → ℝ) :
    tomographicInner
        (tomographicBackprojection rows
          (fun view => tomographicDot (rows view) error)) error =
      ∑ view, (tomographicDot (rows view) error) ^ 2 := by
  rw [tomographicBackprojection_adjoint]
  apply Finset.sum_congr rfl
  intro view _
  ring

theorem tomographicWeightedResidual_backprojection_energy
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (error : Coordinate → ℝ) :
    tomographicInner
        (tomographicWeightedBackprojection rows weight
          (fun view => tomographicDot (rows view) error)) error =
      ∑ view, weight view * (tomographicDot (rows view) error) ^ 2 := by
  rw [tomographicWeightedBackprojection_adjoint]
  apply Finset.sum_congr rfl
  intro view _
  ring

theorem tomographicWeightedResidual_backprojection_energy_nonnegative
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (error : Coordinate → ℝ)
    (weight_nonnegative : ∀ view, 0 ≤ weight view) :
    0 ≤ tomographicInner
        (tomographicWeightedBackprojection rows weight
          (fun view => tomographicDot (rows view) error)) error := by
  rw [tomographicWeightedResidual_backprojection_energy]
  exact Finset.sum_nonneg (fun view _ =>
    mul_nonneg (weight_nonnegative view) (sq_nonneg _))

theorem tomographicWeightedResidual_backprojection_energy_zero_iff
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (error : Coordinate → ℝ)
    (weight_nonnegative : ∀ view, 0 ≤ weight view) :
    tomographicInner
        (tomographicWeightedBackprojection rows weight
          (fun view => tomographicDot (rows view) error)) error = 0 ↔
      ∀ view, 0 < weight view →
        tomographicDot (rows view) error = 0 := by
  constructor
  · intro energyZero view weight_positive
    rw [tomographicWeightedResidual_backprojection_energy] at energyZero
    have termZero :
        weight view * (tomographicDot (rows view) error) ^ 2 = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedView selectedMem =>
        mul_nonneg (weight_nonnegative selectedView)
          (sq_nonneg (tomographicDot (rows selectedView) error)))).mp
        energyZero view (Finset.mem_univ view)
    have squareZero :
        (tomographicDot (rows view) error) ^ 2 = 0 :=
      (mul_eq_zero.mp termZero).resolve_left (ne_of_gt weight_positive)
    exact sq_eq_zero_iff.mp squareZero
  · intro agreement
    rw [tomographicWeightedResidual_backprojection_energy]
    apply (Finset.sum_eq_zero_iff_of_nonneg (fun view viewMem =>
      mul_nonneg (weight_nonnegative view)
        (sq_nonneg (tomographicDot (rows view) error)))).mpr
    intro view viewMem
    by_cases weight_positive : 0 < weight view
    · have dotZero := agreement view weight_positive
      simp [dotZero]
    · have weight_zero : weight view = 0 := le_antisymm
        (le_of_not_gt weight_positive) (weight_nonnegative view)
      simp [weight_zero]

theorem tomographicResidual_backprojection_energy_nonnegative
    (rows : View → Coordinate → ℝ) (error : Coordinate → ℝ) :
    0 ≤ tomographicInner
        (tomographicBackprojection rows
          (fun view => tomographicDot (rows view) error)) error := by
  rw [tomographicResidual_backprojection_energy]
  exact Finset.sum_nonneg (fun view _ => sq_nonneg _)

/-- A zero residual vector gives a zero backprojection. The converse requires a
separate rank/independence condition and is intentionally not inferred. -/
theorem tomographicBackprojection_zero_of_zero_residual
    (rows : View → Coordinate → ℝ) (residual : View → ℝ)
    (zeroResidual : ∀ view, residual view = 0) :
    tomographicBackprojection rows residual = 0 := by
  funext coordinate
  simp [tomographicBackprojection, zeroResidual]

/-- The normal direction cannot see a common invisible state error through the
forward rows. This is the adjoint form of the existing kernel no-go. -/
theorem tomographicBackprojection_zero_on_invisible_error
    (rows : View → Coordinate → ℝ) (error : Coordinate → ℝ)
    (invisible : ∀ view, tomographicDot (rows view) error = 0) :
    tomographicBackprojection rows
        (fun view => tomographicDot (rows view) error) = 0 := by
  apply tomographicBackprojection_zero_of_zero_residual
  exact invisible

end FiniteAdjoint

end OCKIndividuationMSpaceComposition
