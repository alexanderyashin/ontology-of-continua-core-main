import OCKIndividuationMSpaceComposition.TomographicMultidimensionalGramBatch
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition


section MultidimensionalPolarization

variable {Coordinate Modality View Ray Sample : Type*}
  [Fintype Coordinate] [Fintype Modality] [Fintype View]
  [Fintype Ray] [Fintype Sample]

/-! Polarization is the tomography-native way to recover cross-interaction from
    observable energies.  The identities below are finite accounting laws on
    the selected modality/view/ray rectangle; they do not assert that an
    inverse, rank, or scientific interpretation exists. -/

noncomputable def tomographicMultidimensionalRayPolarizationOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) : ℝ :=
  ∑ modality ∈ modalities, ∑ view ∈ views, ∑ rayId ∈ rayIds,
    ((tomographicMultidimensionalRayProjection rays
        (fun coordinate => left coordinate + right coordinate)
        (modality, (view, rayId))) ^ 2 -
      (tomographicMultidimensionalRayProjection rays
        (fun coordinate => left coordinate - right coordinate)
        (modality, (view, rayId))) ^ 2) / 4

noncomputable def tomographicWeightedMultidimensionalRayPolarizationOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) : ℝ :=
  ∑ modality ∈ modalities, ∑ view ∈ views, ∑ rayId ∈ rayIds,
    weight modality view rayId *
      (((tomographicMultidimensionalRayProjection rays
          (fun coordinate => left coordinate + right coordinate)
          (modality, (view, rayId))) ^ 2 -
        (tomographicMultidimensionalRayProjection rays
          (fun coordinate => left coordinate - right coordinate)
          (modality, (view, rayId))) ^ 2) / 4)

theorem tomographicMultidimensionalRayPolarizationOn_eq_gramPairOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayPolarizationOn modalities views rayIds rays left right =
      tomographicMultidimensionalRayGramPairOn modalities views rayIds rays left right := by
  unfold tomographicMultidimensionalRayPolarizationOn
    tomographicMultidimensionalRayGramPairOn
  apply Finset.sum_congr rfl
  intro modality modalityMem
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  have hplus := congrFun
    (tomographicMultidimensionalRayProjection_add rays left right)
    (modality, (view, rayId))
  have hsub := congrFun
    (tomographicMultidimensionalRayProjection_sub rays left right)
    (modality, (view, rayId))
  rw [hplus, hsub]
  ring

theorem tomographicWeightedMultidimensionalRayPolarizationOn_eq_gramPairOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicWeightedMultidimensionalRayPolarizationOn modalities views rayIds
        weight rays left right =
      tomographicWeightedMultidimensionalRayGramPairOn modalities views rayIds
        weight rays left right := by
  unfold tomographicWeightedMultidimensionalRayPolarizationOn
    tomographicWeightedMultidimensionalRayGramPairOn
  apply Finset.sum_congr rfl
  intro modality modalityMem
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  have hplus := congrFun
    (tomographicMultidimensionalRayProjection_add rays left right)
    (modality, (view, rayId))
  have hsub := congrFun
    (tomographicMultidimensionalRayProjection_sub rays left right)
    (modality, (view, rayId))
  rw [hplus, hsub]
  ring

end MultidimensionalPolarization

end OCKIndividuationMSpaceComposition
