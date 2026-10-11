import OCKIndividuationMSpaceComposition.TomographicWeightedConsistency
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Heterogeneous residual accounting

The frame bridge certifies distinguishability; this module certifies the
accounting of observed-vs-predicted disagreement for two modalities.  The
residual is intentionally a sum of two branch energies, so a caller can report
which modality consumed the error budget.  Zero-weight views remain outside
the agreement conclusion.
-/


section HeterogeneousConsistency

variable {World View₁ View₂ : Type*}
  [Fintype View₁] [Fintype View₂] [DecidableEq View₁] [DecidableEq View₂]

def tomographicHeterogeneousWeightedDataResidualEnergy
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (project₁ : View₁ → World → ℝ)
    (project₂ : View₂ → World → ℝ)
    (observation₁ : View₁ → ℝ)
    (observation₂ : View₂ → ℝ)
    (world : World) : ℝ :=
  (∑ view, weight₁ view *
    (project₁ view world - observation₁ view) ^ 2) +
  ∑ view, weight₂ view *
    (project₂ view world - observation₂ view) ^ 2

theorem tomographicHeterogeneousWeightedDataResidualEnergy_nonnegative
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (project₁ : View₁ → World → ℝ)
    (project₂ : View₂ → World → ℝ)
    (observation₁ : View₁ → ℝ)
    (observation₂ : View₂ → ℝ)
    (world : World)
    (weight₁_nonnegative : ∀ view, 0 ≤ weight₁ view)
    (weight₂_nonnegative : ∀ view, 0 ≤ weight₂ view) :
    0 ≤ tomographicHeterogeneousWeightedDataResidualEnergy
      weight₁ weight₂ project₁ project₂ observation₁ observation₂ world := by
  unfold tomographicHeterogeneousWeightedDataResidualEnergy
  exact add_nonneg
    (Finset.sum_nonneg (fun view _ =>
      mul_nonneg (weight₁_nonnegative view) (sq_nonneg _)))
    (Finset.sum_nonneg (fun view _ =>
      mul_nonneg (weight₂_nonnegative view) (sq_nonneg _)))

theorem tomographicHeterogeneousWeightedDataResidualEnergy_mono_weight
    (weightLower₁ : View₁ → ℝ) (weightLower₂ : View₂ → ℝ)
    (weightUpper₁ : View₁ → ℝ) (weightUpper₂ : View₂ → ℝ)
    (project₁ : View₁ → World → ℝ)
    (project₂ : View₂ → World → ℝ)
    (observation₁ : View₁ → ℝ)
    (observation₂ : View₂ → ℝ)
    (world : World)
    (weightLower₁_nonnegative : ∀ view, 0 ≤ weightLower₁ view)
    (weightLower₂_nonnegative : ∀ view, 0 ≤ weightLower₂ view)
    (weight_order₁ : ∀ view, weightLower₁ view ≤ weightUpper₁ view)
    (weight_order₂ : ∀ view, weightLower₂ view ≤ weightUpper₂ view) :
    tomographicHeterogeneousWeightedDataResidualEnergy
        weightLower₁ weightLower₂ project₁ project₂ observation₁ observation₂ world ≤
      tomographicHeterogeneousWeightedDataResidualEnergy
        weightUpper₁ weightUpper₂ project₁ project₂ observation₁ observation₂ world := by
  unfold tomographicHeterogeneousWeightedDataResidualEnergy
  exact add_le_add
    (tomographicWeightedDataResidualEnergy_mono_weight
      weightLower₁ weightUpper₁ project₁ observation₁ world
        weightLower₁_nonnegative weight_order₁)
    (tomographicWeightedDataResidualEnergy_mono_weight
      weightLower₂ weightUpper₂ project₂ observation₂ world
        weightLower₂_nonnegative weight_order₂)

theorem tomographicHeterogeneousWeightedDataResidualEnergy_zero_iff_agreement_on_positive_weight
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (project₁ : View₁ → World → ℝ)
    (project₂ : View₂ → World → ℝ)
    (observation₁ : View₁ → ℝ)
    (observation₂ : View₂ → ℝ)
    (world : World)
    (weight₁_nonnegative : ∀ view, 0 ≤ weight₁ view)
    (weight₂_nonnegative : ∀ view, 0 ≤ weight₂ view) :
    tomographicHeterogeneousWeightedDataResidualEnergy
        weight₁ weight₂ project₁ project₂ observation₁ observation₂ world = 0 ↔
      (∀ view, 0 < weight₁ view → project₁ view world = observation₁ view) ∧
      (∀ view, 0 < weight₂ view → project₂ view world = observation₂ view) := by
  constructor
  · intro residual_zero
    have left_energy_nonnegative :
        0 ≤ ∑ view, weight₁ view *
          (project₁ view world - observation₁ view) ^ 2 :=
      Finset.sum_nonneg (fun view _ =>
        mul_nonneg (weight₁_nonnegative view) (sq_nonneg _))
    have right_energy_nonnegative :
        0 ≤ ∑ view, weight₂ view *
          (project₂ view world - observation₂ view) ^ 2 :=
      Finset.sum_nonneg (fun view _ =>
        mul_nonneg (weight₂_nonnegative view) (sq_nonneg _))
    have left_energy_zero :
        (∑ view, weight₁ view *
          (project₁ view world - observation₁ view) ^ 2) = 0 := by
      unfold tomographicHeterogeneousWeightedDataResidualEnergy at residual_zero
      linarith
    have right_energy_zero :
        (∑ view, weight₂ view *
          (project₂ view world - observation₂ view) ^ 2) = 0 := by
      unfold tomographicHeterogeneousWeightedDataResidualEnergy at residual_zero
      linarith
    constructor
    · intro view positive
      have every_term_zero :=
        (Finset.sum_eq_zero_iff_of_nonneg (fun selected selected_mem =>
          mul_nonneg (weight₁_nonnegative selected)
            (sq_nonneg (project₁ selected world - observation₁ selected)))).mp
          left_energy_zero view (Finset.mem_univ view)
      have square_zero :
          (project₁ view world - observation₁ view) ^ 2 = 0 := by
        exact (mul_eq_zero.mp every_term_zero).resolve_left
          (ne_of_gt positive)
      exact sub_eq_zero.mp (sq_eq_zero_iff.mp square_zero)
    · intro view positive
      have every_term_zero :=
        (Finset.sum_eq_zero_iff_of_nonneg (fun selected selected_mem =>
          mul_nonneg (weight₂_nonnegative selected)
            (sq_nonneg (project₂ selected world - observation₂ selected)))).mp
          right_energy_zero view (Finset.mem_univ view)
      have square_zero :
          (project₂ view world - observation₂ view) ^ 2 = 0 := by
        exact (mul_eq_zero.mp every_term_zero).resolve_left
          (ne_of_gt positive)
      exact sub_eq_zero.mp (sq_eq_zero_iff.mp square_zero)
  · rintro ⟨left_agreement, right_agreement⟩
    unfold tomographicHeterogeneousWeightedDataResidualEnergy
    have left_zero :
        (∑ view, weight₁ view *
          (project₁ view world - observation₁ view) ^ 2) = 0 := by
      change (∑ view, weight₁ view *
        (project₁ view world - observation₁ view) ^ 2) = 0
      apply (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
        mul_nonneg (weight₁_nonnegative view)
          (sq_nonneg (project₁ view world - observation₁ view)))).mpr
      funext view
      by_cases positive : 0 < weight₁ view
      · simp [sub_eq_zero.mpr (left_agreement view positive)]
      · have weight_zero : weight₁ view = 0 := by
          exact le_antisymm (not_lt.mp positive) (weight₁_nonnegative view)
        simp [weight_zero]
    have right_zero :
        (∑ view, weight₂ view *
          (project₂ view world - observation₂ view) ^ 2) = 0 := by
      change (∑ view, weight₂ view *
        (project₂ view world - observation₂ view) ^ 2) = 0
      apply (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
        mul_nonneg (weight₂_nonnegative view)
          (sq_nonneg (project₂ view world - observation₂ view)))).mpr
      funext view
      by_cases positive : 0 < weight₂ view
      · simp [sub_eq_zero.mpr (right_agreement view positive)]
      · have weight_zero : weight₂ view = 0 := by
          exact le_antisymm (not_lt.mp positive) (weight₂_nonnegative view)
        simp [weight_zero]
    simp [left_zero, right_zero]

theorem tomographicHeterogeneousWeightedDataResidualEnergy_pos_of_exists_positive_weight_disagreement
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (project₁ : View₁ → World → ℝ)
    (project₂ : View₂ → World → ℝ)
    (observation₁ : View₁ → ℝ)
    (observation₂ : View₂ → ℝ)
    (world : World)
    (weight₁_nonnegative : ∀ view, 0 ≤ weight₁ view)
    (weight₂_nonnegative : ∀ view, 0 ≤ weight₂ view)
    (witness :
      (∃ view, 0 < weight₁ view ∧ project₁ view world ≠ observation₁ view) ∨
      (∃ view, 0 < weight₂ view ∧ project₂ view world ≠ observation₂ view)) :
    0 < tomographicHeterogeneousWeightedDataResidualEnergy
      weight₁ weight₂ project₁ project₂ observation₁ observation₂ world := by
  have energy_nonnegative :=
    tomographicHeterogeneousWeightedDataResidualEnergy_nonnegative
      weight₁ weight₂ project₁ project₂ observation₁ observation₂ world
      weight₁_nonnegative weight₂_nonnegative
  have energy_ne_zero :
      tomographicHeterogeneousWeightedDataResidualEnergy
        weight₁ weight₂ project₁ project₂ observation₁ observation₂ world ≠ 0 := by
    intro energy_zero
    have agreement :=
      (tomographicHeterogeneousWeightedDataResidualEnergy_zero_iff_agreement_on_positive_weight
        weight₁ weight₂ project₁ project₂ observation₁ observation₂ world
        weight₁_nonnegative weight₂_nonnegative).mp energy_zero
    rcases witness with left_witness | right_witness
    · rcases left_witness with ⟨view, weight_positive, disagreement⟩
      exact disagreement (agreement.1 view weight_positive)
    · rcases right_witness with ⟨view, weight_positive, disagreement⟩
      exact disagreement (agreement.2 view weight_positive)
  exact lt_of_le_of_ne energy_nonnegative (Ne.symm energy_ne_zero)

theorem tomographicHeterogeneousWeightedDataResidualEnergy_uniform_bound
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (project₁ : View₁ → World → ℝ)
    (project₂ : View₂ → World → ℝ)
    (observation₁ : View₁ → ℝ)
    (observation₂ : View₂ → ℝ)
    (world : World)
    (bound₁ bound₂ : ℝ)
    (bound₁_nonnegative : 0 ≤ bound₁)
    (bound₂_nonnegative : 0 ≤ bound₂)
    (weight₁_nonnegative : ∀ view, 0 ≤ weight₁ view)
    (weight₂_nonnegative : ∀ view, 0 ≤ weight₂ view)
    (pointwise_bound₁ : ∀ view,
      |project₁ view world - observation₁ view| ≤ bound₁)
    (pointwise_bound₂ : ∀ view,
      |project₂ view world - observation₂ view| ≤ bound₂) :
    tomographicHeterogeneousWeightedDataResidualEnergy
      weight₁ weight₂ project₁ project₂ observation₁ observation₂ world ≤
      (∑ view, weight₁ view * bound₁ ^ 2) +
      ∑ view, weight₂ view * bound₂ ^ 2 := by
  unfold tomographicHeterogeneousWeightedDataResidualEnergy
  apply add_le_add
  · apply Finset.sum_le_sum
    intro view _
    apply mul_le_mul_of_nonneg_left _ (weight₁_nonnegative view)
    have pointwise := pointwise_bound₁ view
    have squared_bound :
        |project₁ view world - observation₁ view| ^ 2 ≤ bound₁ ^ 2 := by
      apply (sq_le_sq).2
      simpa [abs_of_nonneg bound₁_nonnegative] using pointwise
    simpa [sq_abs] using squared_bound
  · apply Finset.sum_le_sum
    intro view _
    apply mul_le_mul_of_nonneg_left _ (weight₂_nonnegative view)
    have pointwise := pointwise_bound₂ view
    have squared_bound :
        |project₂ view world - observation₂ view| ^ 2 ≤ bound₂ ^ 2 := by
      apply (sq_le_sq).2
      simpa [abs_of_nonneg bound₂_nonnegative] using pointwise
    simpa [sq_abs] using squared_bound

theorem tomographicHeterogeneousWeightedDataResidualEnergy_lower_bound_of_weight_floor
    (weightFloor₁ : View₁ → ℝ) (weightFloor₂ : View₂ → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (project₁ : View₁ → World → ℝ)
    (project₂ : View₂ → World → ℝ)
    (observation₁ : View₁ → ℝ)
    (observation₂ : View₂ → ℝ)
    (world : World)
    (margin₁ margin₂ : ℝ)
    (margin₁_nonnegative : 0 ≤ margin₁)
    (margin₂_nonnegative : 0 ≤ margin₂)
    (weightFloor₁_nonnegative : ∀ view, 0 ≤ weightFloor₁ view)
    (weightFloor₂_nonnegative : ∀ view, 0 ≤ weightFloor₂ view)
    (weightFloor₁_le : ∀ view, weightFloor₁ view ≤ weight₁ view)
    (weightFloor₂_le : ∀ view, weightFloor₂ view ≤ weight₂ view)
    (pointwise_lower_bound₁ : ∀ view,
      margin₁ ≤ |project₁ view world - observation₁ view|)
    (pointwise_lower_bound₂ : ∀ view,
      margin₂ ≤ |project₂ view world - observation₂ view|) :
    (∑ view, weightFloor₁ view * margin₁ ^ 2) +
        ∑ view, weightFloor₂ view * margin₂ ^ 2 ≤
      tomographicHeterogeneousWeightedDataResidualEnergy
        weight₁ weight₂ project₁ project₂ observation₁ observation₂ world := by
  unfold tomographicHeterogeneousWeightedDataResidualEnergy
  exact add_le_add
    (tomographicWeightedDataResidualEnergy_lower_bound_of_weight_floor
      weightFloor₁ weight₁ project₁ observation₁ world margin₁
      margin₁_nonnegative weightFloor₁_nonnegative weightFloor₁_le
      pointwise_lower_bound₁)
    (tomographicWeightedDataResidualEnergy_lower_bound_of_weight_floor
      weightFloor₂ weight₂ project₂ observation₂ world margin₂
      margin₂_nonnegative weightFloor₂_nonnegative weightFloor₂_le
      pointwise_lower_bound₂)

end HeterogeneousConsistency

end OCKIndividuationMSpaceComposition
