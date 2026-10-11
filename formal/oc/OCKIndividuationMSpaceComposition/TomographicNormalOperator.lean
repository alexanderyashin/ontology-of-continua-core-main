import OCKIndividuationMSpaceComposition.TomographicAdjointBackprojection
import OCKIndividuationMSpaceComposition.TomographicGramPair
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite normal operator and least-squares consistency

The normal operator `A* A` is the finite algebraic bridge between registered
projections and reconstruction diagnostics.  This file records the pairing,
symmetry, positivity, and residual-zero contracts needed by an ESTRA
reconstruction layer.  It does not assert invertibility, conditioning,
physical calibration, or semantic recovery.
-/


section NormalOperator

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View] [DecidableEq View]

/-- The finite normal operator obtained by backprojecting forward projections. -/
def tomographicNormalOperator
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) : Coordinate → ℝ :=
  tomographicBackprojection rows (tomographicProjection rows state)

/-! The confidence-weighted normal operator `A* W A`.  The weight is an
    explicit view-level input; no statistical interpretation is inferred. -/

def tomographicWeightedNormalOperator
    (rows : View → Coordinate → ℝ)
    (weight : View → ℝ)
    (state : Coordinate → ℝ) : Coordinate → ℝ :=
  tomographicWeightedBackprojection rows weight (tomographicProjection rows state)

/-! A frame certificate is the explicit quantitative premise that turns the
    normal-energy diagnostic into an injectivity guarantee.  The lower bound is
    supplied for the declared finite model; it is not inferred from the
    existence of the operator or from a small residual. -/

structure TomographicWeightedFrameCertificate
    (rows : View → Coordinate → ℝ) (weight : View → ℝ) where
  alpha : ℝ
  alpha_positive : 0 < alpha
  weight_nonnegative : ∀ view, 0 ≤ weight view
  lower : ∀ state,
    alpha * tomographicInner state state ≤
      tomographicInner
        (tomographicWeightedNormalOperator rows weight state) state

theorem tomographicWeightedNormalOperator_pairing
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (state direction : Coordinate → ℝ) :
    tomographicInner
        (tomographicWeightedNormalOperator rows weight state) direction =
      ∑ view, weight view * tomographicProjection rows state view *
        tomographicProjection rows direction view := by
  unfold tomographicWeightedNormalOperator
  rw [tomographicWeightedBackprojection_adjoint]
  rfl

theorem tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (state : Coordinate → ℝ) :
    tomographicInner
        (tomographicWeightedNormalOperator rows weight state) state =
      ∑ view, weight view * (tomographicProjection rows state view) ^ 2 := by
  rw [tomographicWeightedNormalOperator_pairing]
  apply Finset.sum_congr rfl
  intro view _
  ring

theorem tomographicWeightedNormalOperator_positive_semidefinite
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ view, 0 ≤ weight view) :
    0 ≤ tomographicInner
        (tomographicWeightedNormalOperator rows weight state) state := by
  rw [tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy]
  exact Finset.sum_nonneg (fun view _ =>
    mul_nonneg (weight_nonnegative view) (sq_nonneg _))

theorem tomographicWeightedNormalOperator_self_adjoint
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicInner
        (tomographicWeightedNormalOperator rows weight left) right =
      tomographicInner left
        (tomographicWeightedNormalOperator rows weight right) := by
  calc
    tomographicInner
        (tomographicWeightedNormalOperator rows weight left) right =
        ∑ view, weight view * tomographicProjection rows left view *
          tomographicProjection rows right view :=
      tomographicWeightedNormalOperator_pairing rows weight left right
    _ = ∑ view, weight view * tomographicProjection rows right view *
          tomographicProjection rows left view := by
      apply Finset.sum_congr rfl
      intro view _
      ring
    _ = tomographicInner left
        (tomographicWeightedNormalOperator rows weight right) := by
      symm
      simpa [tomographicInner, mul_comm] using
        (tomographicWeightedNormalOperator_pairing rows weight right left)

theorem tomographicWeightedNormalOperator_add
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicWeightedNormalOperator rows weight (fun coordinate =>
      left coordinate + right coordinate) =
      fun coordinate =>
        tomographicWeightedNormalOperator rows weight left coordinate +
          tomographicWeightedNormalOperator rows weight right coordinate := by
  funext coordinate
  unfold tomographicWeightedNormalOperator tomographicWeightedBackprojection
  rw [tomographicProjection_add]
  calc
    (∑ view, weight view *
        (tomographicProjection rows left view +
          tomographicProjection rows right view) * rows view coordinate) =
        ∑ view, (weight view * tomographicProjection rows left view *
          rows view coordinate +
          weight view * tomographicProjection rows right view *
            rows view coordinate) := by
      apply Finset.sum_congr rfl
      intro view _
      ring
    _ = (∑ view, weight view * tomographicProjection rows left view *
          rows view coordinate) +
        ∑ view, weight view * tomographicProjection rows right view *
          rows view coordinate := by
      rw [Finset.sum_add_distrib]

theorem tomographicWeightedNormalOperator_smul
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (scalar : ℝ) (state : Coordinate → ℝ) :
    tomographicWeightedNormalOperator rows weight (fun coordinate =>
      scalar * state coordinate) =
      fun coordinate => scalar *
        tomographicWeightedNormalOperator rows weight state coordinate := by
  funext coordinate
  unfold tomographicWeightedNormalOperator tomographicWeightedBackprojection
  rw [tomographicProjection_smul]
  calc
    (∑ view, weight view * (scalar *
        tomographicProjection rows state view) * rows view coordinate) =
        ∑ view, scalar * (weight view *
          tomographicProjection rows state view * rows view coordinate) := by
      apply Finset.sum_congr rfl
      intro view _
      ring
    _ = scalar * ∑ view, weight view *
        tomographicProjection rows state view * rows view coordinate := by
      rw [Finset.mul_sum]

theorem tomographicWeightedNormalOperator_zero_of_invisible
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (state : Coordinate → ℝ)
    (invisible : ∀ view, tomographicProjection rows state view = 0) :
    tomographicWeightedNormalOperator rows weight state = 0 := by
  funext coordinate
  simp [tomographicWeightedNormalOperator, tomographicWeightedBackprojection,
    invisible]

theorem tomographicWeightedNormalOperator_zero_iff_invisible_on_positive_weight
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ view, 0 ≤ weight view) :
    tomographicWeightedNormalOperator rows weight state = 0 ↔
      ∀ view, 0 < weight view →
        tomographicProjection rows state view = 0 := by
  constructor
  · intro normalZero view weight_positive
    have energyZero :
        tomographicInner
            (tomographicWeightedNormalOperator rows weight state) state = 0 := by
      simp [normalZero, tomographicInner]
    rw [tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy]
      at energyZero
    have termZero :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedView selectedMem =>
        mul_nonneg (weight_nonnegative selectedView)
          (sq_nonneg (tomographicProjection rows state selectedView)))).mp
        energyZero view (Finset.mem_univ view)
    have squareZero :
        (tomographicProjection rows state view) ^ 2 = 0 := by
      exact (mul_eq_zero.mp termZero).resolve_left
        (ne_of_gt weight_positive)
    exact sq_eq_zero_iff.mp squareZero
  · intro invisible
    funext coordinate
    unfold tomographicWeightedNormalOperator tomographicWeightedBackprojection
    apply Finset.sum_eq_zero
    intro view viewMem
    by_cases weight_positive : 0 < weight view
    · simp [invisible view weight_positive]
    · have weight_zero : weight view = 0 := by
        exact le_antisymm (not_lt.mp weight_positive)
          (weight_nonnegative view)
      simp [weight_zero]

theorem tomographicWeightedFrameCertificate_projection_injective
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (certificate : TomographicWeightedFrameCertificate rows weight) :
    Function.Injective (tomographicProjection rows) := by
  intro left right projections_equal
  let difference : Coordinate → ℝ := fun coordinate =>
    left coordinate - right coordinate
  have difference_projection_zero :
      tomographicProjection rows difference = 0 := by
    rw [show difference = (fun coordinate =>
      left coordinate - right coordinate) from rfl]
    rw [tomographicProjection_sub]
    funext view
    simp [projections_equal]
  have difference_normal_zero :
      tomographicWeightedNormalOperator rows weight difference = 0 :=
    tomographicWeightedNormalOperator_zero_of_invisible rows weight difference
      (fun view => congrFun difference_projection_zero view)
  have normal_energy_zero :
      tomographicInner
          (tomographicWeightedNormalOperator rows weight difference) difference = 0 := by
    simp [difference_normal_zero, tomographicInner]
  have lower_at_difference := certificate.lower difference
  have state_energy_zero : tomographicInner difference difference = 0 := by
    have upper : certificate.alpha * tomographicInner difference difference ≤ 0 := by
      simpa [normal_energy_zero] using lower_at_difference
    have lower_nonnegative : 0 ≤ certificate.alpha * tomographicInner difference difference :=
      mul_nonneg (le_of_lt certificate.alpha_positive)
        (tomographicInner_nonnegative difference)
    have product_zero : certificate.alpha * tomographicInner difference difference = 0 :=
      le_antisymm upper lower_nonnegative
    exact (mul_eq_zero.mp product_zero).resolve_left
      (ne_of_gt certificate.alpha_positive)
  have every_square_zero :
      (fun coordinate => difference coordinate ^ 2) = 0 := by
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
      sq_nonneg (difference coordinate))).mp
    simpa [tomographicInner, pow_two] using state_energy_zero
  have difference_zero : difference = 0 := by
    funext coordinate
    exact sq_eq_zero_iff.mp (congrFun every_square_zero coordinate)
  funext coordinate
  exact sub_eq_zero.mp (congrFun difference_zero coordinate)

theorem tomographicWeightedFrameCertificate_state_energy_bound
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (certificate : TomographicWeightedFrameCertificate rows weight)
    (state : Coordinate → ℝ) (budget : ℝ) :
    tomographicInner
        (tomographicWeightedNormalOperator rows weight
          state) state ≤ budget →
      tomographicInner state state ≤ budget / certificate.alpha := by
  intro energy_upper
  apply (le_div_iff₀ certificate.alpha_positive).mpr
  simpa [mul_comm] using (certificate.lower state).trans energy_upper

theorem tomographicWeightedNormalOperator_difference_energy_eq_weighted_projection_difference_energy
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicInner
        (tomographicWeightedNormalOperator rows weight (fun coordinate =>
          left coordinate - right coordinate))
        (fun coordinate => left coordinate - right coordinate) =
      ∑ view, weight view *
        (tomographicProjection rows left view -
          tomographicProjection rows right view) ^ 2 := by
  rw [tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy]
  apply Finset.sum_congr rfl
  intro view _
  rw [tomographicProjection_sub]

theorem tomographicWeightedFrameCertificate_difference_state_energy_bound
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (certificate : TomographicWeightedFrameCertificate rows weight)
    (left right : Coordinate → ℝ) (budget : ℝ)
    (projection_energy_upper :
      (∑ view, weight view *
        (tomographicProjection rows left view -
          tomographicProjection rows right view) ^ 2) ≤ budget) :
    tomographicInner
        (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) ≤
      budget / certificate.alpha := by
  apply tomographicWeightedFrameCertificate_state_energy_bound rows weight
    certificate (fun coordinate => left coordinate - right coordinate) budget
  rw [tomographicWeightedNormalOperator_difference_energy_eq_weighted_projection_difference_energy]
  exact projection_energy_upper

theorem tomographicNormalOperator_pairing
    (rows : View → Coordinate → ℝ)
    (state direction : Coordinate → ℝ) :
    tomographicInner (tomographicNormalOperator rows state) direction =
      tomographicGramPair rows state direction := by
  unfold tomographicNormalOperator
  rw [tomographicBackprojection_adjoint]
  rfl

theorem tomographicNormalOperator_energy_eq_projection_energy
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicInner (tomographicNormalOperator rows state) state =
      ∑ view, (tomographicProjection rows state view) ^ 2 := by
  rw [tomographicNormalOperator_pairing]
  unfold tomographicGramPair
  apply Finset.sum_congr rfl
  intro view _
  simp [pow_two]

theorem tomographicNormalOperator_add
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicNormalOperator rows (fun coordinate =>
      left coordinate + right coordinate) =
      fun coordinate => tomographicNormalOperator rows left coordinate +
        tomographicNormalOperator rows right coordinate := by
  funext coordinate
  unfold tomographicNormalOperator tomographicBackprojection
  rw [tomographicProjection_add]
  calc
    (∑ view, (tomographicProjection rows left view +
        tomographicProjection rows right view) * rows view coordinate) =
        ∑ view, (tomographicProjection rows left view * rows view coordinate +
          tomographicProjection rows right view * rows view coordinate) := by
      apply Finset.sum_congr rfl
      intro view _
      ring
    _ = (∑ view, tomographicProjection rows left view * rows view coordinate) +
        ∑ view, tomographicProjection rows right view * rows view coordinate := by
      rw [Finset.sum_add_distrib]

theorem tomographicNormalOperator_smul
    (rows : View → Coordinate → ℝ)
    (scalar : ℝ) (state : Coordinate → ℝ) :
    tomographicNormalOperator rows (fun coordinate =>
      scalar * state coordinate) =
      fun coordinate => scalar * tomographicNormalOperator rows state coordinate := by
  funext coordinate
  unfold tomographicNormalOperator tomographicBackprojection
  rw [tomographicProjection_smul]
  calc
    (∑ view, (scalar * tomographicProjection rows state view) *
        rows view coordinate) =
        ∑ view, scalar * (tomographicProjection rows state view * rows view coordinate) := by
      apply Finset.sum_congr rfl
      intro view _
      ring
    _ = scalar * ∑ view,
        tomographicProjection rows state view * rows view coordinate := by
      rw [Finset.mul_sum]

theorem tomographicNormalOperator_self_adjoint
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicInner (tomographicNormalOperator rows left) right =
      tomographicInner left (tomographicNormalOperator rows right) := by
  calc
    tomographicInner (tomographicNormalOperator rows left) right =
        tomographicGramPair rows left right :=
      tomographicNormalOperator_pairing rows left right
    _ = tomographicGramPair rows right left :=
      tomographicGramPair_symmetric rows left right
    _ = tomographicInner (tomographicNormalOperator rows right) left :=
      (tomographicNormalOperator_pairing rows right left).symm
    _ = tomographicInner left (tomographicNormalOperator rows right) := by
      unfold tomographicInner
      apply Finset.sum_congr rfl
      intro coordinate _
      ring

theorem tomographicNormalOperator_positive_semidefinite
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    0 ≤ tomographicInner (tomographicNormalOperator rows state) state := by
  rw [tomographicNormalOperator_pairing]
  exact tomographicGramPair_self_nonnegative rows state

theorem tomographicNormalOperator_zero_of_invisible
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (invisible : ∀ view, tomographicProjection rows state view = 0) :
    tomographicNormalOperator rows state = 0 := by
  unfold tomographicNormalOperator
  exact tomographicBackprojection_zero_on_invisible_error rows state invisible

theorem tomographicNormalOperator_zero_iff_invisible
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicNormalOperator rows state = 0 ↔
      ∀ view, tomographicProjection rows state view = 0 := by
  constructor
  · intro normalZero
    have projectionEnergyZero :
        (∑ view, (tomographicProjection rows state view) ^ 2) = 0 := by
      rw [← tomographicNormalOperator_energy_eq_projection_energy]
      simp [normalZero, tomographicInner]
    simpa [tomographicNormalEnergy] using
      (tomographicNormalEnergy_zero_iff rows state).mp projectionEnergyZero
  · intro invisible
    exact tomographicNormalOperator_zero_of_invisible rows state invisible

theorem tomographicNormalOperator_equal_of_equal_projections
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ)
    (equal_projections : ∀ view,
      tomographicProjection rows left view =
        tomographicProjection rows right view) :
    tomographicNormalOperator rows left =
      tomographicNormalOperator rows right := by
  funext coordinate
  unfold tomographicNormalOperator tomographicBackprojection
  apply Finset.sum_congr rfl
  intro view _
  rw [equal_projections view]

/-! A residual energy is the finite least-squares objective for observed data. -/

def tomographicResidualEnergy
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ) : ℝ :=
  ∑ view, (tomographicProjection rows state view - observations view) ^ 2

theorem tomographicResidualEnergy_nonnegative
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ) :
    0 ≤ tomographicResidualEnergy rows state observations := by
  exact Finset.sum_nonneg (fun view _ => sq_nonneg _)

theorem tomographicResidualEnergy_zero_iff_exact
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ) :
    tomographicResidualEnergy rows state observations = 0 ↔
      ∀ view, tomographicProjection rows state view = observations view := by
  constructor
  · intro energyZero
    have everySquareZero :
        (fun view =>
          (tomographicProjection rows state view - observations view) ^ 2) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
        sq_nonneg (tomographicProjection rows state view - observations view))).mp
        energyZero
    intro view
    exact sub_eq_zero.mp (sq_eq_zero_iff.mp (congrFun everySquareZero view))
  · intro exactData
    unfold tomographicResidualEnergy
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
      sq_nonneg (tomographicProjection rows state view - observations view))).mpr
    funext view
    simp [exactData view]

theorem tomographicResidualEnergy_zero_of_forward_data
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicResidualEnergy rows state
        (tomographicProjection rows state) = 0 := by
  apply (tomographicResidualEnergy_zero_iff_exact rows state
    (tomographicProjection rows state)).mpr
  intro view
  rfl

theorem tomographicResidualEnergy_forward_difference
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicResidualEnergy rows left
        (tomographicProjection rows right) =
      tomographicNormalEnergy rows (fun coordinate =>
        left coordinate - right coordinate) := by
  unfold tomographicResidualEnergy tomographicNormalEnergy
  rw [tomographicProjection_sub]

end NormalOperator

end OCKIndividuationMSpaceComposition
