import OCKIndividuationMSpaceComposition.TomographicWeightedConsistency
import OCKIndividuationMSpaceComposition.TomographicNormalOperator
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite-modality residual fusion

This module generalises the two-branch residual ledger to an arbitrary finite
family of modalities sharing a finite coordinate and view model.  The modality
index is retained in the product view, so residuals remain attributable while
the total energy is one auditable scalar.  No registration, calibration,
independence, or reconstruction algorithm is inferred by this definition.
-/


section FiniteModalityResidual

variable {Coordinate Modality View : Type*}
  [Fintype Coordinate] [Fintype Modality] [Fintype View]

def tomographicFiniteModalityWeightedDataResidualEnergy
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ) : ℝ :=
  ∑ index : Modality × View,
    weight index.1 index.2 *
      (tomographicProjection (rows index.1) state index.2 -
        observation index.1 index.2) ^ 2

theorem tomographicFiniteModalityWeightedDataResidualEnergy_eq_fused_weighted_data_residual
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ) :
    tomographicFiniteModalityWeightedDataResidualEnergy
        rows weight observation state =
      tomographicWeightedDataResidualEnergy
        (fun index : Modality × View => weight index.1 index.2)
        (fun index state => tomographicProjection (rows index.1) state index.2)
        (fun index => observation index.1 index.2)
        state := by
  rfl

/-! The product ledger is also decomposable into modality-owned ledgers.  This
    is the accounting bridge needed when a fused observation is assembled from
    heterogeneous sources: the aggregate residual is exactly the sum of the
    source residuals, so no modality can disappear inside a scalar total. -/

theorem tomographicFiniteModalityWeightedDataResidualEnergy_eq_sum_modalities
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ) :
    tomographicFiniteModalityWeightedDataResidualEnergy
        rows weight observation state =
      ∑ modality,
        tomographicWeightedDataResidualEnergy
          (weight modality)
          (fun view state => tomographicProjection (rows modality) state view)
          (observation modality)
          state := by
  unfold tomographicFiniteModalityWeightedDataResidualEnergy
    tomographicWeightedDataResidualEnergy
  rw [Fintype.sum_prod_type]

theorem tomographicFiniteModalityWeightedDataResidualEnergy_le_sum_modality_budgets
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ)
    (budget : Modality → ℝ)
    (branch_upper : ∀ modality,
      tomographicWeightedDataResidualEnergy
        (weight modality)
        (fun view state => tomographicProjection (rows modality) state view)
        (observation modality)
        state ≤ budget modality) :
    tomographicFiniteModalityWeightedDataResidualEnergy
        rows weight observation state ≤ ∑ modality, budget modality := by
  rw [tomographicFiniteModalityWeightedDataResidualEnergy_eq_sum_modalities]
  exact Finset.sum_le_sum (fun modality _ => branch_upper modality)

theorem tomographicFiniteModalityWeightedNormalOperator_energy_eq_projection_energy
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (state : Coordinate → ℝ) :
    (∑ index : Modality × View,
      weight index.1 index.2 *
        (tomographicProjection (rows index.1) state index.2) ^ 2) =
      tomographicInner
        (tomographicWeightedNormalOperator
          (fun index : Modality × View => rows index.1 index.2)
          (fun index : Modality × View => weight index.1 index.2)
           state) state := by
  classical
  rw [tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy]
  rfl

theorem tomographicFiniteModalityWeightedDataResidualEnergy_nonnegative
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ modality view, 0 ≤ weight modality view) :
    0 ≤ tomographicFiniteModalityWeightedDataResidualEnergy
      rows weight observation state := by
  unfold tomographicFiniteModalityWeightedDataResidualEnergy
  exact Finset.sum_nonneg (fun index _ =>
    mul_nonneg (weight_nonnegative index.1 index.2) (sq_nonneg _))

theorem tomographicFiniteModalityWeightedDataResidualEnergy_zero_iff_agreement_on_positive_weight
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ modality view, 0 ≤ weight modality view) :
    tomographicFiniteModalityWeightedDataResidualEnergy
        rows weight observation state = 0 ↔
      ∀ modality view, 0 < weight modality view →
      tomographicProjection (rows modality) state view =
          observation modality view := by
  classical
  have pair_iff := tomographicWeightedDataResidualEnergy_zero_iff_agreement_on_positive_weight
    (fun index : Modality × View => weight index.1 index.2)
    (fun index state => tomographicProjection (rows index.1) state index.2)
    (fun index => observation index.1 index.2)
    state (fun index => weight_nonnegative index.1 index.2)
  constructor
  · intro h
    have hp : tomographicWeightedDataResidualEnergy
        (fun index : Modality × View => weight index.1 index.2)
        (fun index state => tomographicProjection (rows index.1) state index.2)
        (fun index => observation index.1 index.2) state = 0 := by
      simpa [tomographicFiniteModalityWeightedDataResidualEnergy] using h
    intro modality view hpos
    exact (pair_iff.mp hp) (modality, view) hpos
  · intro h
    have hp := pair_iff.mpr (by
      intro index hpos
      exact h index.1 index.2 hpos)
    simpa [tomographicFiniteModalityWeightedDataResidualEnergy] using hp

theorem tomographicFiniteModalityWeightedDataResidualEnergy_zero_iff_agreement_of_positive_weights
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ)
    (weight_positive : ∀ modality view, 0 < weight modality view) :
    tomographicFiniteModalityWeightedDataResidualEnergy
        rows weight observation state = 0 ↔
      ∀ modality view,
        tomographicProjection (rows modality) state view =
          observation modality view := by
  classical
  apply Iff.trans
    (tomographicFiniteModalityWeightedDataResidualEnergy_zero_iff_agreement_on_positive_weight
      rows weight observation state (fun modality view =>
        le_of_lt (weight_positive modality view)))
  constructor
  · intro agreement modality view
    exact agreement modality view (weight_positive modality view)
  · intro agreement modality view _
    exact agreement modality view

theorem tomographicFiniteModalityWeightedDataResidualEnergy_pos_of_exists_positive_weight_disagreement
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ modality view, 0 ≤ weight modality view)
    (witness : ∃ modality view,
      0 < weight modality view ∧
        tomographicProjection (rows modality) state view ≠
          observation modality view) :
    0 < tomographicFiniteModalityWeightedDataResidualEnergy
      rows weight observation state := by
  classical
  exact tomographicWeightedDataResidualEnergy_pos_of_exists_positive_weight_disagreement
    (fun index : Modality × View => weight index.1 index.2)
    (fun index state => tomographicProjection (rows index.1) state index.2)
    (fun index => observation index.1 index.2)
    state (fun index => weight_nonnegative index.1 index.2) (by
      rcases witness with ⟨modality, view, weight_positive, disagreement⟩
      exact ⟨(modality, view), weight_positive, disagreement⟩)

theorem tomographicFiniteModalityWeightedDataResidualEnergy_lower_bound_of_weight_floor
    (weight_floor : Modality → View → ℝ)
    (weight : Modality → View → ℝ)
    (rows : Modality → View → Coordinate → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ)
    (margin : ℝ)
    (margin_nonnegative : 0 ≤ margin)
    (weight_floor_nonnegative : ∀ modality view,
      0 ≤ weight_floor modality view)
    (weight_floor_le : ∀ modality view,
      weight_floor modality view ≤ weight modality view)
    (pointwise_lower_bound : ∀ modality view,
      margin ≤ |tomographicProjection (rows modality) state view -
        observation modality view|) :
    (∑ index : Modality × View,
      weight_floor index.1 index.2 * margin ^ 2) ≤
      tomographicFiniteModalityWeightedDataResidualEnergy
        rows weight observation state := by
  classical
  exact tomographicWeightedDataResidualEnergy_lower_bound_of_weight_floor
    (fun index : Modality × View => weight_floor index.1 index.2)
    (fun index : Modality × View => weight index.1 index.2)
    (fun index state => tomographicProjection (rows index.1) state index.2)
    (fun index => observation index.1 index.2)
    state margin margin_nonnegative
    (fun index => weight_floor_nonnegative index.1 index.2)
    (fun index => weight_floor_le index.1 index.2)
    (fun index => pointwise_lower_bound index.1 index.2)

theorem tomographicFiniteModalityWeightedDataResidualEnergy_mono_weight
    (rows : Modality → View → Coordinate → ℝ)
    (weightLower weightUpper : Modality → View → ℝ)
    (observation : Modality → View → ℝ)
    (state : Coordinate → ℝ)
    (weight_order : ∀ modality view,
      weightLower modality view ≤ weightUpper modality view) :
    tomographicFiniteModalityWeightedDataResidualEnergy
        rows weightLower observation state ≤
      tomographicFiniteModalityWeightedDataResidualEnergy
        rows weightUpper observation state := by
  unfold tomographicFiniteModalityWeightedDataResidualEnergy
  apply Finset.sum_le_sum
  intro index _
  exact mul_le_mul_of_nonneg_right
    (weight_order index.1 index.2) (sq_nonneg _)

end FiniteModalityResidual

end OCKIndividuationMSpaceComposition
