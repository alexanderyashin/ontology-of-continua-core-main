import OCKIndividuationMSpaceComposition.TomographicFrameTaskBridge
import OCKIndividuationMSpaceComposition.TomographicFiniteModalityResidual
import OCKIndividuationMSpaceComposition.TomographicFusionCertificate
import OCKIndividuationMSpaceComposition.TomographicFilteredBackprojection
import OCKIndividuationMSpaceComposition.TomographicRayTransform
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition


/-!
# Finite-modality frame/task bridge

The finite modality family uses the existing weighted-frame and task-decoder
contracts over a product view index.  This is an adapter, not a second decoder:
modality identity is preserved while the established pairwise-resolution proof
is reused unchanged.
-/

section FiniteModalityFrameBridge

variable {Coordinate Modality View Answer : Type*}
  [Fintype Coordinate] [Fintype Modality] [Fintype View]

def tomographicFiniteModalityProjection
    (rows : Modality → View → Coordinate → ℝ) :
    (Coordinate → ℝ) → Modality × View → ℝ :=
  fun state index => tomographicProjection (rows index.1) state index.2

def tomographicFiniteModalityProjectionOperator
    (rows : Modality → View → Coordinate → ℝ) :
    Modality × View → (Coordinate → ℝ) → ℝ :=
  fun index state => tomographicFiniteModalityProjection rows state index

/-! The modality-preserving projection is definitionally the ordinary finite
    projection over the product index.  This adapter is the seam at which a
    source-supplied reconstruction certificate may be reused without
    flattening away modality identity in downstream ledgers. -/

theorem tomographicFiniteModalityProjection_eq_flattened
    (rows : Modality → View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicFiniteModalityProjection rows state =
      tomographicProjection
        (fun index : Modality × View => rows index.1 index.2) state := by
  funext index
  rfl

theorem tomographicFiniteModality_exact_reconstruction_of_fusion_certificate
    (rows : Modality → View → Coordinate → ℝ)
    (certificate :
      TomographicFusionCertificate
        (fun index : Modality × View => rows index.1 index.2))
    (state : Coordinate → ℝ) :
    certificate.reconstruct (tomographicFiniteModalityProjection rows state) =
      state := by
  rw [tomographicFiniteModalityProjection_eq_flattened]
  exact certificate.exact_on_model state

theorem tomographicFiniteModality_injective_of_fusion_certificate
    (rows : Modality → View → Coordinate → ℝ)
    (certificate :
      TomographicFusionCertificate
        (fun index : Modality × View => rows index.1 index.2)) :
    Function.Injective (tomographicFiniteModalityProjection rows) := by
  intro left right same
  calc
    left = certificate.reconstruct
        (tomographicFiniteModalityProjection rows left) :=
      (tomographicFiniteModality_exact_reconstruction_of_fusion_certificate
        rows certificate left).symm
    _ = certificate.reconstruct
        (tomographicFiniteModalityProjection rows right) :=
      congrArg certificate.reconstruct same
    _ = right :=
      tomographicFiniteModality_exact_reconstruction_of_fusion_certificate
        rows certificate right

theorem tomographicFiniteModality_noise_bound_of_fusion_certificate
    (rows : Modality → View → Coordinate → ℝ)
    (certificate :
      TomographicFusionCertificate
        (fun index : Modality × View => rows index.1 index.2))
    (state : Coordinate → ℝ) (data : Modality × View → ℝ) (budget : ℝ)
    (measurementBound :
      dist data (tomographicFiniteModalityProjection rows state) ≤ budget) :
    dist (certificate.reconstruct data) state ≤
      certificate.noiseGain * budget := by
  rw [tomographicFiniteModalityProjection_eq_flattened] at measurementBound
  exact tomographicFusion_noise_bound certificate state data budget
    measurementBound

theorem tomographicFiniteModality_task_noise_bound_of_fusion_certificate
    {Answer : Type*} [PseudoMetricSpace Answer]
    (rows : Modality → View → Coordinate → ℝ)
    (certificate :
      TomographicFusionCertificate
        (fun index : Modality × View => rows index.1 index.2))
    (target : (Coordinate → ℝ) → Answer)
    (target_constant : ℝ) (target_constant_nonnegative : 0 ≤ target_constant)
    (target_modulus : ∀ first second,
      dist (target first) (target second) ≤
        target_constant * dist first second)
    (state : Coordinate → ℝ) (data : Modality × View → ℝ) (budget : ℝ)
    (measurementBound :
      dist data (tomographicFiniteModalityProjection rows state) ≤ budget) :
    dist (target (certificate.reconstruct data)) (target state) ≤
      target_constant * certificate.noiseGain * budget := by
  rw [tomographicFiniteModalityProjection_eq_flattened] at measurementBound
  exact tomographicFusion_task_noise_bound certificate target target_constant
    target_constant_nonnegative target_modulus state data budget
    measurementBound

/-! A complete fused image contains every registered branch.  Consequently a
    source-supplied exact certificate for one selected modality can be lifted
    to an exact reconstruction functional on the full product image by
    restricting the observation to that modality.  The lift is intentionally
    exact-only: no stability or independence claim is inferred for the other
    modalities. -/

def tomographicFiniteModalityBranchReconstruct
    (rows : Modality → View → Coordinate → ℝ)
    (modality : Modality)
    (certificate : TomographicFusionCertificate (rows modality))
    (data : Modality × View → ℝ) : Coordinate → ℝ :=
  certificate.reconstruct (fun view => data (modality, view))

theorem tomographicFiniteModality_exact_reconstruction_of_branch_certificate
    (rows : Modality → View → Coordinate → ℝ)
    (modality : Modality)
    (certificate : TomographicFusionCertificate (rows modality))
    (state : Coordinate → ℝ) :
    tomographicFiniteModalityBranchReconstruct rows modality certificate
        (tomographicFiniteModalityProjection rows state) = state := by
  unfold tomographicFiniteModalityBranchReconstruct
  have branch_image_eq :
      (fun view => tomographicFiniteModalityProjection rows state
        (modality, view)) = tomographicProjection (rows modality) state := by
    funext view
    rfl
  rw [branch_image_eq]
  exact certificate.exact_on_model state

theorem tomographicFiniteModality_injective_of_branch_certificate
    (rows : Modality → View → Coordinate → ℝ)
    (modality : Modality)
    (certificate : TomographicFusionCertificate (rows modality)) :
    Function.Injective (tomographicFiniteModalityProjection rows) := by
  intro left right same
  calc
    left = tomographicFiniteModalityBranchReconstruct rows modality certificate
        (tomographicFiniteModalityProjection rows left) :=
      (tomographicFiniteModality_exact_reconstruction_of_branch_certificate
        rows modality certificate left).symm
    _ = tomographicFiniteModalityBranchReconstruct rows modality certificate
        (tomographicFiniteModalityProjection rows right) :=
      congrArg
        (tomographicFiniteModalityBranchReconstruct rows modality certificate)
        same
    _ = right :=
      tomographicFiniteModality_exact_reconstruction_of_branch_certificate
        rows modality certificate right

theorem tomographicFiniteModality_target_decoder_of_branch_certificate
    {Answer : Type*}
    (rows : Modality → View → Coordinate → ℝ)
    (modality : Modality)
    (certificate : TomographicFusionCertificate (rows modality))
    (target : (Coordinate → ℝ) → Answer) :
    ∃ decode : (Modality × View → ℝ) → Answer, ∀ state,
      decode (tomographicFiniteModalityProjection rows state) = target state := by
  refine ⟨fun data => target
      (tomographicFiniteModalityBranchReconstruct rows modality certificate data), ?_⟩
  intro state
  simpa using congrArg target
    (tomographicFiniteModality_exact_reconstruction_of_branch_certificate
      rows modality certificate state)

theorem tomographicFiniteModality_exact_reconstruction_of_filtered_backprojection_certificate
    (rows : Modality → View → Coordinate → ℝ)
    (certificate :
      TomographicFilteredBackprojectionCertificate
        (fun index : Modality × View => rows index.1 index.2))
    (state : Coordinate → ℝ) :
    tomographicFilteredBackprojection
        (fun index : Modality × View => rows index.1 index.2)
        certificate.filter (tomographicFiniteModalityProjection rows state) =
      state := by
  rw [tomographicFiniteModalityProjection_eq_flattened]
  exact certificate.exact_reconstruction state

theorem tomographicFiniteModality_target_decoder_of_filtered_backprojection_certificate
    {Answer : Type*}
    (rows : Modality → View → Coordinate → ℝ)
    (certificate :
      TomographicFilteredBackprojectionCertificate
        (fun index : Modality × View => rows index.1 index.2))
    (target : (Coordinate → ℝ) → Answer) :
    ∃ decode : (Modality × View → ℝ) → Answer, ∀ state,
      decode (tomographicFiniteModalityProjection rows state) = target state := by
  refine ⟨fun data => target
      (tomographicFilteredBackprojection
        (fun index : Modality × View => rows index.1 index.2)
        certificate.filter data), ?_⟩
  intro state
  simpa [tomographicFiniteModalityProjection] using
    congrArg target (certificate.exact_reconstruction state)

theorem tomographicFiniteModality_target_decoder_with_noise_bound_of_fusion_certificate
    {Answer : Type*} [PseudoMetricSpace Answer]
    (rows : Modality → View → Coordinate → ℝ)
    (certificate :
      TomographicFusionCertificate
        (fun index : Modality × View => rows index.1 index.2))
    (target : (Coordinate → ℝ) → Answer)
    (target_constant : ℝ) (target_constant_nonnegative : 0 ≤ target_constant)
    (target_modulus : ∀ first second,
      dist (target first) (target second) ≤
        target_constant * dist first second) :
    ∃ decode : (Modality × View → ℝ) → Answer,
      (∀ state,
        decode (tomographicFiniteModalityProjection rows state) = target state) ∧
      (∀ state data budget,
        dist data (tomographicFiniteModalityProjection rows state) ≤ budget →
          dist (decode data) (target state) ≤
            target_constant * certificate.noiseGain * budget) := by
  refine ⟨fun data => target (certificate.reconstruct data), ?_, ?_⟩
  · intro state
    exact congrArg target
      (tomographicFiniteModality_exact_reconstruction_of_fusion_certificate
        rows certificate state)
  · intro state data budget measurementBound
    exact tomographicFiniteModality_task_noise_bound_of_fusion_certificate
      rows certificate target target_constant target_constant_nonnegative
      target_modulus state data budget measurementBound

def TomographicFiniteModalityTaskFrameCertificate
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer) :=
  TomographicWeightedTaskFrameCertificate
    (fun index : Modality × View => rows index.1 index.2)
    (fun index : Modality × View => weight index.1 index.2)
    target

/-! The fused weighted normal operator is source-decomposable.  This keeps the
    adjoint/normal diagnostic attributable to each modality while retaining a
    single product-indexed operator for downstream task certificates. -/

theorem tomographicFiniteModalityWeightedNormalOperator_eq_sum_modalities
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (state : Coordinate → ℝ) :
    tomographicWeightedNormalOperator
        (fun index : Modality × View => rows index.1 index.2)
        (fun index : Modality × View => weight index.1 index.2)
        state =
      fun coordinate =>
        ∑ modality,
          tomographicWeightedNormalOperator
            (rows modality) (weight modality) state coordinate := by
  funext coordinate
  unfold tomographicWeightedNormalOperator tomographicWeightedBackprojection
  rw [Fintype.sum_prod_type]
  rfl

theorem tomographicFiniteModalityWeightedNormalOperator_energy_eq_sum_modalities
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (state : Coordinate → ℝ) :
    tomographicInner
        (tomographicWeightedNormalOperator
          (fun index : Modality × View => rows index.1 index.2)
          (fun index : Modality × View => weight index.1 index.2)
          state) state =
      ∑ modality,
        tomographicInner
        (tomographicWeightedNormalOperator
            (rows modality) (weight modality) state) state := by
  classical
  calc
    tomographicInner
        (tomographicWeightedNormalOperator
          (fun index : Modality × View => rows index.1 index.2)
          (fun index : Modality × View => weight index.1 index.2)
          state) state =
        ∑ index : Modality × View,
          weight index.1 index.2 *
            (tomographicProjection (rows index.1) state index.2) ^ 2 :=
      tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy
        (fun index : Modality × View => rows index.1 index.2)
        (fun index : Modality × View => weight index.1 index.2) state
    _ = ∑ modality, ∑ view,
          weight modality view *
            (tomographicProjection (rows modality) state view) ^ 2 := by
      rw [Fintype.sum_prod_type]
    _ = ∑ modality,
        tomographicInner
          (tomographicWeightedNormalOperator
            (rows modality) (weight modality) state) state := by
      classical
      apply Finset.sum_congr rfl
      intro modality _
      symm
      exact tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy
        (rows modality) (weight modality) state

theorem tomographicFiniteModalityWeightedNormalOperator_pairing_eq_sum_modalities
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (state direction : Coordinate → ℝ) :
    tomographicInner
        (tomographicWeightedNormalOperator
          (fun index : Modality × View => rows index.1 index.2)
          (fun index : Modality × View => weight index.1 index.2)
          state) direction =
      ∑ modality,
        tomographicInner
          (tomographicWeightedNormalOperator
            (rows modality) (weight modality) state) direction := by
  classical
  calc
    tomographicInner
        (tomographicWeightedNormalOperator
          (fun index : Modality × View => rows index.1 index.2)
          (fun index : Modality × View => weight index.1 index.2)
          state) direction =
        ∑ index : Modality × View,
          weight index.1 index.2 *
            tomographicProjection (rows index.1) state index.2 *
              tomographicProjection (rows index.1) direction index.2 :=
      tomographicWeightedNormalOperator_pairing
        (fun index : Modality × View => rows index.1 index.2)
        (fun index : Modality × View => weight index.1 index.2)
        state direction
    _ = ∑ modality, ∑ view,
          weight modality view *
            tomographicProjection (rows modality) state view *
              tomographicProjection (rows modality) direction view := by
      rw [Fintype.sum_prod_type]
    _ = ∑ modality,
        tomographicInner
          (tomographicWeightedNormalOperator
            (rows modality) (weight modality) state) direction := by
      classical
      apply Finset.sum_congr rfl
      intro modality _
      symm
      exact tomographicWeightedNormalOperator_pairing
        (rows modality) (weight modality) state direction

def tomographicFiniteModalityTaskFrameCertificate_of_branch_certificates
    [Nonempty Modality]
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : ∀ modality,
      TomographicWeightedTaskFrameCertificate
        (rows modality) (weight modality) target) :
    TomographicFiniteModalityTaskFrameCertificate rows weight target := by
  classical
  refine
    { alpha := ∑ modality, (certificate modality).alpha
      alpha_positive := ?_
      weight_nonnegative := ?_
      lower_on_target_disagreement := ?_ }
  · exact Finset.sum_pos
      (fun modality _ => (certificate modality).alpha_positive)
      Finset.univ_nonempty
  · intro index
    exact (certificate index.1).weight_nonnegative index.2
  · intro left right target_ne
    calc
      (∑ modality, (certificate modality).alpha) *
          tomographicInner (fun coordinate => left coordinate - right coordinate)
            (fun coordinate => left coordinate - right coordinate) =
        ∑ modality, (certificate modality).alpha *
          tomographicInner (fun coordinate => left coordinate - right coordinate)
            (fun coordinate => left coordinate - right coordinate) := by
        rw [Finset.sum_mul]
      _ ≤ ∑ modality, ∑ view, (weight modality view) *
          (tomographicProjection (rows modality) left view -
            tomographicProjection (rows modality) right view) ^ 2 := by
        apply Finset.sum_le_sum
        intro modality modality_mem
        exact (certificate modality).lower_on_target_disagreement target_ne
      _ = ∑ index : Modality × View,
          (weight index.1 index.2) *
            (tomographicFiniteModalityProjection rows left index -
              tomographicFiniteModalityProjection rows right index) ^ 2 := by
        rw [Fintype.sum_prod_type]
        rfl

def tomographicFiniteModalityTaskFrameCertificate_mono_weights
    (rows : Modality → View → Coordinate → ℝ)
    (weight weight' : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (weight_le : ∀ modality view,
      weight modality view ≤ weight' modality view) :
    TomographicFiniteModalityTaskFrameCertificate rows weight' target := by
  exact tomographicWeightedTaskFrameCertificate_mono_weights
    (fun index : Modality × View => rows index.1 index.2)
    (fun index : Modality × View => weight index.1 index.2)
    (fun index : Modality × View => weight' index.1 index.2)
    target certificate (fun index => weight_le index.1 index.2)

theorem tomographicFiniteModalityTaskFrameCertificate_task_pairwise_resolution
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
      (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target) :
    TomographicTaskPairwiseResolution
      (tomographicFiniteModalityProjectionOperator rows) target := by
  classical
  intro left right target_ne
  obtain ⟨index, weight_positive, projection_unequal⟩ :=
    tomographicWeightedTaskFrameCertificate_positive_weight_separates
      (fun index : Modality × View => rows index.1 index.2)
      (fun index : Modality × View => weight index.1 index.2)
      target certificate left right target_ne
  refine ⟨{
    view := index
    margin := abs (tomographicFiniteModalityProjection rows left index -
      tomographicFiniteModalityProjection rows right index)
    margin_positive := by
      apply abs_pos.mpr
      simpa [tomographicFiniteModalityProjection] using
        sub_ne_zero.mpr projection_unequal
    lower_bound := le_rfl
  }⟩

theorem tomographicFiniteModalityTaskFrameCertificate_task_decoder
    [Nonempty Answer]
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target) :
    ∃ decode : (∀ _ : Modality × View, ℝ) → Answer, ∀ state,
      decode (tomographicFiniteModalityProjection rows state) = target state := by
  classical
  apply (tomographic_task_decoder_iff
    (project := tomographicFiniteModalityProjectionOperator rows)
    target).2
  intro left right same
  by_contra target_ne
  obtain ⟨resolution⟩ :=
    tomographicFiniteModalityTaskFrameCertificate_task_pairwise_resolution
      rows weight target certificate target_ne
  exact (tomographicPairResolutionCertificate_distinguishes
    (tomographicFiniteModalityProjectionOperator rows) left right resolution)
    (congrFun same resolution.view)

theorem tomographicFiniteModalityTaskFrameCertificate_difference_state_energy_bound
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (left right : Coordinate → ℝ)
    (target_ne : target left ≠ target right)
    (budget : ℝ)
    (projection_energy_upper :
      (∑ index : Modality × View,
        weight index.1 index.2 *
          (tomographicFiniteModalityProjection rows left index -
            tomographicFiniteModalityProjection rows right index) ^ 2) ≤ budget) :
    tomographicInner
        (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) ≤
      budget / certificate.alpha := by
  apply (le_div_iff₀ certificate.alpha_positive).mpr
  calc
    tomographicInner (fun coordinate => left coordinate - right coordinate)
          (fun coordinate => left coordinate - right coordinate) * certificate.alpha ≤
      ∑ index : Modality × View,
        weight index.1 index.2 *
          (tomographicFiniteModalityProjection rows left index -
            tomographicFiniteModalityProjection rows right index) ^ 2 := by
      simpa [tomographicFiniteModalityProjection, mul_comm] using
        certificate.lower_on_target_disagreement target_ne
    _ ≤ budget := projection_energy_upper

theorem tomographicFiniteModalityTaskFrameCertificate_difference_state_energy_bound_of_observation_residual
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (left right : Coordinate → ℝ)
    (target_ne : target left ≠ target right)
    (budget : ℝ)
    (residual_upper :
      tomographicFiniteModalityWeightedDataResidualEnergy
        rows weight
        (fun modality view => tomographicProjection (rows modality) right view)
        left ≤ budget) :
    tomographicInner
        (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) ≤
      budget / certificate.alpha := by
  apply tomographicFiniteModalityTaskFrameCertificate_difference_state_energy_bound
    rows weight target certificate left right target_ne budget
  simpa [tomographicFiniteModalityWeightedDataResidualEnergy,
    tomographicFiniteModalityProjection] using residual_upper

theorem tomographicFiniteModalityTaskFrameCertificate_difference_state_energy_bound_of_modality_residual_budgets
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (left right : Coordinate → ℝ)
    (target_ne : target left ≠ target right)
    (budget : Modality → ℝ)
    (residual_upper : ∀ modality,
      tomographicWeightedDataResidualEnergy
        (weight modality)
        (fun view state => tomographicProjection (rows modality) state view)
        (fun view => tomographicProjection (rows modality) right view)
        left ≤ budget modality) :
    tomographicInner
        (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) ≤
      (∑ modality, budget modality) / certificate.alpha := by
  apply tomographicFiniteModalityTaskFrameCertificate_difference_state_energy_bound
    rows weight target certificate left right target_ne (∑ modality, budget modality)
  apply tomographicFiniteModalityWeightedDataResidualEnergy_le_sum_modality_budgets
    rows weight
    (fun modality view => tomographicProjection (rows modality) right view)
    left budget
  exact residual_upper

theorem tomographicFiniteModalityTaskFrameCertificate_shared_observation_difference_state_energy_bound
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (observations : Modality → View → ℝ)
    (left right : Coordinate → ℝ)
    (target_ne : target left ≠ target right)
    (left_budget right_budget : ℝ)
    (left_residual_upper :
      tomographicFiniteModalityWeightedDataResidualEnergy
        rows weight observations left ≤ left_budget)
    (right_residual_upper :
      tomographicFiniteModalityWeightedDataResidualEnergy
        rows weight observations right ≤ right_budget) :
    tomographicInner
        (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) ≤
      (2 * left_budget + 2 * right_budget) / certificate.alpha := by
  apply tomographicFiniteModalityTaskFrameCertificate_difference_state_energy_bound
    rows weight target certificate left right target_ne
      (2 * left_budget + 2 * right_budget)
  calc
    ∑ index : Modality × View,
        weight index.1 index.2 *
          (tomographicFiniteModalityProjection rows left index -
            tomographicFiniteModalityProjection rows right index) ^ 2 ≤
      ∑ index : Modality × View,
        (2 * (weight index.1 index.2 *
          (tomographicFiniteModalityProjection rows left index -
            observations index.1 index.2) ^ 2) +
          2 * (weight index.1 index.2 *
            (tomographicFiniteModalityProjection rows right index -
              observations index.1 index.2) ^ 2)) := by
      apply Finset.sum_le_sum
      intro index _
      have weight_nonnegative := certificate.weight_nonnegative index
      have square_bound :
          (tomographicFiniteModalityProjection rows left index -
              tomographicFiniteModalityProjection rows right index) ^ 2 ≤
            2 * (tomographicFiniteModalityProjection rows left index -
              observations index.1 index.2) ^ 2 +
              2 * (tomographicFiniteModalityProjection rows right index -
                observations index.1 index.2) ^ 2 := by
        nlinarith [sq_nonneg
          ((tomographicFiniteModalityProjection rows left index -
              observations index.1 index.2) +
            (tomographicFiniteModalityProjection rows right index -
              observations index.1 index.2))]
      calc
        weight index.1 index.2 *
              (tomographicFiniteModalityProjection rows left index -
                tomographicFiniteModalityProjection rows right index) ^ 2 ≤
            weight index.1 index.2 *
              (2 * (tomographicFiniteModalityProjection rows left index -
                observations index.1 index.2) ^ 2 +
                2 * (tomographicFiniteModalityProjection rows right index -
                  observations index.1 index.2) ^ 2) :=
          mul_le_mul_of_nonneg_left square_bound weight_nonnegative
        _ = 2 * (weight index.1 index.2 *
            (tomographicFiniteModalityProjection rows left index -
              observations index.1 index.2) ^ 2) +
            2 * (weight index.1 index.2 *
              (tomographicFiniteModalityProjection rows right index -
                observations index.1 index.2) ^ 2) := by
          ring_nf
    _ = 2 * tomographicFiniteModalityWeightedDataResidualEnergy
          rows weight observations left +
        2 * tomographicFiniteModalityWeightedDataResidualEnergy
          rows weight observations right := by
      unfold tomographicFiniteModalityWeightedDataResidualEnergy
      rw [Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib]
      apply Finset.sum_congr rfl
      intro index _
      simp only [tomographicFiniteModalityProjection]
    _ ≤ 2 * left_budget + 2 * right_budget := by
      nlinarith [left_residual_upper, right_residual_upper]

theorem tomographicFiniteModalityTaskFrameCertificate_noisy_task_decoder_exists
    [Nonempty Answer]
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (noise : (Modality × View) → (Coordinate → ℝ) → ℝ)
    (error_budget : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (tomographicFiniteModalityProjectionOperator rows) left right,
        |noise resolution.view left| + |noise resolution.view right| <
          resolution.margin) :
    ∃ decode : (∀ _ : Modality × View, ℝ) → Answer, ∀ state,
      decode (tomographicNoisyFusedImage
        (tomographicFiniteModalityProjectionOperator rows) noise state) = target state := by
  apply tomographic_noisy_task_decoder_exists_of_task_pairwise_resolution
    (project := tomographicFiniteModalityProjectionOperator rows)
    (noise := noise)
    (target := target)
    (resolution :=
      tomographicFiniteModalityTaskFrameCertificate_task_pairwise_resolution
        rows weight target certificate)
  intro left right target_ne resolution
  exact error_budget target_ne resolution

theorem tomographicFiniteModalityTaskFrameCertificate_uniform_noisy_task_decoder_exists
    [Nonempty Answer]
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (noise : (Modality × View) → (Coordinate → ℝ) → ℝ)
    (epsilon : ℝ) (epsilon_nonnegative : 0 ≤ epsilon)
    (noise_bound : ∀ index state, |noise index state| ≤ epsilon)
    (margin_bound : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (tomographicFiniteModalityProjectionOperator rows) left right,
        2 * epsilon < resolution.margin) :
    ∃ decode : (∀ _ : Modality × View, ℝ) → Answer, ∀ state,
      decode (tomographicNoisyFusedImage
        (tomographicFiniteModalityProjectionOperator rows) noise state) = target state := by
  apply tomographicFiniteModalityTaskFrameCertificate_noisy_task_decoder_exists
    rows weight target certificate noise
  intro left right target_ne resolution
  have left_bound := noise_bound resolution.view left
  have right_bound := noise_bound resolution.view right
  have margin := margin_bound target_ne resolution
  nlinarith

theorem tomographicFiniteModalityTaskFrameCertificate_noisy_taskIdentifiable
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (noise : (Modality × View) → (Coordinate → ℝ) → ℝ)
    (error_budget : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (tomographicFiniteModalityProjectionOperator rows) left right,
        |noise resolution.view left| + |noise resolution.view right| <
          resolution.margin) :
    TomographicTaskIdentifiable
      (fun index state =>
        tomographicNoisyFusedImage
          (tomographicFiniteModalityProjectionOperator rows) noise state index)
      target := by
  apply tomographic_noisy_fused_image_taskIdentifiable_of_task_pairwise_resolution
    (project := tomographicFiniteModalityProjectionOperator rows)
    (noise := noise)
    (target := target)
    (resolution :=
      tomographicFiniteModalityTaskFrameCertificate_task_pairwise_resolution
        rows weight target certificate)
  intro left right target_ne resolution
  exact error_budget target_ne resolution

theorem tomographicFiniteModalityTaskFrameCertificate_uniform_noisy_taskIdentifiable
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (noise : (Modality × View) → (Coordinate → ℝ) → ℝ)
    (epsilon : ℝ) (epsilon_nonnegative : 0 ≤ epsilon)
    (noise_bound : ∀ index state, |noise index state| ≤ epsilon)
    (margin_bound : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (tomographicFiniteModalityProjectionOperator rows) left right,
        2 * epsilon < resolution.margin) :
    TomographicTaskIdentifiable
      (fun index state =>
        tomographicNoisyFusedImage
          (tomographicFiniteModalityProjectionOperator rows) noise state index)
      target := by
  apply tomographicFiniteModalityTaskFrameCertificate_noisy_taskIdentifiable
    rows weight target certificate noise
  intro left right target_ne resolution
  have left_bound := noise_bound resolution.view left
  have right_bound := noise_bound resolution.view right
  have margin := margin_bound target_ne resolution
  nlinarith

theorem tomographicFiniteModalityTaskFrameCertificate_modalitywise_noisy_taskIdentifiable
    (rows : Modality → View → Coordinate → ℝ)
    (weight : Modality → View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicFiniteModalityTaskFrameCertificate
      rows weight target)
    (noise : (Modality × View) → (Coordinate → ℝ) → ℝ)
    (epsilon : Modality → ℝ)
    (noise_bound : ∀ modality view state,
      |noise (modality, view) state| ≤ epsilon modality)
    (margin_bound : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (tomographicFiniteModalityProjectionOperator rows) left right,
        epsilon resolution.view.1 + epsilon resolution.view.1 <
          resolution.margin) :
    TomographicTaskIdentifiable
      (fun index state =>
        tomographicNoisyFusedImage
          (tomographicFiniteModalityProjectionOperator rows) noise state index)
      target := by
  apply tomographicFiniteModalityTaskFrameCertificate_noisy_taskIdentifiable
    rows weight target certificate noise
  intro left right target_ne resolution
  have left_bound := noise_bound resolution.view.1 resolution.view.2 left
  have right_bound := noise_bound resolution.view.1 resolution.view.2 right
  have margin := margin_bound target_ne resolution
  nlinarith

end FiniteModalityFrameBridge

section FiniteModalityRayBridge

variable {Coordinate Modality View Ray Sample : Type*}
  [Fintype Coordinate] [Fintype Modality] [Fintype View]
  [Fintype Ray] [Fintype Sample]

/-! A modality-indexed ray family is flattened only at the observation
    boundary.  The product index retains modality, view and ray identity, so
    downstream ledgers can still attribute every reading to its source. -/

def tomographicFiniteModalityRayProjection
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) : Modality × (View × Ray) → ℝ :=
  fun index => tomographicRayTransform state (rays index.1)
    index.2.1 index.2.2

def tomographicFiniteModalityRayRow
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate) :
    (Modality × (View × Ray)) → Coordinate → ℝ :=
  fun index => tomographicRayRow (rays index.1) index.2

theorem tomographicFiniteModalityRayProjection_eq_projection
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (state : Coordinate → ℝ) :
    tomographicFiniteModalityRayProjection rays state =
      tomographicProjection (tomographicFiniteModalityRayRow rays) state := by
  funext index
  have bridge := congrFun
    (tomographicRayTransform_eq_projection_of_ray_row
      state (rays index.1)) index.2.1
  have bridge' := congrFun bridge index.2.2
  simpa [tomographicFiniteModalityRayProjection,
    tomographicFiniteModalityRayRow] using bridge'

theorem tomographicFiniteModalityRay_target_decoder_of_filtered_backprojection_certificate
    {Answer : Type*}
    [DecidableEq Coordinate]
    (rays : Modality → View → Ray → Sample → Coordinate)
    (certificate :
      TomographicFilteredBackprojectionCertificate
        (tomographicFiniteModalityRayRow rays))
    (target : (Coordinate → ℝ) → Answer) :
    ∃ decode : (Modality × (View × Ray) → ℝ) → Answer, ∀ state,
      decode (tomographicFiniteModalityRayProjection rays state) = target state := by
  refine ⟨fun data => target
      (tomographicFilteredBackprojection
        (tomographicFiniteModalityRayRow rays)
        certificate.filter data), ?_⟩
  intro state
  rw [tomographicFiniteModalityRayProjection_eq_projection]
  simpa using congrArg target (certificate.exact_reconstruction state)

end FiniteModalityRayBridge

end OCKIndividuationMSpaceComposition
