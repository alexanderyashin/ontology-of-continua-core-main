import OCKIndividuationMSpaceComposition.TomographicMultidimensionalGram
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition


section MultidimensionalGramBatch

variable {Coordinate Modality View Ray Sample : Type*}
  [Fintype Coordinate] [Fintype Modality] [Fintype View]
  [Fintype Ray] [Fintype Sample]

/-! A selected Gram batch is an accounting view over an explicitly selected
    modality/view/ray rectangle.  It does not create a second projection or
    erase provenance: the same registered multidimensional ray image is used
    cell by cell. -/

def tomographicMultidimensionalRayGramPairOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) : ℝ :=
  ∑ modality ∈ modalities, ∑ view ∈ views, ∑ rayId ∈ rayIds,
    tomographicMultidimensionalRayProjection rays left
        (modality, (view, rayId)) *
      tomographicMultidimensionalRayProjection rays right
        (modality, (view, rayId))

def tomographicWeightedMultidimensionalRayGramPairOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) : ℝ :=
  ∑ modality ∈ modalities, ∑ view ∈ views, ∑ rayId ∈ rayIds,
    weight modality view rayId *
      tomographicMultidimensionalRayProjection rays left
        (modality, (view, rayId)) *
      tomographicMultidimensionalRayProjection rays right
        (modality, (view, rayId))

theorem tomographicMultidimensionalRayGramPairOn_symmetric
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn modalities views rayIds rays left right =
      tomographicMultidimensionalRayGramPairOn modalities views rayIds rays right left := by
  unfold tomographicMultidimensionalRayGramPairOn
  apply Finset.sum_congr rfl
  intro modality modalityMem
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  ring

theorem tomographicWeightedMultidimensionalRayGramPairOn_symmetric
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicWeightedMultidimensionalRayGramPairOn modalities views rayIds
        weight rays left right =
      tomographicWeightedMultidimensionalRayGramPairOn modalities views rayIds
        weight rays right left := by
  unfold tomographicWeightedMultidimensionalRayGramPairOn
  apply Finset.sum_congr rfl
  intro modality modalityMem
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  ring

theorem tomographicMultidimensionalRayGramPairOn_self_eq_normalEnergyOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn modalities views rayIds rays state state =
      tomographicMultidimensionalRayNormalEnergyOn modalities views rayIds state rays := by
  unfold tomographicMultidimensionalRayGramPairOn
    tomographicMultidimensionalRayNormalEnergyOn
  apply Finset.sum_congr rfl
  intro modality modalityMem
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  ring

theorem tomographicWeightedMultidimensionalRayGramPairOn_self_eq_normalEnergyOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    tomographicWeightedMultidimensionalRayGramPairOn modalities views rayIds
        weight rays state state =
      tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views rayIds
        weight state rays := by
  unfold tomographicWeightedMultidimensionalRayGramPairOn
    tomographicWeightedMultidimensionalRayNormalEnergyOn
  apply Finset.sum_congr rfl
  intro modality modalityMem
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  ring

theorem tomographicMultidimensionalRayGramPairOn_self_nonnegative
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    0 ≤ tomographicMultidimensionalRayGramPairOn modalities views rayIds rays state state := by
  unfold tomographicMultidimensionalRayGramPairOn
  apply Finset.sum_nonneg
  intro modality modalityMem
  apply Finset.sum_nonneg
  intro view viewMem
  apply Finset.sum_nonneg
  intro rayId rayMem
  simpa [pow_two] using sq_nonneg
    (tomographicMultidimensionalRayProjection rays state (modality, (view, rayId)))

theorem tomographicWeightedMultidimensionalRayGramPairOn_self_nonnegative
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ modality view rayId,
      0 ≤ weight modality view rayId) :
    0 ≤ tomographicWeightedMultidimensionalRayGramPairOn modalities views rayIds
      weight rays state state := by
  unfold tomographicWeightedMultidimensionalRayGramPairOn
  apply Finset.sum_nonneg
  intro modality modalityMem
  apply Finset.sum_nonneg
  intro view viewMem
  apply Finset.sum_nonneg
  intro rayId rayMem
  have h := mul_nonneg (weight_nonnegative modality view rayId)
    (sq_nonneg (tomographicMultidimensionalRayProjection rays state
      (modality, (view, rayId))))
  simpa [pow_two, mul_assoc] using h

theorem tomographicMultidimensionalRayGramPairOn_self_zero_iff_pointwise_invisible
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn modalities views rayIds rays state state = 0 ↔
      ∀ modality ∈ modalities, ∀ view ∈ views, ∀ rayId ∈ rayIds,
        tomographicMultidimensionalRayProjection rays state
          (modality, (view, rayId)) = 0 := by
  constructor
  · intro energyZero modality modalityMem view viewMem rayId rayMem
    have modalityEnergyZero :
        (∑ selectedView ∈ views, ∑ selectedRay ∈ rayIds,
          (tomographicMultidimensionalRayProjection rays state
            (modality, (selectedView, selectedRay))) ^ 2) = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedMod selectedModMem =>
        Finset.sum_nonneg (fun selectedView selectedViewMem =>
          Finset.sum_nonneg (fun selectedRay selectedRayMem =>
            sq_nonneg (tomographicMultidimensionalRayProjection rays state
              (selectedMod, (selectedView, selectedRay))))))).mp
        (by
          have normalZero :
              tomographicMultidimensionalRayNormalEnergyOn modalities views rayIds state rays = 0 := by
            rw [← tomographicMultidimensionalRayGramPairOn_self_eq_normalEnergyOn
              modalities views rayIds rays state]
            exact energyZero
          simpa [tomographicMultidimensionalRayNormalEnergyOn] using normalZero)
        modality modalityMem
    have viewEnergyZero :
        (∑ selectedRay ∈ rayIds,
          (tomographicMultidimensionalRayProjection rays state
            (modality, (view, selectedRay))) ^ 2) = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedView selectedViewMem =>
        Finset.sum_nonneg (fun selectedRay selectedRayMem =>
          sq_nonneg (tomographicMultidimensionalRayProjection rays state
            (modality, (selectedView, selectedRay)))))).mp
        modalityEnergyZero view viewMem
    have squareZero :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedRay selectedRayMem =>
        sq_nonneg (tomographicMultidimensionalRayProjection rays state
          (modality, (view, selectedRay))))).mp
        viewEnergyZero rayId rayMem
    exact sq_eq_zero_iff.mp squareZero
  · intro everyZero
    have normalZero :
        tomographicMultidimensionalRayNormalEnergyOn modalities views rayIds state rays = 0 := by
      unfold tomographicMultidimensionalRayNormalEnergyOn
      apply (Finset.sum_eq_zero_iff_of_nonneg (fun modality modalityMem =>
        Finset.sum_nonneg (fun view viewMem =>
          Finset.sum_nonneg (fun rayId rayMem =>
            sq_nonneg (tomographicMultidimensionalRayProjection rays state
              (modality, (view, rayId))))))).mpr
      intro modality modalityMem
      apply (Finset.sum_eq_zero_iff_of_nonneg (fun view viewMem =>
        Finset.sum_nonneg (fun rayId rayMem =>
          sq_nonneg (tomographicMultidimensionalRayProjection rays state
            (modality, (view, rayId)))))).mpr
      intro view viewMem
      apply (Finset.sum_eq_zero_iff_of_nonneg (fun rayId rayMem =>
        sq_nonneg (tomographicMultidimensionalRayProjection rays state
          (modality, (view, rayId))))).mpr
      intro rayId rayMem
      simp [everyZero modality modalityMem view viewMem rayId rayMem]
    rw [tomographicMultidimensionalRayGramPairOn_self_eq_normalEnergyOn
      modalities views rayIds rays state]
    exact normalZero

theorem tomographicWeightedMultidimensionalRayGramPairOn_self_zero_iff_invisible_on_positive_weight
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ modality view rayId,
      0 ≤ weight modality view rayId) :
    tomographicWeightedMultidimensionalRayGramPairOn modalities views rayIds
        weight rays state state = 0 ↔
      ∀ modality ∈ modalities, ∀ view ∈ views, ∀ rayId ∈ rayIds,
        0 < weight modality view rayId →
          tomographicMultidimensionalRayProjection rays state
            (modality, (view, rayId)) = 0 := by
  constructor
  · intro energyZero modality modalityMem view viewMem rayId rayMem weightPositive
    have modalityEnergyZero :
        (∑ selectedView ∈ views, ∑ selectedRay ∈ rayIds,
          weight modality selectedView selectedRay *
            (tomographicMultidimensionalRayProjection rays state
              (modality, (selectedView, selectedRay))) ^ 2) = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedMod selectedModMem =>
        Finset.sum_nonneg (fun selectedView selectedViewMem =>
          Finset.sum_nonneg (fun selectedRay selectedRayMem =>
            mul_nonneg (weight_nonnegative selectedMod selectedView selectedRay)
              (sq_nonneg (tomographicMultidimensionalRayProjection rays state
                (selectedMod, (selectedView, selectedRay)))))))).mp
        (by
          have normalZero :
              tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views rayIds
                weight state rays = 0 := by
            rw [← tomographicWeightedMultidimensionalRayGramPairOn_self_eq_normalEnergyOn
              modalities views rayIds weight rays state]
            exact energyZero
          simpa [tomographicWeightedMultidimensionalRayNormalEnergyOn] using normalZero)
        modality modalityMem
    have viewEnergyZero :
        (∑ selectedRay ∈ rayIds,
          weight modality view selectedRay *
            (tomographicMultidimensionalRayProjection rays state
              (modality, (view, selectedRay))) ^ 2) = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedView selectedViewMem =>
        Finset.sum_nonneg (fun selectedRay selectedRayMem =>
          mul_nonneg (weight_nonnegative modality selectedView selectedRay)
            (sq_nonneg (tomographicMultidimensionalRayProjection rays state
              (modality, (selectedView, selectedRay))))))).mp
        modalityEnergyZero view viewMem
    have termZero :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedRay selectedRayMem =>
        mul_nonneg (weight_nonnegative modality view selectedRay)
          (sq_nonneg (tomographicMultidimensionalRayProjection rays state
            (modality, (view, selectedRay)))))).mp
        viewEnergyZero rayId rayMem
    have squareZero :
        (tomographicMultidimensionalRayProjection rays state
          (modality, (view, rayId))) ^ 2 = 0 := by
      exact (mul_eq_zero.mp termZero).resolve_left (ne_of_gt weightPositive)
    exact sq_eq_zero_iff.mp squareZero
  · intro everyZero
    have normalZero :
        tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views rayIds
          weight state rays = 0 := by
      unfold tomographicWeightedMultidimensionalRayNormalEnergyOn
      apply (Finset.sum_eq_zero_iff_of_nonneg (fun modality modalityMem =>
        Finset.sum_nonneg (fun view viewMem =>
          Finset.sum_nonneg (fun rayId rayMem =>
            mul_nonneg (weight_nonnegative modality view rayId)
              (sq_nonneg (tomographicMultidimensionalRayProjection rays state
                (modality, (view, rayId)))))))).mpr
      intro modality modalityMem
      apply (Finset.sum_eq_zero_iff_of_nonneg (fun view viewMem =>
        Finset.sum_nonneg (fun rayId rayMem =>
          mul_nonneg (weight_nonnegative modality view rayId)
            (sq_nonneg (tomographicMultidimensionalRayProjection rays state
              (modality, (view, rayId))))))).mpr
      intro view viewMem
      apply (Finset.sum_eq_zero_iff_of_nonneg (fun rayId rayMem =>
        mul_nonneg (weight_nonnegative modality view rayId)
          (sq_nonneg (tomographicMultidimensionalRayProjection rays state
            (modality, (view, rayId)))))).mpr
      intro rayId rayMem
      by_cases weightPositive : 0 < weight modality view rayId
      · simp [everyZero modality modalityMem view viewMem rayId rayMem weightPositive]
      · have weightZero : weight modality view rayId = 0 := by
          exact le_antisymm (not_lt.mp weightPositive)
            (weight_nonnegative modality view rayId)
        simp [weightZero]
    rw [tomographicWeightedMultidimensionalRayGramPairOn_self_eq_normalEnergyOn
      modalities views rayIds weight rays state]
    exact normalZero

theorem tomographicMultidimensionalRayGramPairOn_univ_eq
    [DecidableEq Coordinate] [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn Finset.univ Finset.univ Finset.univ
        rays left right =
      tomographicMultidimensionalRayGramPair rays left right := by
  classical
  unfold tomographicMultidimensionalRayGramPairOn
    tomographicMultidimensionalRayGramPair tomographicGramPair
  rw [← tomographicMultidimensionalRayProjection_eq_projection rays left,
    ← tomographicMultidimensionalRayProjection_eq_projection rays right]
  simpa only [← Finset.univ_product_univ, Finset.sum_product]

theorem tomographicWeightedMultidimensionalRayGramPairOn_univ_eq
    [DecidableEq Coordinate] [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicWeightedMultidimensionalRayGramPairOn Finset.univ Finset.univ Finset.univ
        weight rays left right =
      tomographicWeightedMultidimensionalRayGramPair weight rays left right := by
  classical
  simp [tomographicWeightedMultidimensionalRayGramPairOn,
    tomographicWeightedMultidimensionalRayGramPair]

theorem tomographicMultidimensionalRayGramPairOn_union_modalities
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (first second : Finset Modality)
    (disjoint : Disjoint first second)
    (views : Finset View)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn (first ∪ second) views rayIds rays left right =
      tomographicMultidimensionalRayGramPairOn first views rayIds rays left right +
        tomographicMultidimensionalRayGramPairOn second views rayIds rays left right := by
  unfold tomographicMultidimensionalRayGramPairOn
  rw [Finset.sum_union disjoint]

theorem tomographicMultidimensionalRayGramPairOn_union_views
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn modalities (first ∪ second) rayIds rays left right =
      tomographicMultidimensionalRayGramPairOn modalities first rayIds rays left right +
        tomographicMultidimensionalRayGramPairOn modalities second rayIds rays left right := by
  unfold tomographicMultidimensionalRayGramPairOn
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro modality modalityMem
  rw [Finset.sum_union disjoint]

theorem tomographicMultidimensionalRayGramPairOn_union_rays
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (first second : Finset Ray)
    (disjoint : Disjoint first second)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn modalities views (first ∪ second) rays left right =
      tomographicMultidimensionalRayGramPairOn modalities views first rays left right +
      tomographicMultidimensionalRayGramPairOn modalities views second rays left right := by
  unfold tomographicMultidimensionalRayGramPairOn
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro modality modalityMem
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro view viewMem
  rw [Finset.sum_union disjoint]

theorem tomographicWeightedMultidimensionalRayGramPairOn_union_modalities
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (first second : Finset Modality)
    (disjoint : Disjoint first second)
    (views : Finset View)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicWeightedMultidimensionalRayGramPairOn (first ∪ second) views rayIds
        weight rays left right =
      tomographicWeightedMultidimensionalRayGramPairOn first views rayIds
          weight rays left right +
        tomographicWeightedMultidimensionalRayGramPairOn second views rayIds
          weight rays left right := by
  unfold tomographicWeightedMultidimensionalRayGramPairOn
  rw [Finset.sum_union disjoint]

theorem tomographicWeightedMultidimensionalRayGramPairOn_union_views
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicWeightedMultidimensionalRayGramPairOn modalities (first ∪ second) rayIds
        weight rays left right =
      tomographicWeightedMultidimensionalRayGramPairOn modalities first rayIds
          weight rays left right +
        tomographicWeightedMultidimensionalRayGramPairOn modalities second rayIds
          weight rays left right := by
  unfold tomographicWeightedMultidimensionalRayGramPairOn
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro modality modalityMem
  rw [Finset.sum_union disjoint]

theorem tomographicWeightedMultidimensionalRayGramPairOn_union_rays
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (first second : Finset Ray)
    (disjoint : Disjoint first second)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicWeightedMultidimensionalRayGramPairOn modalities views (first ∪ second)
        weight rays left right =
      tomographicWeightedMultidimensionalRayGramPairOn modalities views first
          weight rays left right +
    tomographicWeightedMultidimensionalRayGramPairOn modalities views second
          weight rays left right := by
  unfold tomographicWeightedMultidimensionalRayGramPairOn
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro modality modalityMem
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro view viewMem
  rw [Finset.sum_union disjoint]

theorem tomographicMultidimensionalRayGramPairOn_union_modalities_le
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (first second : Finset Modality)
    (disjoint : Disjoint first second)
    (views : Finset View)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn first views rayIds rays state state ≤
      tomographicMultidimensionalRayGramPairOn (first ∪ second) views rayIds rays state state := by
  rw [tomographicMultidimensionalRayGramPairOn_union_modalities first second disjoint
    views rayIds rays state state]
  exact le_add_of_nonneg_right
    (tomographicMultidimensionalRayGramPairOn_self_nonnegative second views rayIds rays state)

theorem tomographicMultidimensionalRayGramPairOn_union_views_le
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (rayIds : Finset Ray)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn modalities first rayIds rays state state ≤
      tomographicMultidimensionalRayGramPairOn modalities (first ∪ second) rayIds rays state state := by
  rw [tomographicMultidimensionalRayGramPairOn_union_views modalities first second disjoint
    rayIds rays state state]
  exact le_add_of_nonneg_right
    (tomographicMultidimensionalRayGramPairOn_self_nonnegative modalities second rayIds rays state)

theorem tomographicMultidimensionalRayGramPairOn_union_rays_le
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (first second : Finset Ray)
    (disjoint : Disjoint first second)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    tomographicMultidimensionalRayGramPairOn modalities views first rays state state ≤
      tomographicMultidimensionalRayGramPairOn modalities views (first ∪ second) rays state state := by
  rw [tomographicMultidimensionalRayGramPairOn_union_rays modalities views first second disjoint
    rays state state]
  exact le_add_of_nonneg_right
    (tomographicMultidimensionalRayGramPairOn_self_nonnegative modalities views second rays state)

theorem tomographicWeightedMultidimensionalRayGramPairOn_union_modalities_le
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (first second : Finset Modality)
    (disjoint : Disjoint first second)
    (views : Finset View)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ modality view rayId,
      0 ≤ weight modality view rayId) :
    tomographicWeightedMultidimensionalRayGramPairOn first views rayIds
        weight rays state state ≤
      tomographicWeightedMultidimensionalRayGramPairOn (first ∪ second) views rayIds
        weight rays state state := by
  rw [tomographicWeightedMultidimensionalRayGramPairOn_union_modalities first second disjoint
    views rayIds weight rays state state]
  exact le_add_of_nonneg_right
    (tomographicWeightedMultidimensionalRayGramPairOn_self_nonnegative second views rayIds
      weight rays state weight_nonnegative)

theorem tomographicWeightedMultidimensionalRayGramPairOn_union_views_le
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (rayIds : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ modality view rayId,
      0 ≤ weight modality view rayId) :
    tomographicWeightedMultidimensionalRayGramPairOn modalities first rayIds
        weight rays state state ≤
      tomographicWeightedMultidimensionalRayGramPairOn modalities (first ∪ second) rayIds
        weight rays state state := by
  rw [tomographicWeightedMultidimensionalRayGramPairOn_union_views modalities first second disjoint
    rayIds weight rays state state]
  exact le_add_of_nonneg_right
    (tomographicWeightedMultidimensionalRayGramPairOn_self_nonnegative modalities second rayIds
      weight rays state weight_nonnegative)

theorem tomographicWeightedMultidimensionalRayGramPairOn_union_rays_le
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (first second : Finset Ray)
    (disjoint : Disjoint first second)
    (weight : Modality → View → Ray → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ)
    (weight_nonnegative : ∀ modality view rayId,
      0 ≤ weight modality view rayId) :
    tomographicWeightedMultidimensionalRayGramPairOn modalities views first
        weight rays state state ≤
      tomographicWeightedMultidimensionalRayGramPairOn modalities views (first ∪ second)
        weight rays state state := by
  rw [tomographicWeightedMultidimensionalRayGramPairOn_union_rays modalities views first second
    disjoint weight rays state state]
  exact le_add_of_nonneg_right
    (tomographicWeightedMultidimensionalRayGramPairOn_self_nonnegative modalities views second
      weight rays state weight_nonnegative)

end MultidimensionalGramBatch

end OCKIndividuationMSpaceComposition
