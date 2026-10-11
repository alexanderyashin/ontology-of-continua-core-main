import OCKIndividuationMSpaceComposition.TomographicDataConsistency
import Mathlib.Algebra.BigOperators.Field

namespace OCKIndividuationMSpaceComposition

/-!
# Weighted data-consistency residual

Confidence weights are useful for adaptive acquisition, but a zero weighted
residual is a full compatibility certificate only when every registered view
has strictly positive weight.  With merely nonnegative weights, zero-weighted
views are intentionally not certified and may still contain disagreement.
-/


section WeightedConsistency

variable {World View : Type*} [Fintype View] [DecidableEq View]

def tomographicWeightedDataResidualEnergy
    (weight : View → ℝ)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) : ℝ :=
  ∑ view, weight view * (project view world - observation view) ^ 2

theorem tomographicWeightedDataResidualEnergy_nonnegative
    (weight : View → ℝ)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World)
    (weight_nonnegative : ∀ view, 0 ≤ weight view) :
    0 ≤ tomographicWeightedDataResidualEnergy weight project observation world := by
  exact Finset.sum_nonneg (fun view _ =>
    mul_nonneg (weight_nonnegative view) (sq_nonneg _))

theorem tomographicWeightedDataResidualEnergy_zero_iff_pointwise_of_positive
    (weight : View → ℝ)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World)
    (weight_positive : ∀ view, 0 < weight view) :
    tomographicWeightedDataResidualEnergy weight project observation world = 0 ↔
      ∀ view, project view world = observation view := by
  constructor
  · intro energyZero
    have everyTermZero :
        (fun view => weight view * (project view world - observation view) ^ 2) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
        mul_nonneg (le_of_lt (weight_positive view))
          (sq_nonneg (project view world - observation view)))).mp energyZero
    intro view
    have selected := congrFun everyTermZero view
    have squareZero : (project view world - observation view) ^ 2 = 0 := by
      exact (mul_eq_zero.mp selected).resolve_left (ne_of_gt (weight_positive view))
    exact sub_eq_zero.mp (sq_eq_zero_iff.mp squareZero)
  · intro everyEqual
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
      mul_nonneg (le_of_lt (weight_positive view))
        (sq_nonneg (project view world - observation view)))).mpr
    funext view
    simp [everyEqual view]

theorem tomographicWeightedDataResidualEnergy_uniform_bound
    (weight : View → ℝ)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World)
    (bound : ℝ)
    (bound_nonnegative : 0 ≤ bound)
    (weight_nonnegative : ∀ view, 0 ≤ weight view)
    (pointwise_bound : ∀ view,
      |project view world - observation view| ≤ bound) :
    tomographicWeightedDataResidualEnergy weight project observation world ≤
      ∑ view, weight view * bound ^ 2 := by
  unfold tomographicWeightedDataResidualEnergy
  apply Finset.sum_le_sum
  intro view _
  apply mul_le_mul_of_nonneg_left _ (weight_nonnegative view)
  have pointwise := pointwise_bound view
  have squared_bound :
      |project view world - observation view| ^ 2 ≤ bound ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg bound_nonnegative] using pointwise
  simpa [sq_abs] using squared_bound

theorem tomographicWeightedDataResidualEnergy_mono_weight
    (weightLower : View → ℝ)
    (weightUpper : View → ℝ)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World)
    (weightLower_nonnegative : ∀ view, 0 ≤ weightLower view)
    (weight_order : ∀ view, weightLower view ≤ weightUpper view) :
    tomographicWeightedDataResidualEnergy weightLower project observation world ≤
      tomographicWeightedDataResidualEnergy weightUpper project observation world := by
  unfold tomographicWeightedDataResidualEnergy
  apply Finset.sum_le_sum
  intro view _
  exact mul_le_mul_of_nonneg_right (weight_order view) (sq_nonneg _)

theorem tomographicWeightedDataResidualEnergy_zero_iff_agreement_on_positive_weight
    (weight : View → ℝ)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World)
    (weight_nonnegative : ∀ view, 0 ≤ weight view) :
    tomographicWeightedDataResidualEnergy weight project observation world = 0 ↔
      ∀ view, 0 < weight view → project view world = observation view := by
  constructor
  · intro energyZero view weight_positive
    have everyTermZero :
        (fun view => weight view * (project view world - observation view) ^ 2) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
        mul_nonneg (weight_nonnegative view)
          (sq_nonneg (project view world - observation view)))).mp energyZero
    have selected := congrFun everyTermZero view
    have squareZero : (project view world - observation view) ^ 2 = 0 := by
      exact (mul_eq_zero.mp selected).resolve_left (ne_of_gt weight_positive)
    exact sub_eq_zero.mp (sq_eq_zero_iff.mp squareZero)
  · intro agreement
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
      mul_nonneg (weight_nonnegative view)
        (sq_nonneg (project view world - observation view)))).mpr
    funext view
    by_cases weight_positive : 0 < weight view
    · simp [sub_eq_zero.mpr (agreement view weight_positive)]
    · have weight_zero : weight view = 0 := by
        exact le_antisymm (not_lt.mp weight_positive) (weight_nonnegative view)
      simp [weight_zero]

theorem tomographicWeightedDataResidualEnergy_pos_of_exists_positive_weight_disagreement
    (weight : View → ℝ)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World)
    (weight_nonnegative : ∀ view, 0 ≤ weight view)
    (witness : ∃ view, 0 < weight view ∧
      project view world ≠ observation view) :
    0 < tomographicWeightedDataResidualEnergy weight project observation world := by
  have energy_nonnegative :
      0 ≤ tomographicWeightedDataResidualEnergy weight project observation world :=
    tomographicWeightedDataResidualEnergy_nonnegative weight project observation world
      weight_nonnegative
  have energy_ne_zero :
      tomographicWeightedDataResidualEnergy weight project observation world ≠ 0 := by
    intro energy_zero
    have agreement :=
      (tomographicWeightedDataResidualEnergy_zero_iff_agreement_on_positive_weight
        weight project observation world weight_nonnegative).mp energy_zero
    rcases witness with ⟨view, weight_positive, disagreement⟩
    exact disagreement (agreement view weight_positive)
  exact lt_of_le_of_ne energy_nonnegative (Ne.symm energy_ne_zero)

theorem tomographicWeightedDataResidualEnergy_lower_bound_of_weight_floor
    (weight_floor : View → ℝ)
    (weight : View → ℝ)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World)
    (margin : ℝ)
    (margin_nonnegative : 0 ≤ margin)
    (weight_floor_nonnegative : ∀ view, 0 ≤ weight_floor view)
    (weight_floor_le : ∀ view, weight_floor view ≤ weight view)
    (pointwise_lower_bound : ∀ view,
      margin ≤ |project view world - observation view|) :
    ∑ view, weight_floor view * margin ^ 2 ≤
      tomographicWeightedDataResidualEnergy weight project observation world := by
  unfold tomographicWeightedDataResidualEnergy
  apply Finset.sum_le_sum
  intro view _
  have square_lower :
      margin ^ 2 ≤ (project view world - observation view) ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg margin_nonnegative] using
      (pointwise_lower_bound view)
  exact le_trans
    (mul_le_mul_of_nonneg_left square_lower
      (weight_floor_nonnegative view))
    (mul_le_mul_of_nonneg_right
      (weight_floor_le view)
      (sq_nonneg (project view world - observation view)))

end WeightedConsistency

end OCKIndividuationMSpaceComposition
