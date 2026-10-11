import OCKIndividuationMSpaceComposition.TomographicMultidimensionalFusion
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition


section MultidimensionalResidual

variable {Modality View Ray : Type*}
  [Fintype Modality] [Fintype View] [Fintype Ray]

/-! A residual ledger keeps the observed and predicted scalar attached to the
same modality/view/ray key.  It is an accounting object for registration and
reconstruction checks, not a semantic score or an acceptance decision. -/

def tomographicMultidimensionalResidualEnergyOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rays : Finset Ray)
    (observed predicted : Modality → View → Ray → ℝ) : ℝ :=
  ∑ modality ∈ modalities, ∑ view ∈ views, ∑ rayId ∈ rays,
    (observed modality view rayId - predicted modality view rayId) ^ 2

def tomographicMultidimensionalResidualEnergy
    (observed predicted : Modality → View → Ray → ℝ) : ℝ :=
  ∑ modality, ∑ view, ∑ rayId,
    (observed modality view rayId - predicted modality view rayId) ^ 2

theorem tomographicMultidimensionalResidualEnergyOn_union_modalities
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (first second : Finset Modality)
    (disjoint : Disjoint first second)
    (views : Finset View)
    (rays : Finset Ray)
    (observed predicted : Modality → View → Ray → ℝ) :
    tomographicMultidimensionalResidualEnergyOn (first ∪ second) views rays
        observed predicted =
      tomographicMultidimensionalResidualEnergyOn first views rays observed predicted +
        tomographicMultidimensionalResidualEnergyOn second views rays observed predicted := by
  unfold tomographicMultidimensionalResidualEnergyOn
  rw [Finset.sum_union disjoint]

theorem tomographicMultidimensionalResidualEnergyOn_univ_eq
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (observed predicted : Modality → View → Ray → ℝ) :
    tomographicMultidimensionalResidualEnergyOn Finset.univ Finset.univ Finset.univ
        observed predicted =
      tomographicMultidimensionalResidualEnergy observed predicted := by
  simp [tomographicMultidimensionalResidualEnergyOn,
    tomographicMultidimensionalResidualEnergy]

theorem tomographicMultidimensionalResidualEnergyOn_eq_zero_of_agreement
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rays : Finset Ray)
    (observed predicted : Modality → View → Ray → ℝ)
    (agreement : ∀ modality view rayId,
      observed modality view rayId = predicted modality view rayId) :
    tomographicMultidimensionalResidualEnergyOn modalities views rays observed predicted = 0 := by
  unfold tomographicMultidimensionalResidualEnergyOn
  simp [agreement]

end MultidimensionalResidual

end OCKIndividuationMSpaceComposition