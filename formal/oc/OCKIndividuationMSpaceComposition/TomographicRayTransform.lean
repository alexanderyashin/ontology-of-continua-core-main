import Mathlib.Algebra.BigOperators.Field
import OCKIndividuationMSpaceComposition.TomographicBandLimit
import OCKIndividuationMSpaceComposition.TomographicNormalOperator
import OCKIndividuationMSpaceComposition.TomographicProjectionMatrix
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite ray-transform adapter

This is the discrete line-integral primitive used by projection tomography:
each registered ray samples a finite family of coordinates and sums the image
values along that ray.  It is deliberately only a finite algebraic adapter;
continuous Radon inversion, interpolation, calibration and completeness need
separate hypotheses and are not inferred here.
-/


section FiniteRayTransform

variable {Coordinate View Ray Sample : Type*} [Fintype Sample]

def tomographicRayTransform
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) : View → Ray → ℝ :=
  fun view rayId => ∑ sample, image (ray view rayId sample)

/-! Every finite ray sum is a finite matrix row once repeated samples are
    represented by their coordinate multiplicity.  This is the exact seam
    between the ray-level physical notation and the existing projection,
    normal-operator and fusion certificates. -/

def tomographicRayRow
    [DecidableEq Coordinate]
    (ray : View → Ray → Sample → Coordinate) :
    (View × Ray) → Coordinate → ℝ :=
  fun index coordinate =>
    ∑ sample, if ray index.1 index.2 sample = coordinate then 1 else 0

theorem tomographicRayTransform_eq_projection_of_ray_row
    [Fintype Coordinate] [Fintype View] [Fintype Ray]
    [DecidableEq Coordinate]
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayTransform image ray =
      fun view rayId =>
        tomographicProjection (tomographicRayRow ray) image (view, rayId) := by
  funext view
  funext rayId
  unfold tomographicRayTransform tomographicProjection tomographicDot
    tomographicRayRow
  change (∑ sample, image (ray view rayId sample)) =
    ∑ coordinate, (∑ sample,
      if ray view rayId sample = coordinate then 1 else 0) * image coordinate
  calc
    (∑ sample, image (ray view rayId sample)) =
        ∑ sample, ∑ coordinate,
          (if ray view rayId sample = coordinate then 1 else 0) * image coordinate := by
      apply Finset.sum_congr rfl
      intro sample _
      rw [Finset.sum_eq_single (ray view rayId sample)]
      · simp
      · intro coordinate _ coordinate_ne
        have ray_ne_coordinate : ray view rayId sample ≠ coordinate :=
          Ne.symm coordinate_ne
        simp [ray_ne_coordinate]
      · intro sample_mem
        exact (sample_mem (Finset.mem_univ _)).elim
    _ = ∑ coordinate, ∑ sample,
        (if ray view rayId sample = coordinate then 1 else 0) * image coordinate :=
      Finset.sum_comm
    _ = ∑ coordinate, (∑ sample,
        if ray view rayId sample = coordinate then 1 else 0) * image coordinate := by
      apply Finset.sum_congr rfl
      intro coordinate _
      rw [Finset.sum_mul]

/-! A selected finite sample batch is the ray-level analogue of selected-view
normal energy. It is used for checkpointed acquisition and never silently
stands in for the complete ray unless the batch is `Finset.univ`. -/

def tomographicRayTransformOn
    (samples : Finset Sample)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) : View → Ray → ℝ :=
  fun view rayId => ∑ sample ∈ samples, image (ray view rayId sample)

theorem tomographicRayTransformOn_union
    [DecidableEq Sample]
    (first second : Finset Sample)
    (disjoint : Disjoint first second)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayTransformOn (first ∪ second) image ray =
      fun view rayId => tomographicRayTransformOn first image ray view rayId +
        tomographicRayTransformOn second image ray view rayId := by
  funext view
  funext rayId
  unfold tomographicRayTransformOn
  rw [Finset.sum_union disjoint]

theorem tomographicRayTransformOn_univ_eq
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayTransformOn Finset.univ image ray =
      tomographicRayTransform image ray := by
  funext view
  funext rayId
  simp [tomographicRayTransformOn, tomographicRayTransform]

theorem tomographicRayTransform_sub
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayTransform (fun coordinate =>
      left coordinate - right coordinate) ray =
      fun view rayId =>
        tomographicRayTransform left ray view rayId -
          tomographicRayTransform right ray view rayId := by
  funext view
  funext rayId
  simp [tomographicRayTransform, Finset.sum_sub_distrib]

theorem tomographicRayTransformOn_partition_eq_full
    [DecidableEq Sample]
    (first second : Finset Sample)
    (disjoint : Disjoint first second)
    (complete : first ∪ second = Finset.univ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayTransform image ray =
      fun view rayId => tomographicRayTransformOn first image ray view rayId +
        tomographicRayTransformOn second image ray view rayId := by
  rw [← tomographicRayTransformOn_univ_eq image ray, ← complete]
  exact tomographicRayTransformOn_union first second disjoint image ray

theorem tomographicRayTransformOn_abs_bound
    (samples : Finset Sample)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (bound : ℝ)
    (image_bound : ∀ coordinate, |image coordinate| ≤ bound) :
    ∀ view rayId,
      |tomographicRayTransformOn samples image ray view rayId| ≤
        samples.card * bound := by
  intro view rayId
  unfold tomographicRayTransformOn
  calc
    |∑ sample ∈ samples, image (ray view rayId sample)| ≤
        ∑ sample ∈ samples, |image (ray view rayId sample)| := by
      exact Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ sample ∈ samples, bound := by
      apply Finset.sum_le_sum
      intro sample sampleMem
      exact image_bound (ray view rayId sample)
    _ = samples.card * bound := by
      simp

theorem tomographicRayTransformOn_abs_bound_by_sample
    (samples : Finset Sample)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (sample_bound : View → Ray → Sample → ℝ)
    (sample_bound_nonnegative : ∀ view rayId sample,
      0 ≤ sample_bound view rayId sample)
    (image_bound : ∀ view rayId sample,
      |image (ray view rayId sample)| ≤ sample_bound view rayId sample) :
    ∀ view rayId,
      |tomographicRayTransformOn samples image ray view rayId| ≤
        ∑ sample ∈ samples, sample_bound view rayId sample := by
  intro view rayId
  unfold tomographicRayTransformOn
  calc
    |∑ sample ∈ samples, image (ray view rayId sample)| ≤
        ∑ sample ∈ samples, |image (ray view rayId sample)| := by
      exact Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ sample ∈ samples, sample_bound view rayId sample := by
      apply Finset.sum_le_sum
      intro sample sampleMem
      exact image_bound view rayId sample

theorem tomographicRayTransformOn_sq_bound_by_sample
    (samples : Finset Sample)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (sample_bound : View → Ray → Sample → ℝ)
    (sample_bound_nonnegative : ∀ view rayId sample,
      0 ≤ sample_bound view rayId sample)
    (image_bound : ∀ view rayId sample,
      |image (ray view rayId sample)| ≤ sample_bound view rayId sample) :
    ∀ view rayId,
      |tomographicRayTransformOn samples image ray view rayId| ^ 2 ≤
        (∑ sample ∈ samples, sample_bound view rayId sample) ^ 2 := by
  intro view rayId
  have amplitude := tomographicRayTransformOn_abs_bound_by_sample samples image
    ray sample_bound sample_bound_nonnegative image_bound view rayId
  apply (sq_le_sq).2
  simpa [abs_of_nonneg (Finset.sum_nonneg (fun sample sampleMem =>
    sample_bound_nonnegative view rayId sample))] using amplitude

theorem tomographicRayTransform_sq_bound_by_sample
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (sample_bound : View → Ray → Sample → ℝ)
    (sample_bound_nonnegative : ∀ view rayId sample,
      0 ≤ sample_bound view rayId sample)
    (image_bound : ∀ view rayId sample,
      |image (ray view rayId sample)| ≤ sample_bound view rayId sample) :
    ∀ view rayId,
      |tomographicRayTransform image ray view rayId| ^ 2 ≤
        (∑ sample, sample_bound view rayId sample) ^ 2 := by
  intro view rayId
  have selected := tomographicRayTransformOn_sq_bound_by_sample
    (samples := Finset.univ) image ray sample_bound
    sample_bound_nonnegative image_bound view rayId
  simpa [tomographicRayTransformOn, tomographicRayTransform] using selected

theorem tomographicRayTransformOn_diff_abs_bound
    (samples : Finset Sample)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (bound : ℝ)
    (pointwise_bound : ∀ coordinate,
      |left coordinate - right coordinate| ≤ bound) :
    ∀ view rayId,
      |tomographicRayTransformOn samples left ray view rayId -
          tomographicRayTransformOn samples right ray view rayId| ≤
        samples.card * bound := by
  intro view rayId
  unfold tomographicRayTransformOn
  rw [← Finset.sum_sub_distrib]
  calc
    |∑ sample ∈ samples, (left (ray view rayId sample) -
        right (ray view rayId sample))| ≤
        ∑ sample ∈ samples, |left (ray view rayId sample) -
          right (ray view rayId sample)| := by
      exact Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ sample ∈ samples, bound := by
      apply Finset.sum_le_sum
      intro sample sampleMem
      exact pointwise_bound (ray view rayId sample)
    _ = samples.card * bound := by
      simp

theorem tomographicRayTransformOn_diff_sq_bound
    (samples : Finset Sample)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (sample_bound : View → Ray → Sample → ℝ)
    (sample_bound_nonnegative : ∀ view rayId sample,
      0 ≤ sample_bound view rayId sample)
    (pointwise_bound : ∀ view rayId sample,
      |left (ray view rayId sample) - right (ray view rayId sample)| ≤
        sample_bound view rayId sample) :
    ∀ view rayId,
      |tomographicRayTransformOn samples left ray view rayId -
          tomographicRayTransformOn samples right ray view rayId| ^ 2 ≤
        (∑ sample ∈ samples, sample_bound view rayId sample) ^ 2 := by
  intro view rayId
  unfold tomographicRayTransformOn
  rw [← Finset.sum_sub_distrib]
  have amplitude :
      |∑ sample ∈ samples,
          (left (ray view rayId sample) - right (ray view rayId sample))| ≤
        ∑ sample ∈ samples, sample_bound view rayId sample := by
    calc
      |∑ sample ∈ samples,
          (left (ray view rayId sample) - right (ray view rayId sample))| ≤
          ∑ sample ∈ samples,
            |left (ray view rayId sample) - right (ray view rayId sample)| :=
        Finset.abs_sum_le_sum_abs _ _
      _ ≤ ∑ sample ∈ samples, sample_bound view rayId sample := by
        apply Finset.sum_le_sum
        intro sample sampleMem
        exact pointwise_bound view rayId sample
  apply (sq_le_sq).2
  simpa [abs_of_nonneg (Finset.sum_nonneg (fun sample sampleMem =>
    sample_bound_nonnegative view rayId sample))] using amplitude

theorem tomographicRayTransform_diff_sq_bound
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (sample_bound : View → Ray → Sample → ℝ)
    (sample_bound_nonnegative : ∀ view rayId sample,
      0 ≤ sample_bound view rayId sample)
    (pointwise_bound : ∀ view rayId sample,
      |left (ray view rayId sample) - right (ray view rayId sample)| ≤
        sample_bound view rayId sample) :
    ∀ view rayId,
      |tomographicRayTransform left ray view rayId -
          tomographicRayTransform right ray view rayId| ^ 2 ≤
        (∑ sample, sample_bound view rayId sample) ^ 2 := by
  intro view rayId
  have selected := tomographicRayTransformOn_diff_sq_bound
    (samples := Finset.univ) left right ray sample_bound
    sample_bound_nonnegative pointwise_bound view rayId
  simpa [tomographicRayTransformOn, tomographicRayTransform] using selected

/-! Aggregating squared ray readings gives the ray-level counterpart of the
    finite view normal energy.  It is an accounting certificate over the
    registered finite `(view, ray)` grid, not a continuous inversion claim. -/

def tomographicRayNormalEnergy
    [Fintype View] [Fintype Ray]
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) : ℝ :=
  ∑ view, ∑ rayId, (tomographicRayTransform image ray view rayId) ^ 2

/-! The ray-grid energy is exactly the ordinary finite matrix normal energy
    after flattening `(view, ray)` into one registered index.  This is the
    algebraic handoff to the existing `A* A` certificates; it does not add a
    rank, conditioning, calibration or continuous-coverage premise. -/

theorem tomographicRayNormalEnergy_eq_matrix_normalEnergy
    [Fintype Coordinate] [Fintype View] [Fintype Ray]
    [DecidableEq Coordinate]
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayNormalEnergy image ray =
      tomographicNormalEnergy (tomographicRayRow ray) image := by
  unfold tomographicRayNormalEnergy tomographicNormalEnergy
  rw [Fintype.sum_prod_type]
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  have bridge := congrFun
    (tomographicRayTransform_eq_projection_of_ray_row image ray)
    view
  have bridge' := congrFun bridge rayId
  simpa using congrArg (fun value : ℝ => value ^ 2) bridge'

def tomographicRayNormalEnergyOn
    (views : Finset View)
    (rays : Finset Ray)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) : ℝ :=
  ∑ view ∈ views, ∑ rayId ∈ rays,
    (tomographicRayTransform image ray view rayId) ^ 2

/-! Confidence/exposure weights are kept separate from the unweighted normal
    energy. A zero weight deliberately removes a ray from this accounting
    certificate; it does not create evidence for that ray. -/

def tomographicWeightedRayNormalEnergyOn
    (views : Finset View)
    (rays : Finset Ray)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) : ℝ :=
  ∑ view ∈ views, ∑ rayId ∈ rays,
    weight view rayId * (tomographicRayTransform image ray view rayId) ^ 2

def tomographicWeightedRayNormalEnergy
    [Fintype View] [Fintype Ray]
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) : ℝ :=
  ∑ view, ∑ rayId,
    weight view rayId * (tomographicRayTransform image ray view rayId) ^ 2

theorem tomographicWeightedRayNormalEnergy_eq_matrix_weightedNormalEnergy
    [Fintype Coordinate] [Fintype View] [Fintype Ray]
    [DecidableEq Coordinate] [DecidableEq View] [DecidableEq Ray]
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicWeightedRayNormalEnergy weight image ray =
      tomographicInner
        (tomographicWeightedNormalOperator
          (tomographicRayRow ray)
          (fun index : View × Ray => weight index.1 index.2)
          image) image := by
  calc
    tomographicWeightedRayNormalEnergy weight image ray =
        ∑ index : View × Ray,
          weight index.1 index.2 *
            (tomographicProjection (tomographicRayRow ray) image index) ^ 2 := by
      unfold tomographicWeightedRayNormalEnergy
      rw [Fintype.sum_prod_type]
      apply Finset.sum_congr rfl
      intro view viewMem
      apply Finset.sum_congr rfl
      intro rayId rayMem
      have bridge := congrFun
        (tomographicRayTransform_eq_projection_of_ray_row image ray)
        view
      have bridge' := congrFun bridge rayId
      rw [bridge']
    _ = tomographicInner
        (tomographicWeightedNormalOperator
          (tomographicRayRow ray)
          (fun index : View × Ray => weight index.1 index.2)
          image) image := by
      symm
      exact tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy
        (tomographicRayRow ray)
        (fun index : View × Ray => weight index.1 index.2)
        image

/-! Geometry calibration is a separate equivalence boundary.  If two ray
    parameterizations address the same coordinate at every registered sample,
    they are observationally indistinguishable to this finite projector.  The
    statement is intentionally pointwise: it does not certify calibration
    quality, injectivity, or physical correctness of either parameterization. -/

theorem tomographicRayTransform_congr_of_ray_eq
    (image : Coordinate → ℝ)
    (ray₁ ray₂ : View → Ray → Sample → Coordinate)
    (ray_eq : ∀ view rayId sample,
      ray₁ view rayId sample = ray₂ view rayId sample) :
    tomographicRayTransform image ray₁ =
      tomographicRayTransform image ray₂ := by
  funext view
  funext rayId
  simp [tomographicRayTransform, ray_eq]

theorem tomographicRayNormalEnergyOn_congr_of_ray_eq
    (views : Finset View)
    (rays : Finset Ray)
    (image : Coordinate → ℝ)
    (ray₁ ray₂ : View → Ray → Sample → Coordinate)
    (ray_eq : ∀ view rayId sample,
      ray₁ view rayId sample = ray₂ view rayId sample) :
    tomographicRayNormalEnergyOn views rays image ray₁ =
      tomographicRayNormalEnergyOn views rays image ray₂ := by
  unfold tomographicRayNormalEnergyOn
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  rw [tomographicRayTransform_congr_of_ray_eq image ray₁ ray₂ ray_eq]

theorem tomographicWeightedRayNormalEnergyOn_congr_of_ray_eq
    (views : Finset View)
    (rays : Finset Ray)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray₁ ray₂ : View → Ray → Sample → Coordinate)
    (ray_eq : ∀ view rayId sample,
      ray₁ view rayId sample = ray₂ view rayId sample) :
    tomographicWeightedRayNormalEnergyOn views rays weight image ray₁ =
      tomographicWeightedRayNormalEnergyOn views rays weight image ray₂ := by
  unfold tomographicWeightedRayNormalEnergyOn
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  rw [tomographicRayTransform_congr_of_ray_eq image ray₁ ray₂ ray_eq]

theorem tomographicRayNormalEnergy_congr_of_ray_eq
    [Fintype View] [Fintype Ray]
    (image : Coordinate → ℝ)
    (ray₁ ray₂ : View → Ray → Sample → Coordinate)
    (ray_eq : ∀ view rayId sample,
      ray₁ view rayId sample = ray₂ view rayId sample) :
    tomographicRayNormalEnergy image ray₁ =
      tomographicRayNormalEnergy image ray₂ := by
  simpa [tomographicRayNormalEnergy, tomographicRayNormalEnergyOn] using
    (tomographicRayNormalEnergyOn_congr_of_ray_eq
      (views := Finset.univ) (rays := Finset.univ) image ray₁ ray₂ ray_eq)

theorem tomographicWeightedRayNormalEnergy_congr_of_ray_eq
    [Fintype View] [Fintype Ray]
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray₁ ray₂ : View → Ray → Sample → Coordinate)
    (ray_eq : ∀ view rayId sample,
      ray₁ view rayId sample = ray₂ view rayId sample) :
    tomographicWeightedRayNormalEnergy weight image ray₁ =
      tomographicWeightedRayNormalEnergy weight image ray₂ := by
  simpa [tomographicWeightedRayNormalEnergy,
    tomographicWeightedRayNormalEnergyOn] using
    (tomographicWeightedRayNormalEnergyOn_congr_of_ray_eq
      (views := Finset.univ) (rays := Finset.univ) weight image ray₁ ray₂ ray_eq)

theorem tomographicWeightedRayNormalEnergyOn_univ_eq
    [Fintype View] [Fintype Ray]
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicWeightedRayNormalEnergyOn Finset.univ Finset.univ weight image ray =
      tomographicWeightedRayNormalEnergy weight image ray := by
  simp [tomographicWeightedRayNormalEnergyOn, tomographicWeightedRayNormalEnergy]

theorem tomographicRayNormalEnergyOn_nonnegative
    (views : Finset View)
    (rays : Finset Ray)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    0 ≤ tomographicRayNormalEnergyOn views rays image ray := by
  unfold tomographicRayNormalEnergyOn
  exact Finset.sum_nonneg (fun view viewMem =>
    Finset.sum_nonneg (fun rayId rayMem =>
      sq_nonneg (tomographicRayTransform image ray view rayId)))

theorem tomographicWeightedRayNormalEnergyOn_nonnegative
    (views : Finset View)
    (rays : Finset Ray)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (weight_nonnegative : ∀ view rayId, 0 ≤ weight view rayId) :
    0 ≤ tomographicWeightedRayNormalEnergyOn views rays weight image ray := by
  unfold tomographicWeightedRayNormalEnergyOn
  exact Finset.sum_nonneg (fun view viewMem =>
    Finset.sum_nonneg (fun rayId rayMem =>
      mul_nonneg (weight_nonnegative view rayId)
        (sq_nonneg (tomographicRayTransform image ray view rayId))))

theorem tomographicWeightedRayNormalEnergyOn_rowwise_bound
    (views : Finset View)
    (rays : Finset Ray)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (ray_bound : View → Ray → ℝ)
    (weight_nonnegative : ∀ view rayId, 0 ≤ weight view rayId)
    (ray_bound_nonnegative : ∀ view rayId,
      0 ≤ ray_bound view rayId)
    (pointwise_bound : ∀ view rayId,
      |tomographicRayTransform image ray view rayId| ≤
        ray_bound view rayId) :
    tomographicWeightedRayNormalEnergyOn views rays weight image ray ≤
      ∑ view ∈ views, ∑ rayId ∈ rays,
        weight view rayId * (ray_bound view rayId) ^ 2 := by
  unfold tomographicWeightedRayNormalEnergyOn
  apply Finset.sum_le_sum
  intro view viewMem
  apply Finset.sum_le_sum
  intro rayId rayMem
  apply mul_le_mul_of_nonneg_left _ (weight_nonnegative view rayId)
  have pointwise := pointwise_bound view rayId
  have squared_bound :
      |tomographicRayTransform image ray view rayId| ^ 2 ≤
        (ray_bound view rayId) ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg (ray_bound_nonnegative view rayId)] using pointwise
  simpa [sq_abs] using squared_bound

theorem tomographicWeightedRayNormalEnergyOn_difference_rowwise_bound
    (views : Finset View)
    (rays : Finset Ray)
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (ray_bound : View → Ray → ℝ)
    (weight_nonnegative : ∀ view rayId, 0 ≤ weight view rayId)
    (ray_bound_nonnegative : ∀ view rayId, 0 ≤ ray_bound view rayId)
    (pointwise_bound : ∀ view rayId,
      |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId| ≤
        ray_bound view rayId) :
    tomographicWeightedRayNormalEnergyOn views rays weight
        (fun coordinate => left coordinate - right coordinate) ray ≤
      ∑ view ∈ views, ∑ rayId ∈ rays,
        weight view rayId * (ray_bound view rayId) ^ 2 := by
  unfold tomographicWeightedRayNormalEnergyOn
  apply Finset.sum_le_sum
  intro view viewMem
  apply Finset.sum_le_sum
  intro rayId rayMem
  apply mul_le_mul_of_nonneg_left _ (weight_nonnegative view rayId)
  have pointwise := pointwise_bound view rayId
  have squared_bound :
      |tomographicRayTransform left ray view rayId -
          tomographicRayTransform right ray view rayId| ^ 2 ≤
        (ray_bound view rayId) ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg (ray_bound_nonnegative view rayId)] using pointwise
  rw [congrFun (congrFun (tomographicRayTransform_sub left right ray) view)
    rayId]
  simpa [sq_abs] using squared_bound

theorem tomographicWeightedRayNormalEnergyOn_mono_weight
    (views : Finset View)
    (rays : Finset Ray)
    (weightLower weightUpper : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (weightLower_nonnegative : ∀ view rayId,
      0 ≤ weightLower view rayId)
    (weight_order : ∀ view rayId,
      weightLower view rayId ≤ weightUpper view rayId) :
    tomographicWeightedRayNormalEnergyOn views rays weightLower image ray ≤
      tomographicWeightedRayNormalEnergyOn views rays weightUpper image ray := by
  unfold tomographicWeightedRayNormalEnergyOn
  apply Finset.sum_le_sum
  intro view viewMem
  apply Finset.sum_le_sum
  intro rayId rayMem
  exact mul_le_mul_of_nonneg_right (weight_order view rayId)
    (sq_nonneg (tomographicRayTransform image ray view rayId))

theorem tomographicWeightedRayNormalEnergyOn_lower_bound_of_uniform_weight
    (views : Finset View)
    (rays : Finset Ray)
    (weight_floor : ℝ)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (weight_floor_nonnegative : 0 ≤ weight_floor)
    (weight_floor_le : ∀ view rayId, weight_floor ≤ weight view rayId) :
    weight_floor * tomographicRayNormalEnergyOn views rays image ray ≤
      tomographicWeightedRayNormalEnergyOn views rays weight image ray := by
  unfold tomographicRayNormalEnergyOn tomographicWeightedRayNormalEnergyOn
  calc
    weight_floor * (∑ view ∈ views, ∑ rayId ∈ rays,
        (tomographicRayTransform image ray view rayId) ^ 2) =
        ∑ view ∈ views, ∑ rayId ∈ rays,
          weight_floor * (tomographicRayTransform image ray view rayId) ^ 2 := by
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro view viewMem
      rw [Finset.mul_sum]
    _ ≤ ∑ view ∈ views, ∑ rayId ∈ rays,
          weight view rayId * (tomographicRayTransform image ray view rayId) ^ 2 := by
      apply Finset.sum_le_sum
      intro view viewMem
      apply Finset.sum_le_sum
      intro rayId rayMem
      exact mul_le_mul_of_nonneg_right (weight_floor_le view rayId)
        (sq_nonneg (tomographicRayTransform image ray view rayId))

theorem tomographicWeightedRayNormalEnergyOn_difference_zero_iff_agreement_on_positive_weight
    (views : Finset View)
    (rays : Finset Ray)
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (weight_nonnegative : ∀ view rayId, 0 ≤ weight view rayId) :
    tomographicWeightedRayNormalEnergyOn views rays weight
        (fun coordinate => left coordinate - right coordinate) ray = 0 ↔
      ∀ view ∈ views, ∀ rayId ∈ rays, 0 < weight view rayId →
        tomographicRayTransform left ray view rayId =
          tomographicRayTransform right ray view rayId := by
  constructor
  · intro energyZero view viewMem rayId rayMem weight_positive
    have viewEnergyZero :
        (∑ selectedRay ∈ rays,
          weight view selectedRay *
            (tomographicRayTransform
              (fun coordinate => left coordinate - right coordinate)
              ray view selectedRay) ^ 2) = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedView selectedMem =>
        Finset.sum_nonneg (fun selectedRay selectedRayMem =>
          mul_nonneg (weight_nonnegative selectedView selectedRay)
            (sq_nonneg (tomographicRayTransform
              (fun coordinate => left coordinate - right coordinate)
              ray selectedView selectedRay))))).mp
        (by simpa [tomographicWeightedRayNormalEnergyOn] using energyZero)
        view viewMem
    have termZero :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedRay selectedRayMem =>
        mul_nonneg (weight_nonnegative view selectedRay)
          (sq_nonneg (tomographicRayTransform
            (fun coordinate => left coordinate - right coordinate)
            ray view selectedRay)))).mp viewEnergyZero rayId rayMem
    have squareZero :
        (tomographicRayTransform
          (fun coordinate => left coordinate - right coordinate)
          ray view rayId) ^ 2 = 0 := by
      exact (mul_eq_zero.mp termZero).resolve_left
        (ne_of_gt weight_positive)
    have differenceZero := sq_eq_zero_iff.mp squareZero
    have transform_sub := congrFun
      (tomographicRayTransform_sub left right ray) view
    rw [congrFun transform_sub rayId] at differenceZero
    exact sub_eq_zero.mp differenceZero
  · intro agreement
    unfold tomographicWeightedRayNormalEnergyOn
    apply (Finset.sum_eq_zero_iff_of_nonneg (fun view viewMem =>
      Finset.sum_nonneg (fun rayId rayMem =>
        mul_nonneg (weight_nonnegative view rayId)
          (sq_nonneg (tomographicRayTransform
            (fun coordinate => left coordinate - right coordinate)
            ray view rayId))))).mpr
    intro view viewMem
    apply (Finset.sum_eq_zero_iff_of_nonneg (fun rayId rayMem =>
      mul_nonneg (weight_nonnegative view rayId)
        (sq_nonneg (tomographicRayTransform
          (fun coordinate => left coordinate - right coordinate)
          ray view rayId)))).mpr
    intro rayId rayMem
    by_cases weight_positive : 0 < weight view rayId
    · have equal := agreement view viewMem rayId rayMem weight_positive
      have transform_sub := congrFun
        (tomographicRayTransform_sub left right ray) view
      rw [congrFun transform_sub rayId]
      simp [sub_eq_zero.mpr equal]
    · have weight_zero : weight view rayId = 0 := by
        exact le_antisymm (not_lt.mp weight_positive)
          (weight_nonnegative view rayId)
      simp [weight_zero]

theorem tomographicWeightedRayNormalEnergy_difference_zero_iff_agreement_on_positive_weight
    [Fintype View] [Fintype Ray]
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (weight_nonnegative : ∀ view rayId, 0 ≤ weight view rayId) :
    tomographicWeightedRayNormalEnergy weight
        (fun coordinate => left coordinate - right coordinate) ray = 0 ↔
      ∀ view rayId, 0 < weight view rayId →
        tomographicRayTransform left ray view rayId =
          tomographicRayTransform right ray view rayId := by
  simpa [tomographicWeightedRayNormalEnergyOn,
    tomographicWeightedRayNormalEnergy] using
    (tomographicWeightedRayNormalEnergyOn_difference_zero_iff_agreement_on_positive_weight
      (views := Finset.univ) (rays := Finset.univ) weight left right ray
      weight_nonnegative)

theorem tomographicWeightedRayNormalEnergy_difference_pos_of_exists_positive_weight_disagreement
    [Fintype View] [Fintype Ray]
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (weight_nonnegative : ∀ view rayId, 0 ≤ weight view rayId)
    (witness : ∃ view rayId, 0 < weight view rayId ∧
      tomographicRayTransform left ray view rayId ≠
        tomographicRayTransform right ray view rayId) :
    0 < tomographicWeightedRayNormalEnergy weight
        (fun coordinate => left coordinate - right coordinate) ray := by
  have energy_nonnegative :
      0 ≤ tomographicWeightedRayNormalEnergy weight
        (fun coordinate => left coordinate - right coordinate) ray := by
    simpa [tomographicWeightedRayNormalEnergy] using
      (tomographicWeightedRayNormalEnergyOn_nonnegative
        (views := Finset.univ) (rays := Finset.univ) weight
        (fun coordinate => left coordinate - right coordinate) ray
        weight_nonnegative)
  have energy_ne_zero :
      tomographicWeightedRayNormalEnergy weight
        (fun coordinate => left coordinate - right coordinate) ray ≠ 0 := by
    intro energy_zero
    have agreement :=
      (tomographicWeightedRayNormalEnergy_difference_zero_iff_agreement_on_positive_weight
        weight left right ray weight_nonnegative).mp energy_zero
    rcases witness with ⟨view, rayId, weight_positive, disagreement⟩
    exact disagreement (agreement view rayId weight_positive)
  exact lt_of_le_of_ne energy_nonnegative (Ne.symm energy_ne_zero)

theorem tomographicRayNormalEnergyOn_union_views
    [DecidableEq View]
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (rays : Finset Ray)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayNormalEnergyOn (first ∪ second) rays image ray =
      tomographicRayNormalEnergyOn first rays image ray +
        tomographicRayNormalEnergyOn second rays image ray := by
  unfold tomographicRayNormalEnergyOn
  rw [Finset.sum_union disjoint]

theorem tomographicRayNormalEnergyOn_union_rays
    [DecidableEq Ray]
    (views : Finset View)
    (first second : Finset Ray)
    (disjoint : Disjoint first second)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayNormalEnergyOn views (first ∪ second) image ray =
      tomographicRayNormalEnergyOn views first image ray +
        tomographicRayNormalEnergyOn views second image ray := by
  simp [tomographicRayNormalEnergyOn, Finset.sum_union disjoint,
    Finset.sum_add_distrib, add_assoc, add_left_comm, add_comm]

theorem tomographicRayNormalEnergyOn_rowwise_bound
    (views : Finset View)
    (rays : Finset Ray)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (ray_bound : View → Ray → ℝ)
    (ray_bound_nonnegative : ∀ view rayId,
      0 ≤ ray_bound view rayId)
    (pointwise_bound : ∀ view rayId,
      |tomographicRayTransform image ray view rayId| ≤
        ray_bound view rayId) :
    tomographicRayNormalEnergyOn views rays image ray ≤
      ∑ view ∈ views, ∑ rayId ∈ rays, (ray_bound view rayId) ^ 2 := by
  unfold tomographicRayNormalEnergyOn
  apply Finset.sum_le_sum
  intro view viewMem
  apply Finset.sum_le_sum
  intro rayId rayMem
  have pointwise := pointwise_bound view rayId
  have squared_bound :
      |tomographicRayTransform image ray view rayId| ^ 2 ≤
        (ray_bound view rayId) ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg (ray_bound_nonnegative view rayId)] using pointwise
  simpa [sq_abs] using squared_bound

theorem tomographicRayNormalEnergyOn_difference_rowwise_bound
    (views : Finset View)
    (rays : Finset Ray)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (ray_bound : View → Ray → ℝ)
    (ray_bound_nonnegative : ∀ view rayId,
      0 ≤ ray_bound view rayId)
    (pointwise_bound : ∀ view rayId,
      |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId| ≤
        ray_bound view rayId) :
    tomographicRayNormalEnergyOn views rays
        (fun coordinate => left coordinate - right coordinate) ray ≤
      ∑ view ∈ views, ∑ rayId ∈ rays, (ray_bound view rayId) ^ 2 := by
  apply tomographicRayNormalEnergyOn_rowwise_bound views rays
    (fun coordinate => left coordinate - right coordinate) ray ray_bound
    ray_bound_nonnegative
  intro view rayId
  rw [congrFun (congrFun (tomographicRayTransform_sub left right ray) view) rayId]
  exact pointwise_bound view rayId

theorem tomographicRayNormalEnergyOn_univ_eq
    [Fintype View] [Fintype Ray]
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayNormalEnergyOn Finset.univ Finset.univ image ray =
      tomographicRayNormalEnergy image ray := by
  classical
  change tomographicRayNormalEnergy image ray = tomographicRayNormalEnergy image ray
  rfl

theorem tomographicRayNormalEnergyOn_zero_iff_pointwise_invisible
    (views : Finset View)
    (rays : Finset Ray)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayNormalEnergyOn views rays image ray = 0 ↔
      ∀ view ∈ views, ∀ rayId ∈ rays,
        tomographicRayTransform image ray view rayId = 0 := by
  constructor
  · intro energyZero view viewMem rayId rayMem
    have viewEnergyZero :
        (∑ selectedRay ∈ rays,
          (tomographicRayTransform image ray view selectedRay) ^ 2) = 0 :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedView selectedMem =>
        Finset.sum_nonneg (fun selectedRay _ =>
          sq_nonneg (tomographicRayTransform image ray selectedView selectedRay)))).mp
        (by simpa [tomographicRayNormalEnergyOn] using energyZero) view viewMem
    have raySquareZero :=
      (Finset.sum_eq_zero_iff_of_nonneg (fun selectedRay selectedMem =>
        sq_nonneg (tomographicRayTransform image ray view selectedRay))).mp
        viewEnergyZero rayId rayMem
    exact sq_eq_zero_iff.mp raySquareZero
  · intro everyZero
    unfold tomographicRayNormalEnergyOn
    apply (Finset.sum_eq_zero_iff_of_nonneg (fun view viewMem =>
      Finset.sum_nonneg (fun rayId rayMem =>
        sq_nonneg (tomographicRayTransform image ray view rayId)))).mpr
    intro view viewMem
    apply (Finset.sum_eq_zero_iff_of_nonneg (fun rayId rayMem =>
      sq_nonneg (tomographicRayTransform image ray view rayId))).mpr
    intro rayId rayMem
    simp [everyZero view viewMem rayId rayMem]

theorem tomographicWeightedRayNormalEnergyOn_zero_implies_pointwise_invisible_of_uniform_positive_floor
    (views : Finset View)
    (rays : Finset Ray)
    (weight_floor : ℝ)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (weight_floor_pos : 0 < weight_floor)
    (weight_floor_le : ∀ view rayId, weight_floor ≤ weight view rayId)
    (energy_zero : tomographicWeightedRayNormalEnergyOn views rays weight image ray = 0) :
    ∀ view ∈ views, ∀ rayId ∈ rays,
      tomographicRayTransform image ray view rayId = 0 := by
  have unweighted_nonnegative := tomographicRayNormalEnergyOn_nonnegative
    views rays image ray
  have lower := tomographicWeightedRayNormalEnergyOn_lower_bound_of_uniform_weight
    views rays weight_floor weight image ray (le_of_lt weight_floor_pos)
    weight_floor_le
  have floor_energy_zero :
      weight_floor * tomographicRayNormalEnergyOn views rays image ray = 0 := by
    apply le_antisymm
    · calc
        weight_floor * tomographicRayNormalEnergyOn views rays image ray ≤
            tomographicWeightedRayNormalEnergyOn views rays weight image ray := lower
        _ = 0 := energy_zero
    · exact mul_nonneg (le_of_lt weight_floor_pos) unweighted_nonnegative
  have energy_zero_unweighted :
      tomographicRayNormalEnergyOn views rays image ray = 0 :=
    (mul_eq_zero.mp floor_energy_zero).resolve_left (ne_of_gt weight_floor_pos)
  exact (tomographicRayNormalEnergyOn_zero_iff_pointwise_invisible
    views rays image ray).mp energy_zero_unweighted

theorem tomographicRayNormalEnergyOn_difference_zero_iff_equal_selected_rays
    (views : Finset View)
    (rays : Finset Ray)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayNormalEnergyOn views rays
        (fun coordinate => left coordinate - right coordinate) ray = 0 ↔
      ∀ view ∈ views, ∀ rayId ∈ rays,
        tomographicRayTransform left ray view rayId =
          tomographicRayTransform right ray view rayId := by
  constructor
  · intro energyZero view viewMem rayId rayMem
    have invisible :=
      (tomographicRayNormalEnergyOn_zero_iff_pointwise_invisible views rays
        (fun coordinate => left coordinate - right coordinate) ray).mp
        energyZero view viewMem rayId rayMem
    have transform_sub := congrFun
      (tomographicRayTransform_sub left right ray) view
    rw [congrFun transform_sub rayId] at invisible
    exact sub_eq_zero.mp invisible
  · intro equal
    apply (tomographicRayNormalEnergyOn_zero_iff_pointwise_invisible views rays
      (fun coordinate => left coordinate - right coordinate) ray).mpr
    intro view viewMem rayId rayMem
    have transform_sub := congrFun
      (tomographicRayTransform_sub left right ray) view
    rw [congrFun transform_sub rayId]
    exact sub_eq_zero.mpr (equal view viewMem rayId rayMem)

theorem tomographicRayNormalEnergyOn_difference_rowwise_lower_bound
    (views : Finset View)
    (rays : Finset Ray)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (margin : ℝ)
    (margin_nonnegative : 0 ≤ margin)
    (pointwise_lower_bound : ∀ view ∈ views, ∀ rayId ∈ rays,
      margin ≤ |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId|) :
    views.card * rays.card * margin ^ 2 ≤
      tomographicRayNormalEnergyOn views rays
        (fun coordinate => left coordinate - right coordinate) ray := by
  unfold tomographicRayNormalEnergyOn
  calc
    views.card * rays.card * margin ^ 2 =
        ∑ view ∈ views, ∑ rayId ∈ rays, margin ^ 2 := by
      simp [mul_assoc]
    _ ≤ ∑ view ∈ views, ∑ rayId ∈ rays,
        (tomographicRayTransform
          (fun coordinate => left coordinate - right coordinate)
          ray view rayId) ^ 2 := by
      apply Finset.sum_le_sum
      intro view viewMem
      apply Finset.sum_le_sum
      intro rayId rayMem
      have pointwise := pointwise_lower_bound view viewMem rayId rayMem
      have squared_bound :
          margin ^ 2 ≤
            |tomographicRayTransform left ray view rayId -
              tomographicRayTransform right ray view rayId| ^ 2 := by
        apply (sq_le_sq).2
        simpa [abs_of_nonneg margin_nonnegative] using pointwise
      rw [congrFun (congrFun (tomographicRayTransform_sub left right ray) view)
        rayId]
      simpa [sq_abs] using squared_bound

theorem tomographicWeightedRayNormalEnergyOn_difference_rowwise_lower_bound
    (views : Finset View)
    (rays : Finset Ray)
    (weight_floor : ℝ)
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (margin : ℝ)
    (margin_nonnegative : 0 ≤ margin)
    (weight_floor_pos : 0 < weight_floor)
    (weight_floor_le : ∀ view rayId, weight_floor ≤ weight view rayId)
    (pointwise_lower_bound : ∀ view ∈ views, ∀ rayId ∈ rays,
      margin ≤ |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId|) :
    weight_floor * (views.card * rays.card * margin ^ 2) ≤
      tomographicWeightedRayNormalEnergyOn views rays weight
        (fun coordinate => left coordinate - right coordinate) ray := by
  have unweighted_lower := tomographicRayNormalEnergyOn_difference_rowwise_lower_bound
    views rays left right ray margin margin_nonnegative pointwise_lower_bound
  have weighted_lower := tomographicWeightedRayNormalEnergyOn_lower_bound_of_uniform_weight
    views rays weight_floor weight
      (fun coordinate => left coordinate - right coordinate) ray
      (le_of_lt weight_floor_pos) weight_floor_le
  exact le_trans
    (mul_le_mul_of_nonneg_left unweighted_lower (le_of_lt weight_floor_pos))
    weighted_lower

theorem tomographicWeightedRayNormalEnergyOn_difference_lower_bound_of_weight_floor
    (views : Finset View)
    (rays : Finset Ray)
    (weight_floor : View → Ray → ℝ)
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (margin : ℝ)
    (margin_nonnegative : 0 ≤ margin)
    (weight_floor_nonnegative : ∀ view rayId, 0 ≤ weight_floor view rayId)
    (weight_floor_le : ∀ view rayId,
      weight_floor view rayId ≤ weight view rayId)
    (pointwise_lower_bound : ∀ view ∈ views, ∀ rayId ∈ rays,
      margin ≤ |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId|) :
    ∑ view ∈ views, ∑ rayId ∈ rays,
        weight_floor view rayId * margin ^ 2 ≤
      tomographicWeightedRayNormalEnergyOn views rays weight
        (fun coordinate => left coordinate - right coordinate) ray := by
  unfold tomographicWeightedRayNormalEnergyOn
  apply Finset.sum_le_sum
  intro view viewMem
  apply Finset.sum_le_sum
  intro rayId rayMem
  have pointwise := pointwise_lower_bound view viewMem rayId rayMem
  have square_lower :
      margin ^ 2 ≤
        |tomographicRayTransform left ray view rayId -
          tomographicRayTransform right ray view rayId| ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg margin_nonnegative] using pointwise
  have weighted_square_lower :
      weight_floor view rayId * margin ^ 2 ≤
        weight_floor view rayId *
          (tomographicRayTransform
            (fun coordinate => left coordinate - right coordinate)
            ray view rayId) ^ 2 := by
    rw [congrFun (congrFun (tomographicRayTransform_sub left right ray) view)
      rayId]
    simpa [sq_abs] using
      (mul_le_mul_of_nonneg_left square_lower
        (weight_floor_nonnegative view rayId))
  exact le_trans weighted_square_lower
    (mul_le_mul_of_nonneg_right
      (weight_floor_le view rayId)
      (sq_nonneg (tomographicRayTransform
        (fun coordinate => left coordinate - right coordinate)
        ray view rayId)))

theorem tomographicWeightedRayNormalEnergy_difference_lower_bound_of_weight_floor
    [Fintype View] [Fintype Ray]
    (weight_floor : View → Ray → ℝ)
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (margin : ℝ)
    (margin_nonnegative : 0 ≤ margin)
    (weight_floor_nonnegative : ∀ view rayId, 0 ≤ weight_floor view rayId)
    (weight_floor_le : ∀ view rayId,
      weight_floor view rayId ≤ weight view rayId)
    (pointwise_lower_bound : ∀ view rayId,
      margin ≤ |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId|) :
    (∑ view, ∑ rayId, weight_floor view rayId) * margin ^ 2 ≤
      tomographicWeightedRayNormalEnergy weight
        (fun coordinate => left coordinate - right coordinate) ray := by
  classical
  have selected :=
    tomographicWeightedRayNormalEnergyOn_difference_lower_bound_of_weight_floor
      (views := Finset.univ) (rays := Finset.univ) weight_floor weight left right ray
      margin margin_nonnegative weight_floor_nonnegative weight_floor_le (by
        intro view viewMem rayId rayMem
        exact pointwise_lower_bound view rayId)
  calc
    (∑ view, ∑ rayId, weight_floor view rayId) * margin ^ 2 =
        ∑ view, ∑ rayId, weight_floor view rayId * margin ^ 2 := by
      rw [Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro view viewMem
      rw [Finset.sum_mul]
    _ ≤ tomographicWeightedRayNormalEnergy weight
        (fun coordinate => left coordinate - right coordinate) ray := by
      simpa [tomographicWeightedRayNormalEnergy] using selected

theorem tomographicWeightedRayNormalEnergy_difference_pos_of_positive_floor_and_margin
    [Fintype View] [Fintype Ray]
    (weight_floor : View → Ray → ℝ)
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (margin : ℝ)
    (margin_pos : 0 < margin)
    (weight_floor_nonnegative : ∀ view rayId, 0 ≤ weight_floor view rayId)
    (weight_floor_le : ∀ view rayId,
      weight_floor view rayId ≤ weight view rayId)
    (pointwise_lower_bound : ∀ view rayId,
      margin ≤ |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId|)
    (positive_floor : ∃ view rayId, 0 < weight_floor view rayId) :
    0 < tomographicWeightedRayNormalEnergy weight
        (fun coordinate => left coordinate - right coordinate) ray := by
  have witness : ∃ view rayId, 0 < weight view rayId ∧
      tomographicRayTransform left ray view rayId ≠
        tomographicRayTransform right ray view rayId := by
    rcases positive_floor with ⟨view, rayId, floor_positive⟩
    refine ⟨view, rayId,
      lt_of_lt_of_le floor_positive (weight_floor_le view rayId), ?_⟩
    intro equal
    have margin_le_zero : margin ≤ 0 := by
      simpa [equal] using (pointwise_lower_bound view rayId)
    exact (not_lt_of_ge margin_le_zero) margin_pos
  exact tomographicWeightedRayNormalEnergy_difference_pos_of_exists_positive_weight_disagreement
    weight left right ray
    (fun view rayId => le_trans (weight_floor_nonnegative view rayId)
      (weight_floor_le view rayId)) witness

theorem tomographicWeightedRayNormalEnergy_difference_rowwise_lower_bound
    [Fintype View] [Fintype Ray]
    (weight_floor : ℝ)
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (margin : ℝ)
    (margin_nonnegative : 0 ≤ margin)
    (weight_floor_pos : 0 < weight_floor)
    (weight_floor_le : ∀ view rayId, weight_floor ≤ weight view rayId)
    (pointwise_lower_bound : ∀ view rayId,
      margin ≤ |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId|) :
    weight_floor * (Fintype.card View * Fintype.card Ray * margin ^ 2) ≤
      tomographicWeightedRayNormalEnergy weight
        (fun coordinate => left coordinate - right coordinate) ray := by
  classical
  have selected := tomographicWeightedRayNormalEnergyOn_difference_rowwise_lower_bound
    (views := Finset.univ) (rays := Finset.univ) weight_floor weight left right ray
      margin margin_nonnegative weight_floor_pos weight_floor_le (by
        intro view viewMem rayId rayMem
        exact pointwise_lower_bound view rayId)
  simpa [tomographicWeightedRayNormalEnergyOn,
    tomographicWeightedRayNormalEnergy, mul_assoc] using selected

theorem tomographicWeightedRayNormalEnergyOn_union_views
    [DecidableEq View]
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (rays : Finset Ray)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicWeightedRayNormalEnergyOn (first ∪ second) rays weight image ray =
      tomographicWeightedRayNormalEnergyOn first rays weight image ray +
        tomographicWeightedRayNormalEnergyOn second rays weight image ray := by
  unfold tomographicWeightedRayNormalEnergyOn
  rw [Finset.sum_union disjoint]

theorem tomographicWeightedRayNormalEnergyOn_union_rays
    [DecidableEq Ray]
    (views : Finset View)
    (first second : Finset Ray)
    (disjoint : Disjoint first second)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicWeightedRayNormalEnergyOn views (first ∪ second) weight image ray =
      tomographicWeightedRayNormalEnergyOn views first weight image ray +
        tomographicWeightedRayNormalEnergyOn views second weight image ray := by
  simp [tomographicWeightedRayNormalEnergyOn, Finset.sum_union disjoint,
    Finset.sum_add_distrib, add_assoc, add_left_comm, add_comm]

theorem tomographicRayNormalEnergy_difference_rowwise_lower_bound
    [Fintype View] [Fintype Ray]
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (margin : ℝ)
    (margin_nonnegative : 0 ≤ margin)
    (pointwise_lower_bound : ∀ view rayId,
      margin ≤ |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId|) :
    Fintype.card View * Fintype.card Ray * margin ^ 2 ≤
      tomographicRayNormalEnergy
        (fun coordinate => left coordinate - right coordinate) ray := by
  classical
  have selected := tomographicRayNormalEnergyOn_difference_rowwise_lower_bound
    (views := Finset.univ) (rays := Finset.univ) left right ray margin
    margin_nonnegative (by
      intro view viewMem rayId rayMem
      exact pointwise_lower_bound view rayId)
  simpa [tomographicRayNormalEnergyOn, tomographicRayNormalEnergy, mul_assoc]
    using selected

theorem tomographicRayNormalEnergy_nonnegative
    [Fintype View] [Fintype Ray]
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    0 ≤ tomographicRayNormalEnergy image ray := by
  unfold tomographicRayNormalEnergy
  exact Finset.sum_nonneg (fun view _ =>
    Finset.sum_nonneg (fun rayId _ =>
      sq_nonneg (tomographicRayTransform image ray view rayId)))

theorem tomographicRayNormalEnergy_rowwise_bound
    [Fintype View] [Fintype Ray]
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (ray_bound : View → Ray → ℝ)
    (ray_bound_nonnegative : ∀ view rayId,
      0 ≤ ray_bound view rayId)
    (pointwise_bound : ∀ view rayId,
      |tomographicRayTransform image ray view rayId| ≤
        ray_bound view rayId) :
    tomographicRayNormalEnergy image ray ≤
      ∑ view, ∑ rayId, (ray_bound view rayId) ^ 2 := by
  unfold tomographicRayNormalEnergy
  apply Finset.sum_le_sum
  intro view viewMem
  apply Finset.sum_le_sum
  intro rayId rayMem
  have pointwise := pointwise_bound view rayId
  have squared_bound :
      |tomographicRayTransform image ray view rayId| ^ 2 ≤
        (ray_bound view rayId) ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg (ray_bound_nonnegative view rayId)] using pointwise
  simpa [sq_abs] using squared_bound

theorem tomographicRayNormalEnergy_difference_rowwise_bound
    [Fintype View] [Fintype Ray]
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (ray_bound : View → Ray → ℝ)
    (ray_bound_nonnegative : ∀ view rayId,
      0 ≤ ray_bound view rayId)
    (pointwise_bound : ∀ view rayId,
      |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId| ≤
        ray_bound view rayId) :
    tomographicRayNormalEnergy (fun coordinate =>
      left coordinate - right coordinate) ray ≤
      ∑ view, ∑ rayId, (ray_bound view rayId) ^ 2 := by
  apply tomographicRayNormalEnergy_rowwise_bound
    (fun coordinate => left coordinate - right coordinate) ray ray_bound
    ray_bound_nonnegative
  intro view rayId
  rw [congrFun (congrFun (tomographicRayTransform_sub left right ray) view) rayId]
  exact pointwise_bound view rayId

theorem tomographicRayNormalEnergy_zero_iff_pointwise_invisible
    [Fintype View] [Fintype Ray]
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayNormalEnergy image ray = 0 ↔
      ∀ view rayId, tomographicRayTransform image ray view rayId = 0 := by
  constructor
  · intro energyZero view rayId
    have onZero :
        tomographicRayNormalEnergyOn Finset.univ Finset.univ image ray = 0 := by
      simpa [tomographicRayNormalEnergyOn, tomographicRayNormalEnergy] using energyZero
    have pointwise :=
      (tomographicRayNormalEnergyOn_zero_iff_pointwise_invisible
        (views := Finset.univ) (rays := Finset.univ) image ray).mp onZero
    exact pointwise view (by simp) rayId (by simp)
  · intro everyZero
    have onZero :
        tomographicRayNormalEnergyOn Finset.univ Finset.univ image ray = 0 :=
      (tomographicRayNormalEnergyOn_zero_iff_pointwise_invisible
        (views := Finset.univ) (rays := Finset.univ) image ray).mpr (by
          intro view _ rayId _
          exact everyZero view rayId)
    simpa [tomographicRayNormalEnergyOn, tomographicRayNormalEnergy] using onZero

theorem tomographicRayNormalEnergy_difference_zero_iff_equal_rays
    [Fintype View] [Fintype Ray]
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayNormalEnergy (fun coordinate =>
      left coordinate - right coordinate) ray = 0 ↔
      ∀ view rayId,
        tomographicRayTransform left ray view rayId =
          tomographicRayTransform right ray view rayId := by
  constructor
  · intro energyZero view rayId
    have invisible :=
      (tomographicRayNormalEnergy_zero_iff_pointwise_invisible
        (fun coordinate => left coordinate - right coordinate) ray).mp
        energyZero view rayId
    have transform_sub := congrFun
      (tomographicRayTransform_sub left right ray) view
    rw [congrFun transform_sub rayId] at invisible
    exact sub_eq_zero.mp invisible
  · intro equal
    apply (tomographicRayNormalEnergy_zero_iff_pointwise_invisible
      (fun coordinate => left coordinate - right coordinate) ray).mpr
    intro view rayId
    have transform_sub := congrFun
      (tomographicRayTransform_sub left right ray) view
    rw [congrFun transform_sub rayId]
    exact sub_eq_zero.mpr (equal view rayId)

/-- Every registered ray sample is contained in the declared finite universeSet. -/
def TomographicRaySupport
    (universeSet : Finset Coordinate)
    (ray : View → Ray → Sample → Coordinate) : Prop :=
  ∀ view rayId sample, ray view rayId sample ∈ universeSet

theorem tomographicRayTransformOn_congr_on_support
    [DecidableEq Coordinate]
    (samples : Finset Sample)
    (universeSet : Finset Coordinate)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport universeSet ray)
    (agree_on_universe : ∀ coordinate, coordinate ∈ universeSet →
      left coordinate = right coordinate) :
    tomographicRayTransformOn samples left ray =
      tomographicRayTransformOn samples right ray := by
  funext view
  funext rayId
  simp only [tomographicRayTransformOn]
  apply Finset.sum_congr rfl
  intro sample sampleMem
  exact agree_on_universe (ray view rayId sample)
    (support view rayId sample)

theorem tomographicRayTransformOn_bandProjection_eq_of_support
    [DecidableEq Coordinate]
    (samples : Finset Sample)
    (band : Finset Coordinate)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport band ray) :
    tomographicRayTransformOn samples (tomographicBandProjection band image) ray =
      tomographicRayTransformOn samples image ray := by
  apply tomographicRayTransformOn_congr_on_support samples band
    (tomographicBandProjection band image) image ray support
  intro coordinate membership
  simp [tomographicBandProjection, membership]

theorem tomographicRayTransform_congr_on_support
    [DecidableEq Coordinate]
    (universeSet : Finset Coordinate)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport universeSet ray)
    (agree_on_universe : ∀ coordinate, coordinate ∈ universeSet →
      left coordinate = right coordinate) :
    tomographicRayTransform left ray = tomographicRayTransform right ray := by
  funext view
  funext rayId
  simp only [tomographicRayTransform]
  apply Finset.sum_congr rfl
  intro sample _
  exact agree_on_universe (ray view rayId sample)
    (support view rayId sample)

theorem tomographicRayTransform_bandProjection_eq_of_support
    [DecidableEq Coordinate]
    (band : Finset Coordinate)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport band ray) :
    tomographicRayTransform (tomographicBandProjection band image) ray =
      tomographicRayTransform image ray := by
  apply tomographicRayTransform_congr_on_support band
    (tomographicBandProjection band image) image ray support
  intro coordinate membership
  simp [tomographicBandProjection, membership]

theorem tomographicRayNormalEnergyOn_congr_on_support
    [DecidableEq Coordinate]
    (views : Finset View)
    (rays : Finset Ray)
    (universeSet : Finset Coordinate)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport universeSet ray)
    (agree_on_universe : ∀ coordinate, coordinate ∈ universeSet →
      left coordinate = right coordinate) :
    tomographicRayNormalEnergyOn views rays left ray =
      tomographicRayNormalEnergyOn views rays right ray := by
  have transform_equal := tomographicRayTransform_congr_on_support universeSet
    left right ray support agree_on_universe
  unfold tomographicRayNormalEnergyOn
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  rw [congrFun (congrFun transform_equal view) rayId]

theorem tomographicRayNormalEnergy_congr_on_support
    [Fintype View] [Fintype Ray]
    [DecidableEq Coordinate]
    (universeSet : Finset Coordinate)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport universeSet ray)
    (agree_on_universe : ∀ coordinate, coordinate ∈ universeSet →
      left coordinate = right coordinate) :
    tomographicRayNormalEnergy left ray =
      tomographicRayNormalEnergy right ray := by
  have transform_equal := tomographicRayTransform_congr_on_support universeSet
    left right ray support agree_on_universe
  unfold tomographicRayNormalEnergy
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  rw [congrFun (congrFun transform_equal view) rayId]

theorem tomographicWeightedRayNormalEnergyOn_congr_on_support
    [DecidableEq Coordinate]
    (views : Finset View)
    (rays : Finset Ray)
    (universeSet : Finset Coordinate)
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport universeSet ray)
    (agree_on_universe : ∀ coordinate, coordinate ∈ universeSet →
      left coordinate = right coordinate) :
    tomographicWeightedRayNormalEnergyOn views rays weight left ray =
      tomographicWeightedRayNormalEnergyOn views rays weight right ray := by
  have transform_equal := tomographicRayTransform_congr_on_support universeSet
    left right ray support agree_on_universe
  unfold tomographicWeightedRayNormalEnergyOn
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  rw [congrFun (congrFun transform_equal view) rayId]

theorem tomographicWeightedRayNormalEnergy_congr_on_support
    [DecidableEq Coordinate] [Fintype View] [Fintype Ray]
    (universeSet : Finset Coordinate)
    (weight : View → Ray → ℝ)
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport universeSet ray)
    (agree_on_universe : ∀ coordinate, coordinate ∈ universeSet →
      left coordinate = right coordinate) :
    tomographicWeightedRayNormalEnergy weight left ray =
      tomographicWeightedRayNormalEnergy weight right ray := by
  have transform_equal := tomographicRayTransform_congr_on_support universeSet
    left right ray support agree_on_universe
  unfold tomographicWeightedRayNormalEnergy
  apply Finset.sum_congr rfl
  intro view viewMem
  apply Finset.sum_congr rfl
  intro rayId rayMem
  rw [congrFun (congrFun transform_equal view) rayId]

theorem tomographicWeightedRayNormalEnergyOn_bandProjection_eq_of_support
    [DecidableEq Coordinate]
    (views : Finset View)
    (rays : Finset Ray)
    (band : Finset Coordinate)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport band ray) :
    tomographicWeightedRayNormalEnergyOn views rays weight
        (tomographicBandProjection band image) ray =
      tomographicWeightedRayNormalEnergyOn views rays weight image ray := by
  apply tomographicWeightedRayNormalEnergyOn_congr_on_support views rays band
    weight (tomographicBandProjection band image) image ray support
  intro coordinate membership
  simp [tomographicBandProjection, membership]

theorem tomographicWeightedRayNormalEnergy_bandProjection_eq_of_support
    [DecidableEq Coordinate] [Fintype View] [Fintype Ray]
    (band : Finset Coordinate)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (support : TomographicRaySupport band ray) :
    tomographicWeightedRayNormalEnergy weight
        (tomographicBandProjection band image) ray =
      tomographicWeightedRayNormalEnergy weight image ray := by
  simpa [tomographicWeightedRayNormalEnergy] using
    (tomographicWeightedRayNormalEnergyOn_bandProjection_eq_of_support
      (views := Finset.univ) (rays := Finset.univ) band weight image ray support)

/-- Without complete support, the error introduced by band projection is
bounded by the absolute mass of the ray samples outside the declared band.
This is a finite truncation bound, not a continuous inverse or a physical
diffraction theorem. -/
theorem tomographicRayTransform_bandProjection_error_bound
    [DecidableEq Coordinate]
    (band : Finset Coordinate)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    ∀ view rayId,
      |tomographicRayTransform image ray view rayId -
        tomographicRayTransform (tomographicBandProjection band image) ray view rayId| ≤
        ∑ sample, if ray view rayId sample ∈ band then 0 else
          |image (ray view rayId sample)| := by
  intro view rayId
  simp only [tomographicRayTransform]
  rw [← Finset.sum_sub_distrib]
  calc
    |∑ sample, (image (ray view rayId sample) -
        tomographicBandProjection band image (ray view rayId sample))| ≤
        ∑ sample, |image (ray view rayId sample) -
          tomographicBandProjection band image (ray view rayId sample)| :=
      Finset.abs_sum_le_sum_abs _ _
    _ = ∑ sample, if ray view rayId sample ∈ band then 0 else
          |image (ray view rayId sample)| := by
      apply Finset.sum_congr rfl
      intro sample _
      by_cases membership : ray view rayId sample ∈ band
      · simp [tomographicBandProjection, membership]
      · simp [tomographicBandProjection, membership]

theorem tomographicWeightedRayNormalEnergyOn_bandProjection_error_bound
    [DecidableEq Coordinate]
    (views : Finset View)
    (rays : Finset Ray)
    (band : Finset Coordinate)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (weight_nonnegative : ∀ view rayId, 0 ≤ weight view rayId) :
    tomographicWeightedRayNormalEnergyOn views rays weight
        (fun coordinate => image coordinate -
          tomographicBandProjection band image coordinate) ray ≤
      ∑ view ∈ views, ∑ rayId ∈ rays,
        weight view rayId *
          (∑ sample, if ray view rayId sample ∈ band then 0 else
            |image (ray view rayId sample)|) ^ 2 := by
  let ray_bound : View → Ray → ℝ := fun view rayId =>
    ∑ sample, if ray view rayId sample ∈ band then 0 else
      |image (ray view rayId sample)|
  have ray_bound_nonnegative : ∀ view rayId, 0 ≤ ray_bound view rayId := by
    intro view rayId
    unfold ray_bound
    apply Finset.sum_nonneg
    intro sample _
    by_cases membership : ray view rayId sample ∈ band
    · simp [membership]
    · simp only [if_neg membership]
      exact abs_nonneg _
  have energy_bound := tomographicWeightedRayNormalEnergyOn_difference_rowwise_bound
    views rays weight image (tomographicBandProjection band image) ray ray_bound
      weight_nonnegative ray_bound_nonnegative (by
        intro view rayId
        simpa [ray_bound] using
          (tomographicRayTransform_bandProjection_error_bound band image ray
            view rayId))
  simpa [ray_bound] using energy_bound

theorem tomographicWeightedRayNormalEnergy_bandProjection_error_bound
    [DecidableEq Coordinate] [Fintype View] [Fintype Ray]
    (band : Finset Coordinate)
    (weight : View → Ray → ℝ)
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (weight_nonnegative : ∀ view rayId, 0 ≤ weight view rayId) :
    tomographicWeightedRayNormalEnergy weight
        (fun coordinate => image coordinate -
          tomographicBandProjection band image coordinate) ray ≤
      ∑ view, ∑ rayId,
        weight view rayId *
          (∑ sample, if ray view rayId sample ∈ band then 0 else
            |image (ray view rayId sample)|) ^ 2 := by
  simpa [tomographicWeightedRayNormalEnergy] using
    (tomographicWeightedRayNormalEnergyOn_bandProjection_error_bound
      (views := Finset.univ) (rays := Finset.univ) band weight image ray
      weight_nonnegative)

theorem tomographicRayTransform_zero
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayTransform (fun _ => 0) ray =
      fun _ _ => 0 := by
  funext view
  funext rayId
  simp [tomographicRayTransform]

theorem tomographicRayTransform_add
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayTransform (fun coordinate =>
      left coordinate + right coordinate) ray =
      fun view rayId =>
        tomographicRayTransform left ray view rayId +
          tomographicRayTransform right ray view rayId := by
  funext view
  funext rayId
  simp [tomographicRayTransform, Finset.sum_add_distrib]

theorem tomographicRayTransform_smul
    (scalar : ℝ) (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate) :
    tomographicRayTransform (fun coordinate =>
      scalar * image coordinate) ray =
      fun view rayId =>
        scalar * tomographicRayTransform image ray view rayId := by
  funext view
  funext rayId
  simp only [tomographicRayTransform]
  rw [← Finset.mul_sum]

theorem tomographicRayTransform_abs_bound
    (image : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (bound : ℝ)
    (image_bound : ∀ coordinate, |image coordinate| ≤ bound) :
    ∀ view rayId,
      |tomographicRayTransform image ray view rayId| ≤
        Fintype.card Sample * bound := by
  intro view rayId
  simp only [tomographicRayTransform]
  calc
    |∑ sample, image (ray view rayId sample)| ≤
        ∑ sample, |image (ray view rayId sample)| :=
      Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ sample, bound := by
      apply Finset.sum_le_sum
      intro sample _
      exact image_bound (ray view rayId sample)
    _ = Fintype.card Sample * bound := by
      simp

theorem tomographicRayTransform_diff_abs_bound
    (left right : Coordinate → ℝ)
    (ray : View → Ray → Sample → Coordinate)
    (bound : ℝ)
    (pointwise_bound : ∀ coordinate,
      |left coordinate - right coordinate| ≤ bound) :
    ∀ view rayId,
      |tomographicRayTransform left ray view rayId -
        tomographicRayTransform right ray view rayId| ≤
        Fintype.card Sample * bound := by
  intro view rayId
  simp only [tomographicRayTransform]
  rw [← Finset.sum_sub_distrib]
  calc
    |∑ sample, (left (ray view rayId sample) -
        right (ray view rayId sample))| ≤
        ∑ sample, |left (ray view rayId sample) -
          right (ray view rayId sample)| :=
      Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ sample, bound := by
      apply Finset.sum_le_sum
      intro sample _
      exact pointwise_bound (ray view rayId sample)
    _ = Fintype.card Sample * bound := by
      simp

end FiniteRayTransform

end OCKIndividuationMSpaceComposition
