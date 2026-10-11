import OCKIndividuationMSpaceComposition.TomographicRayTransform
import OCKIndividuationMSpaceComposition.TomographicNormalOperator
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Multidimensional tomographic fusion

This module keeps modality, view, and ray identity in one typed observation
stack.  The stack is then flattened only at the algebraic seam where the
existing finite projection and weighted normal-operator contracts apply.  No
continuous Radon theorem, calibration claim, or scientific acceptance is
introduced by this adapter.
-/


section MultidimensionalFusion

variable {Coordinate Modality View Ray Sample : Type*}
  [Fintype Coordinate] [Fintype Modality] [Fintype View]
  [Fintype Ray] [Fintype Sample]

/-- The registered multidimensional observation stack.  The product index
    retains which modality, view, and ray produced each scalar reading. -/
def tomographicMultidimensionalRayProjection
    (rays : Modality → View → Ray → Sample → Coordinate)
    (image : Coordinate → ℝ) : Modality × (View × Ray) → ℝ :=
  fun index => tomographicRayTransform image (rays index.1)
    index.2.1 index.2.2

/-- The matrix row associated with one modality/view/ray observation. -/
def tomographicMultidimensionalRayRow
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate) :
    (Modality × (View × Ray)) → Coordinate → ℝ :=
  fun index => tomographicRayRow (rays index.1) index.2

/-! The multidimensional stack is exactly the ordinary projection of its
    multiplicity row.  This is the finite-dimensional image-formation bridge;
    it preserves all three physical/semantic indices instead of erasing them
    into an unlabelled vector. -/

theorem tomographicMultidimensionalRayProjection_eq_projection
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (image : Coordinate → ℝ) :
    tomographicMultidimensionalRayProjection rays image =
      tomographicProjection (tomographicMultidimensionalRayRow rays) image := by
  funext index
  have bridge := congrFun
    (tomographicRayTransform_eq_projection_of_ray_row image (rays index.1))
    index.2.1
  have bridge' := congrFun bridge index.2.2
  simpa [tomographicMultidimensionalRayProjection,
    tomographicMultidimensionalRayRow] using bridge'

theorem tomographicMultidimensionalRayProjection_zero
    (rays : Modality → View → Ray → Sample → Coordinate) :
    tomographicMultidimensionalRayProjection rays (0 : Coordinate → ℝ) = 0 := by
  funext index
  simpa [tomographicMultidimensionalRayProjection] using
    congrFun (congrFun
      (tomographicRayTransform_zero (rays index.1)) index.2.1) index.2.2

theorem tomographicMultidimensionalRayProjection_add
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayProjection rays (fun coordinate =>
      left coordinate + right coordinate) =
      fun index => tomographicMultidimensionalRayProjection rays left index +
        tomographicMultidimensionalRayProjection rays right index := by
  funext index
  simp [tomographicMultidimensionalRayProjection, tomographicRayTransform_add]

theorem tomographicMultidimensionalRayProjection_sub
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayProjection rays (fun coordinate =>
      left coordinate - right coordinate) =
      fun index => tomographicMultidimensionalRayProjection rays left index -
        tomographicMultidimensionalRayProjection rays right index := by
  funext index
  simp [tomographicMultidimensionalRayProjection, tomographicRayTransform_sub]

theorem tomographicMultidimensionalRayProjection_smul
    (rays : Modality → View → Ray → Sample → Coordinate)
    (scalar : ℝ) (image : Coordinate → ℝ) :
    tomographicMultidimensionalRayProjection rays (fun coordinate =>
      scalar * image coordinate) =
      fun index => scalar * tomographicMultidimensionalRayProjection rays image index := by
  funext index
  simp [tomographicMultidimensionalRayProjection, tomographicRayTransform_smul]

theorem tomographicMultidimensionalRayProjection_eq_iff
    (rays : Modality → View → Ray → Sample → Coordinate)
    (left right : Coordinate → ℝ) :
    tomographicMultidimensionalRayProjection rays left =
        tomographicMultidimensionalRayProjection rays right ↔
      ∀ modality view rayId,
        tomographicMultidimensionalRayProjection rays left
            (modality, (view, rayId)) =
          tomographicMultidimensionalRayProjection rays right
            (modality, (view, rayId)) := by
  constructor
  · intro equal_stack modality view rayId
    exact congrFun equal_stack (modality, (view, rayId))
  · intro cellwise
    funext index
    rcases index with ⟨modality, view, rayId⟩
    exact cellwise modality view rayId

/-! Summed squared readings are the normal energy of the complete registered
    modality/view/ray stack.  In particular, this is an accounting identity,
    not an assertion that the stack is complete or invertible. -/

def tomographicMultidimensionalRayNormalEnergy
    (image : Coordinate → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate) : ℝ :=
  ∑ modality, ∑ view, ∑ rayId,
    (tomographicMultidimensionalRayProjection rays image
      (modality, (view, rayId))) ^ 2

/-- Checkpointable normal energy for a selected finite modality/view/ray
    batch.  The selected sets are evidence scope, not a silent replacement for
    the complete registered grid. -/
def tomographicMultidimensionalRayNormalEnergyOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rays : Finset Ray)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) : ℝ :=
  ∑ modality ∈ modalities, ∑ view ∈ views, ∑ rayId ∈ rays,
    (tomographicMultidimensionalRayProjection rayMap image
      (modality, (view, rayId))) ^ 2

theorem tomographicMultidimensionalRayNormalEnergyOn_union_modalities
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (first second : Finset Modality)
    (disjoint : Disjoint first second)
    (views : Finset View)
    (rays : Finset Ray)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) :
    tomographicMultidimensionalRayNormalEnergyOn (first ∪ second) views rays
        image rayMap =
      tomographicMultidimensionalRayNormalEnergyOn first views rays image rayMap +
        tomographicMultidimensionalRayNormalEnergyOn second views rays image rayMap := by
  unfold tomographicMultidimensionalRayNormalEnergyOn
  rw [Finset.sum_union disjoint]

theorem tomographicMultidimensionalRayNormalEnergyOn_union_views
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (rays : Finset Ray)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) :
    tomographicMultidimensionalRayNormalEnergyOn modalities (first ∪ second) rays
        image rayMap =
      tomographicMultidimensionalRayNormalEnergyOn modalities first rays image rayMap +
        tomographicMultidimensionalRayNormalEnergyOn modalities second rays image rayMap := by
  unfold tomographicMultidimensionalRayNormalEnergyOn
  simp_rw [Finset.sum_union disjoint, Finset.sum_add_distrib]

theorem tomographicMultidimensionalRayNormalEnergyOn_union_rays
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (first second : Finset Ray)
    (disjoint : Disjoint first second)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) :
    tomographicMultidimensionalRayNormalEnergyOn modalities views (first ∪ second)
        image rayMap =
      tomographicMultidimensionalRayNormalEnergyOn modalities views first image rayMap +
        tomographicMultidimensionalRayNormalEnergyOn modalities views second image rayMap := by
  unfold tomographicMultidimensionalRayNormalEnergyOn
  simp_rw [Finset.sum_union disjoint, Finset.sum_add_distrib]

theorem tomographicMultidimensionalRayNormalEnergyOn_univ_eq
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) :
    tomographicMultidimensionalRayNormalEnergyOn Finset.univ Finset.univ
        Finset.univ image rayMap =
      tomographicMultidimensionalRayNormalEnergy image rayMap := by
  simp [tomographicMultidimensionalRayNormalEnergyOn,
    tomographicMultidimensionalRayNormalEnergy]

theorem tomographicMultidimensionalRayNormalEnergy_eq_matrix_normalEnergy
    [DecidableEq Coordinate]
    (image : Coordinate → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate) :
    tomographicMultidimensionalRayNormalEnergy image rays =
      tomographicNormalEnergy (tomographicMultidimensionalRayRow rays) image := by
  unfold tomographicMultidimensionalRayNormalEnergy tomographicNormalEnergy
  rw [Fintype.sum_prod_type]
  apply Finset.sum_congr rfl
  intro modality modalityMem
  rw [Fintype.sum_prod_type]
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  have bridge := congrFun
    (tomographicMultidimensionalRayProjection_eq_projection rays image)
    (modality, (view, rayId))
  simpa using congrArg (fun value : ℝ => value ^ 2) bridge

/-! Confidence weights remain attached to the full product index.  The
    resulting energy is exactly the existing weighted normal operator with
    the same weights reindexed, so downstream frame certificates can be reused
    without manufacturing a new notion of confidence. -/

def tomographicWeightedMultidimensionalRayNormalEnergy
    (weight : Modality → View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate) : ℝ :=
  ∑ modality, ∑ view, ∑ rayId,
    weight modality view rayId *
      (tomographicMultidimensionalRayProjection rays image
        (modality, (view, rayId))) ^ 2

/-- Weighted checkpoint energy on a selected modality/view/ray batch. -/
def tomographicWeightedMultidimensionalRayNormalEnergyOn
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rays : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) : ℝ :=
  ∑ modality ∈ modalities, ∑ view ∈ views, ∑ rayId ∈ rays,
    weight modality view rayId *
      (tomographicMultidimensionalRayProjection rayMap image
      (modality, (view, rayId))) ^ 2

theorem tomographicWeightedMultidimensionalRayNormalEnergyOn_union_modalities
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (first second : Finset Modality)
    (disjoint : Disjoint first second)
    (views : Finset View)
    (rays : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) :
    tomographicWeightedMultidimensionalRayNormalEnergyOn (first ∪ second) views rays
        weight image rayMap =
      tomographicWeightedMultidimensionalRayNormalEnergyOn first views rays weight image rayMap +
        tomographicWeightedMultidimensionalRayNormalEnergyOn second views rays weight image rayMap := by
  unfold tomographicWeightedMultidimensionalRayNormalEnergyOn
  rw [Finset.sum_union disjoint]

theorem tomographicWeightedMultidimensionalRayNormalEnergyOn_union_views
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (rays : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) :
    tomographicWeightedMultidimensionalRayNormalEnergyOn modalities (first ∪ second) rays
        weight image rayMap =
      tomographicWeightedMultidimensionalRayNormalEnergyOn modalities first rays weight image rayMap +
        tomographicWeightedMultidimensionalRayNormalEnergyOn modalities second rays weight image rayMap := by
  unfold tomographicWeightedMultidimensionalRayNormalEnergyOn
  simp_rw [Finset.sum_union disjoint, Finset.sum_add_distrib]

theorem tomographicWeightedMultidimensionalRayNormalEnergyOn_union_rays
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (first second : Finset Ray)
    (disjoint : Disjoint first second)
    (weight : Modality → View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) :
    tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views (first ∪ second)
        weight image rayMap =
      tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views first weight image rayMap +
        tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views second weight image rayMap := by
  unfold tomographicWeightedMultidimensionalRayNormalEnergyOn
  simp_rw [Finset.sum_union disjoint, Finset.sum_add_distrib]

theorem tomographicWeightedMultidimensionalRayNormalEnergyOn_mono_weight
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rays : Finset Ray)
    (weightLower weightUpper : Modality → View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate)
    (weightLower_nonnegative : ∀ modality view rayId,
      0 ≤ weightLower modality view rayId)
    (weight_order : ∀ modality view rayId,
      weightLower modality view rayId ≤ weightUpper modality view rayId) :
    tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views rays
        weightLower image rayMap ≤
      tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views rays
        weightUpper image rayMap := by
  unfold tomographicWeightedMultidimensionalRayNormalEnergyOn
  apply Finset.sum_le_sum
  intro modality modalityMem
  apply Finset.sum_le_sum
  intro view viewMem
  apply Finset.sum_le_sum
  intro rayId rayMem
  exact mul_le_mul_of_nonneg_right
    (weight_order modality view rayId)
    (sq_nonneg (tomographicMultidimensionalRayProjection rayMap image
      (modality, (view, rayId))))

theorem tomographicWeightedMultidimensionalRayNormalEnergyOn_rowwise_bound
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rays : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate)
    (rayBound : Modality → View → Ray → ℝ)
    (weight_nonnegative : ∀ modality view rayId,
      0 ≤ weight modality view rayId)
    (rayBound_nonnegative : ∀ modality view rayId,
      0 ≤ rayBound modality view rayId)
    (pointwise_bound : ∀ modality view rayId,
      |tomographicMultidimensionalRayProjection rayMap image
          (modality, (view, rayId))| ≤ rayBound modality view rayId) :
    tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views rays
        weight image rayMap ≤
      ∑ modality ∈ modalities, ∑ view ∈ views, ∑ rayId ∈ rays,
        weight modality view rayId * (rayBound modality view rayId) ^ 2 := by
  unfold tomographicWeightedMultidimensionalRayNormalEnergyOn
  apply Finset.sum_le_sum
  intro modality modalityMem
  apply Finset.sum_le_sum
  intro view viewMem
  apply Finset.sum_le_sum
  intro rayId rayMem
  apply mul_le_mul_of_nonneg_left _ (weight_nonnegative modality view rayId)
  have pointwise := pointwise_bound modality view rayId
  have squared_bound :
      |tomographicMultidimensionalRayProjection rayMap image
          (modality, (view, rayId))| ^ 2 ≤
        (rayBound modality view rayId) ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg (rayBound_nonnegative modality view rayId)] using pointwise
  simpa [sq_abs] using squared_bound

theorem tomographicWeightedMultidimensionalRayNormalEnergyOn_difference_rowwise_bound
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (modalities : Finset Modality)
    (views : Finset View)
    (rays : Finset Ray)
    (weight : Modality → View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate)
    (rayBound : Modality → View → Ray → ℝ)
    (weight_nonnegative : ∀ modality view rayId,
      0 ≤ weight modality view rayId)
    (rayBound_nonnegative : ∀ modality view rayId,
      0 ≤ rayBound modality view rayId)
    (pointwise_bound : ∀ modality view rayId,
      |tomographicMultidimensionalRayProjection rayMap left
          (modality, (view, rayId)) -
        tomographicMultidimensionalRayProjection rayMap right
          (modality, (view, rayId))| ≤ rayBound modality view rayId) :
    tomographicWeightedMultidimensionalRayNormalEnergyOn modalities views rays
        weight (fun coordinate => left coordinate - right coordinate) rayMap ≤
      ∑ modality ∈ modalities, ∑ view ∈ views, ∑ rayId ∈ rays,
        weight modality view rayId * (rayBound modality view rayId) ^ 2 := by
  apply tomographicWeightedMultidimensionalRayNormalEnergyOn_rowwise_bound
    modalities views rays weight
    (fun coordinate => left coordinate - right coordinate) rayMap rayBound
    weight_nonnegative rayBound_nonnegative
  intro modality view rayId
  have bridge := congrFun
    (tomographicMultidimensionalRayProjection_sub rayMap left right)
    (modality, (view, rayId))
  rw [bridge]
  exact pointwise_bound modality view rayId

theorem tomographicWeightedMultidimensionalRayNormalEnergyOn_univ_eq
    [DecidableEq Modality] [DecidableEq View] [DecidableEq Ray]
    (weight : Modality → View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (rayMap : Modality → View → Ray → Sample → Coordinate) :
    tomographicWeightedMultidimensionalRayNormalEnergyOn Finset.univ Finset.univ
        Finset.univ weight image rayMap =
      tomographicWeightedMultidimensionalRayNormalEnergy weight image rayMap := by
  simp [tomographicWeightedMultidimensionalRayNormalEnergyOn,
    tomographicWeightedMultidimensionalRayNormalEnergy]

theorem tomographicWeightedMultidimensionalRayNormalEnergy_eq_weightedNormalEnergy
    [DecidableEq Coordinate]
    (weight : Modality → View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate) :
    tomographicWeightedMultidimensionalRayNormalEnergy weight image rays =
      tomographicInner
        (tomographicWeightedNormalOperator
        (tomographicMultidimensionalRayRow rays)
          (fun index : Modality × (View × Ray) =>
            weight index.1 index.2.1 index.2.2)
          image) image := by
  classical
  calc
    tomographicWeightedMultidimensionalRayNormalEnergy weight image rays =
        ∑ index : Modality × (View × Ray),
          weight index.1 index.2.1 index.2.2 *
            (tomographicProjection
              (tomographicMultidimensionalRayRow rays) image index) ^ 2 := by
      unfold tomographicWeightedMultidimensionalRayNormalEnergy
      rw [Fintype.sum_prod_type]
      apply Finset.sum_congr rfl
      intro modality modalityMem
      rw [Fintype.sum_prod_type]
      apply Finset.sum_congr rfl
      intro view viewMem
      apply Finset.sum_congr rfl
      intro rayId rayMem
      have bridge := congrFun
        (tomographicMultidimensionalRayProjection_eq_projection rays image)
        (modality, (view, rayId))
      rw [bridge]
    _ = tomographicInner
        (tomographicWeightedNormalOperator
          (tomographicMultidimensionalRayRow rays)
          (fun index : Modality × (View × Ray) =>
            weight index.1 index.2.1 index.2.2)
          image) image := by
      symm
      exact tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy
        (tomographicMultidimensionalRayRow rays)
        (fun index : Modality × (View × Ray) =>
          weight index.1 index.2.1 index.2.2)
        image

/-! A supplied weighted-frame lower bound can be consumed directly at the
    multidimensional seam.  This is the precise point at which the fused stack
    inherits injectivity; no lower bound is inferred from having many rays. -/

theorem tomographicMultidimensionalRayProjection_injective_of_weighted_frame_certificate
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (weight : Modality → View → Ray → ℝ)
    (certificate :
      TomographicWeightedFrameCertificate
        (tomographicMultidimensionalRayRow rays)
        (fun index : Modality × (View × Ray) =>
          weight index.1 index.2.1 index.2.2)) :
    Function.Injective (tomographicMultidimensionalRayProjection rays) := by
  classical
  intro left right equal_stack
  have left_bridge :=
    tomographicMultidimensionalRayProjection_eq_projection rays left
  have right_bridge :=
    tomographicMultidimensionalRayProjection_eq_projection rays right
  apply tomographicWeightedFrameCertificate_projection_injective
    (tomographicMultidimensionalRayRow rays)
    (fun index : Modality × (View × Ray) =>
      weight index.1 index.2.1 index.2.2)
    certificate
  calc
    tomographicProjection (tomographicMultidimensionalRayRow rays) left =
        tomographicMultidimensionalRayProjection rays left := left_bridge.symm
    _ = tomographicMultidimensionalRayProjection rays right := equal_stack
    _ = tomographicProjection (tomographicMultidimensionalRayRow rays) right :=
      right_bridge

theorem tomographicWeightedMultidimensionalRayNormalEnergy_lower_bound_of_weighted_frame_certificate
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (weight : Modality → View → Ray → ℝ)
    (certificate :
      TomographicWeightedFrameCertificate
        (tomographicMultidimensionalRayRow rays)
        (fun index : Modality × (View × Ray) =>
          weight index.1 index.2.1 index.2.2))
    (image : Coordinate → ℝ) :
    certificate.alpha * tomographicInner image image ≤
      tomographicWeightedMultidimensionalRayNormalEnergy weight image rays := by
  classical
  calc
    certificate.alpha * tomographicInner image image ≤
        tomographicInner
          (tomographicWeightedNormalOperator
            (tomographicMultidimensionalRayRow rays)
            (fun index : Modality × (View × Ray) =>
              weight index.1 index.2.1 index.2.2)
            image) image := certificate.lower image
    _ = tomographicWeightedMultidimensionalRayNormalEnergy weight image rays := by
      symm
      exact tomographicWeightedMultidimensionalRayNormalEnergy_eq_weightedNormalEnergy
        weight image rays

/-! A zero stack energy is only a statement about the registered readings.  It
    is useful as a conservative invisibility diagnostic for the fused stack;
    it must not be upgraded to object equality without a separate frame or
    injectivity certificate. -/

theorem tomographicMultidimensionalRayNormalEnergy_zero_iff_invisible
    [DecidableEq Coordinate]
    (image : Coordinate → ℝ)
    (rays : Modality → View → Ray → Sample → Coordinate) :
    tomographicMultidimensionalRayNormalEnergy image rays = 0 ↔
      ∀ modality view rayId,
        tomographicMultidimensionalRayProjection rays image
          (modality, (view, rayId)) = 0 := by
  classical
  rw [tomographicMultidimensionalRayNormalEnergy_eq_matrix_normalEnergy image rays]
  rw [tomographicNormalEnergy_zero_iff]
  constructor
  · intro invisible modality view rayId
    have bridge := congrFun
      (tomographicMultidimensionalRayProjection_eq_projection rays image)
      (modality, (view, rayId))
    rw [bridge]
    exact invisible (modality, (view, rayId))
  · intro invisible index
    rcases index with ⟨modality, view, rayId⟩
    have bridge := congrFun
      (tomographicMultidimensionalRayProjection_eq_projection rays image)
      (modality, (view, rayId))
    simpa [bridge] using invisible modality view rayId

end MultidimensionalFusion

end OCKIndividuationMSpaceComposition
