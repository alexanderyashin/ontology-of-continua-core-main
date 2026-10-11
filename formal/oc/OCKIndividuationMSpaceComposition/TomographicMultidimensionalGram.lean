import OCKIndividuationMSpaceComposition.TomographicMultidimensionalFusion
import OCKIndividuationMSpaceComposition.TomographicGramPair
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition


section MultidimensionalGram

variable {Coordinate Modality View Ray Sample : Type*}
  [Fintype Coordinate] [Fintype Modality] [Fintype View]
  [Fintype Ray] [Fintype Sample]

/-! The multidimensional Gram pair is deliberately defined by reusing the
    existing finite Gram pair on the exact multiplicity-row bridge.  It keeps
    cross-modality/view/ray interaction without introducing a second inner
    product or an unproved covariance interpretation. -/

def tomographicMultidimensionalRayGramPair
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) : ℝ :=
  tomographicGramPair (tomographicMultidimensionalRayRow rays) left right

theorem tomographicMultidimensionalRayGramPair_symmetric
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPair rays left right =
      tomographicMultidimensionalRayGramPair rays right left := by
  classical
  exact tomographicGramPair_symmetric
    (tomographicMultidimensionalRayRow rays) left right

theorem tomographicMultidimensionalRayGramPair_self_eq_normalEnergy
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPair rays state state =
      tomographicMultidimensionalRayNormalEnergy state rays := by
  classical
  calc
    tomographicMultidimensionalRayGramPair rays state state =
        tomographicNormalEnergy (tomographicMultidimensionalRayRow rays) state :=
      tomographicGramPair_self_eq_normalEnergy
        (tomographicMultidimensionalRayRow rays) state
    _ = tomographicMultidimensionalRayNormalEnergy state rays :=
      (tomographicMultidimensionalRayNormalEnergy_eq_matrix_normalEnergy
        state rays).symm

theorem tomographicMultidimensionalRayGramPair_self_nonnegative
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    0 ≤ tomographicMultidimensionalRayGramPair rays state state := by
  classical
  rw [tomographicMultidimensionalRayGramPair_self_eq_normalEnergy]
  rw [tomographicMultidimensionalRayNormalEnergy_eq_matrix_normalEnergy state rays]
  exact tomographicNormalEnergy_nonnegative
    (tomographicMultidimensionalRayRow rays) state

theorem tomographicMultidimensionalRayGramPair_abs_bound
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ)
    (leftBound rightBound : Modality → View → Ray → ℝ)
    (leftBound_nonnegative : ∀ modality view rayId,
      0 ≤ leftBound modality view rayId)
    (rightBound_nonnegative : ∀ modality view rayId,
      0 ≤ rightBound modality view rayId)
    (left_projection_bound : ∀ modality view rayId,
      |tomographicMultidimensionalRayProjection rays left
          (modality, (view, rayId))| ≤ leftBound modality view rayId)
    (right_projection_bound : ∀ modality view rayId,
      |tomographicMultidimensionalRayProjection rays right
          (modality, (view, rayId))| ≤ rightBound modality view rayId) :
    |tomographicMultidimensionalRayGramPair rays left right| ≤
      ∑ modality, ∑ view, ∑ rayId,
        leftBound modality view rayId * rightBound modality view rayId := by
  classical
  unfold tomographicMultidimensionalRayGramPair
  have h := tomographicGramPair_abs_bound
    (tomographicMultidimensionalRayRow rays) left right
    (fun index => leftBound index.1 index.2.1 index.2.2)
    (fun index => rightBound index.1 index.2.1 index.2.2) (by
      intro index
      rcases index with ⟨modality, view, rayId⟩
      exact leftBound_nonnegative modality view rayId) (by
      intro index
      rcases index with ⟨modality, view, rayId⟩
      exact rightBound_nonnegative modality view rayId) (by
      intro index
      rcases index with ⟨modality, view, rayId⟩
      have bridge := congrFun
        (tomographicMultidimensionalRayProjection_eq_projection rays left)
        (modality, (view, rayId))
      simpa only [bridge] using left_projection_bound modality view rayId) (by
      intro index
      rcases index with ⟨modality, view, rayId⟩
      have bridge := congrFun
        (tomographicMultidimensionalRayProjection_eq_projection rays right)
        (modality, (view, rayId))
      simpa only [bridge] using right_projection_bound modality view rayId)
  simpa only [← Finset.univ_product_univ, Finset.sum_product] using h

/-! Confidence-weighted interaction keeps the same cross-channel ledger while
    attaching the declared acquisition weight to each modality/view/ray cell.
    The weight is bookkeeping input; no probabilistic meaning is inferred. -/

def tomographicWeightedMultidimensionalRayGramPair
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) : ℝ :=
  ∑ modality, ∑ view, ∑ rayId,
    weight modality view rayId *
      tomographicMultidimensionalRayProjection rays left
        (modality, (view, rayId)) *
      tomographicMultidimensionalRayProjection rays right
        (modality, (view, rayId))

theorem tomographicWeightedMultidimensionalRayGramPair_symmetric
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicWeightedMultidimensionalRayGramPair weight rays left right =
      tomographicWeightedMultidimensionalRayGramPair weight rays right left := by
  classical
  unfold tomographicWeightedMultidimensionalRayGramPair
  apply Finset.sum_congr rfl
  intro modality modalityMem
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  ring

theorem tomographicWeightedMultidimensionalRayGramPair_self_eq_normalEnergy
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    tomographicWeightedMultidimensionalRayGramPair weight rays state state =
      tomographicWeightedMultidimensionalRayNormalEnergy weight state rays := by
  classical
  unfold tomographicWeightedMultidimensionalRayGramPair
    tomographicWeightedMultidimensionalRayNormalEnergy
  apply Finset.sum_congr rfl
  intro modality modalityMem
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  ring

theorem tomographicWeightedMultidimensionalRayGramPair_self_nonnegative
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ modality view rayId,
      0 ≤ weight modality view rayId) :
    0 ≤ tomographicWeightedMultidimensionalRayGramPair weight rays state state := by
  classical
  unfold tomographicWeightedMultidimensionalRayGramPair
  apply Finset.sum_nonneg
  intro modality modalityMem
  apply Finset.sum_nonneg
  intro view viewMem
  apply Finset.sum_nonneg
  intro rayId rayMem
  have square_nonnegative :
      0 ≤ tomographicMultidimensionalRayProjection rays state
        (modality, (view, rayId)) ^ 2 := sq_nonneg _
  calc
    0 ≤ weight modality view rayId *
        tomographicMultidimensionalRayProjection rays state
          (modality, (view, rayId)) ^ 2 :=
      mul_nonneg (weight_nonnegative modality view rayId) square_nonnegative
    _ = weight modality view rayId *
        tomographicMultidimensionalRayProjection rays state
          (modality, (view, rayId)) *
        tomographicMultidimensionalRayProjection rays state
          (modality, (view, rayId)) := by ring

theorem tomographicWeightedMultidimensionalRayGramPair_abs_bound
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ)
    (weightBound leftBound rightBound : Modality → View → Ray → ℝ)
    (weightBound_nonnegative : ∀ modality view rayId,
      0 ≤ weightBound modality view rayId)
    (leftBound_nonnegative : ∀ modality view rayId,
      0 ≤ leftBound modality view rayId)
    (rightBound_nonnegative : ∀ modality view rayId,
      0 ≤ rightBound modality view rayId)
    (weight_abs_bound : ∀ modality view rayId,
      |weight modality view rayId| ≤ weightBound modality view rayId)
    (left_projection_bound : ∀ modality view rayId,
      |tomographicMultidimensionalRayProjection rays left
          (modality, (view, rayId))| ≤ leftBound modality view rayId)
    (right_projection_bound : ∀ modality view rayId,
      |tomographicMultidimensionalRayProjection rays right
          (modality, (view, rayId))| ≤ rightBound modality view rayId) :
    |tomographicWeightedMultidimensionalRayGramPair weight rays left right| ≤
      ∑ modality, ∑ view, ∑ rayId,
        weightBound modality view rayId * leftBound modality view rayId *
          rightBound modality view rayId := by
  unfold tomographicWeightedMultidimensionalRayGramPair
  calc
    |∑ modality, ∑ view, ∑ rayId,
        weight modality view rayId *
          tomographicMultidimensionalRayProjection rays left
            (modality, (view, rayId)) *
          tomographicMultidimensionalRayProjection rays right
            (modality, (view, rayId))| ≤
        ∑ modality, |∑ view, ∑ rayId,
          weight modality view rayId *
            tomographicMultidimensionalRayProjection rays left
              (modality, (view, rayId)) *
            tomographicMultidimensionalRayProjection rays right
              (modality, (view, rayId))| := by
      exact Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ modality, ∑ view, |∑ rayId,
        weight modality view rayId *
          tomographicMultidimensionalRayProjection rays left
            (modality, (view, rayId)) *
          tomographicMultidimensionalRayProjection rays right
            (modality, (view, rayId))| := by
      apply Finset.sum_le_sum
      intro modality modalityMem
      exact Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ modality, ∑ view, ∑ rayId,
        |weight modality view rayId *
          tomographicMultidimensionalRayProjection rays left
            (modality, (view, rayId)) *
          tomographicMultidimensionalRayProjection rays right
            (modality, (view, rayId))| := by
      apply Finset.sum_le_sum
      intro modality modalityMem
      apply Finset.sum_le_sum
      intro view viewMem
      exact Finset.abs_sum_le_sum_abs _ _
    _ = ∑ modality, ∑ view, ∑ rayId,
        |weight modality view rayId| *
          |tomographicMultidimensionalRayProjection rays left
            (modality, (view, rayId))| *
          |tomographicMultidimensionalRayProjection rays right
            (modality, (view, rayId))| := by
      apply Finset.sum_congr rfl
      intro modality modalityMem
      apply Finset.sum_congr rfl
      intro view viewMem
      apply Finset.sum_congr rfl
      intro rayId rayMem
      rw [abs_mul, abs_mul]
    _ ≤ ∑ modality, ∑ view, ∑ rayId,
        weightBound modality view rayId * leftBound modality view rayId *
          rightBound modality view rayId := by
      apply Finset.sum_le_sum
      intro modality modalityMem
      apply Finset.sum_le_sum
      intro view viewMem
      apply Finset.sum_le_sum
      intro rayId rayMem
      have weighted_left_bound :
          |weight modality view rayId| *
              |tomographicMultidimensionalRayProjection rays left
                (modality, (view, rayId))| ≤
            weightBound modality view rayId *
              |tomographicMultidimensionalRayProjection rays left
                (modality, (view, rayId))| :=
        mul_le_mul_of_nonneg_right
          (weight_abs_bound modality view rayId) (abs_nonneg _)
      have weighted_left_right_bound :
          |weight modality view rayId| *
              |tomographicMultidimensionalRayProjection rays left
                (modality, (view, rayId))| *
              |tomographicMultidimensionalRayProjection rays right
                (modality, (view, rayId))| ≤
            weightBound modality view rayId *
              |tomographicMultidimensionalRayProjection rays left
                (modality, (view, rayId))| *
              |tomographicMultidimensionalRayProjection rays right
                (modality, (view, rayId))| :=
        mul_le_mul_of_nonneg_right weighted_left_bound (abs_nonneg _)
      calc
        |weight modality view rayId| *
              |tomographicMultidimensionalRayProjection rays left
                (modality, (view, rayId))| *
              |tomographicMultidimensionalRayProjection rays right
                (modality, (view, rayId))| ≤
            weightBound modality view rayId *
              |tomographicMultidimensionalRayProjection rays left
                (modality, (view, rayId))| *
              |tomographicMultidimensionalRayProjection rays right
                (modality, (view, rayId))| := weighted_left_right_bound
        _ ≤ weightBound modality view rayId * leftBound modality view rayId *
              |tomographicMultidimensionalRayProjection rays right
                (modality, (view, rayId))| := by
          apply mul_le_mul_of_nonneg_right
          apply mul_le_mul_of_nonneg_left
          exact left_projection_bound modality view rayId
          exact weightBound_nonnegative modality view rayId
          exact abs_nonneg _
        _ ≤ weightBound modality view rayId * leftBound modality view rayId *
              rightBound modality view rayId := by
          apply mul_le_mul_of_nonneg_left
          exact right_projection_bound modality view rayId
          exact mul_nonneg
            (weightBound_nonnegative modality view rayId)
            (leftBound_nonnegative modality view rayId)

end MultidimensionalGram

end OCKIndividuationMSpaceComposition
