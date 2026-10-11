import OCKIndividuationMSpaceComposition.TomographicFrameTaskBridge
import OCKIndividuationMSpaceComposition.TomographicHeterogeneousConsistency
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Heterogeneous frame-certified task decoding

This bridge makes the physical meaning of a multimodal tomographic image
explicit: two registered projection families may have different view index
types, but they still observe the same finite state.  The certificate is
task-relative and keeps the two energy budgets separate.  Consequently a
failure in one modality can be diagnosed without pretending that its views
are interchangeable with the other modality.

The construction is deliberately algebraic.  It does not infer calibration,
registration, independence, or a numerical reconstruction algorithm.  Those
are separate obligations in the optics transfer catalogue.
-/

section HeterogeneousFrameBridge

variable {Coordinate View₁ View₂ Answer : Type*}
  [Fintype Coordinate] [Fintype View₁] [Fintype View₂]
  [DecidableEq View₁] [DecidableEq View₂]

/-- A scalar projection family whose view index records the modality. -/
def tomographicHeterogeneousProjection
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ) :
    Sum View₁ View₂ → (Coordinate → ℝ) → ℝ
  | Sum.inl view, state => tomographicProjection rows₁ state view
  | Sum.inr view, state => tomographicProjection rows₂ state view

theorem tomographicHeterogeneousWeightedDataResidualEnergy_eq_fused_weighted_data_residual
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (observation₁ : View₁ → ℝ) (observation₂ : View₂ → ℝ)
    (world : Coordinate → ℝ) :
    tomographicHeterogeneousWeightedDataResidualEnergy
        weight₁ weight₂
        (fun view state => tomographicProjection rows₁ state view)
        (fun view state => tomographicProjection rows₂ state view)
        observation₁ observation₂ world =
      tomographicWeightedDataResidualEnergy
        (fun view => match view with
          | Sum.inl leftView => weight₁ leftView
          | Sum.inr rightView => weight₂ rightView)
        (tomographicHeterogeneousProjection rows₁ rows₂)
        (fun view => match view with
          | Sum.inl leftView => observation₁ leftView
          | Sum.inr rightView => observation₂ rightView)
        world := by
  unfold tomographicHeterogeneousWeightedDataResidualEnergy
    tomographicWeightedDataResidualEnergy
  rw [Fintype.sum_sum_type]
  rfl

theorem tomographicHeterogeneousWeightedNormalOperator_energy_eq_fused_weighted_projection_energy
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (state : Coordinate → ℝ) :
    (∑ view, weight₁ view *
      (tomographicProjection rows₁ state view) ^ 2) +
        ∑ view, weight₂ view *
          (tomographicProjection rows₂ state view) ^ 2 =
      tomographicInner
        (tomographicWeightedNormalOperator
          (fun view => match view with
            | Sum.inl leftView => rows₁ leftView
            | Sum.inr rightView => rows₂ rightView)
          (fun view => match view with
            | Sum.inl leftView => weight₁ leftView
            | Sum.inr rightView => weight₂ rightView)
          state) state := by
  rw [tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy]
  unfold tomographicProjection
  rw [Fintype.sum_sum_type]

theorem tomographicHeterogeneousFusedWeightedDataResidualEnergy_zero_iff_agreement_on_positive_support
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (observation₁ : View₁ → ℝ) (observation₂ : View₂ → ℝ)
    (world : Coordinate → ℝ)
    (weight₁_nonnegative : ∀ view, 0 ≤ weight₁ view)
    (weight₂_nonnegative : ∀ view, 0 ≤ weight₂ view) :
    tomographicWeightedDataResidualEnergy
        (fun view => match view with
          | Sum.inl leftView => weight₁ leftView
          | Sum.inr rightView => weight₂ rightView)
        (tomographicHeterogeneousProjection rows₁ rows₂)
        (fun view => match view with
          | Sum.inl leftView => observation₁ leftView
          | Sum.inr rightView => observation₂ rightView)
        world = 0 ↔
      (∀ view, 0 < weight₁ view →
        tomographicProjection rows₁ world view = observation₁ view) ∧
      (∀ view, 0 < weight₂ view →
        tomographicProjection rows₂ world view = observation₂ view) := by
  rw [← tomographicHeterogeneousWeightedDataResidualEnergy_eq_fused_weighted_data_residual
    rows₁ rows₂ weight₁ weight₂ observation₁ observation₂ world]
  exact tomographicHeterogeneousWeightedDataResidualEnergy_zero_iff_agreement_on_positive_weight
    weight₁ weight₂
    (fun view state => tomographicProjection rows₁ state view)
    (fun view state => tomographicProjection rows₂ state view)
    observation₁ observation₂ world weight₁_nonnegative weight₂_nonnegative

@[simp] theorem tomographicHeterogeneousProjection_left
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (view : View₁) (state : Coordinate → ℝ) :
    tomographicHeterogeneousProjection rows₁ rows₂ (Sum.inl view) state =
      tomographicProjection rows₁ state view := rfl

@[simp] theorem tomographicHeterogeneousProjection_right
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (view : View₂) (state : Coordinate → ℝ) :
    tomographicHeterogeneousProjection rows₁ rows₂ (Sum.inr view) state =
      tomographicProjection rows₂ state view := rfl

/-- A lower frame bound for two heterogeneous modalities observing one state
    space and one declared task. -/
structure TomographicHeterogeneousTaskFrameCertificate
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer) where
  alpha : ℝ
  alpha_positive : 0 < alpha
  weight₁_nonnegative : ∀ view, 0 ≤ weight₁ view
  weight₂_nonnegative : ∀ view, 0 ≤ weight₂ view
  lower_on_target_disagreement : ∀ {left right : Coordinate → ℝ},
    target left ≠ target right →
      alpha *
          tomographicInner (fun coordinate => left coordinate - right coordinate)
            (fun coordinate => left coordinate - right coordinate) ≤
        (∑ view, weight₁ view *
          (tomographicProjection rows₁ left view -
            tomographicProjection rows₁ right view) ^ 2) +
        ∑ view, weight₂ view *
          (tomographicProjection rows₂ left view -
            tomographicProjection rows₂ right view) ^ 2

def tomographicHeterogeneousTaskFrameCertificate_of_branch_certificates
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate₁ : TomographicWeightedTaskFrameCertificate
      rows₁ weight₁ target)
    (certificate₂ : TomographicWeightedTaskFrameCertificate
      rows₂ weight₂ target) :
    TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁ weight₂ target := by
  refine
    { alpha := certificate₁.alpha + certificate₂.alpha
      alpha_positive := add_pos certificate₁.alpha_positive certificate₂.alpha_positive
      weight₁_nonnegative := certificate₁.weight_nonnegative
      weight₂_nonnegative := certificate₂.weight_nonnegative
      lower_on_target_disagreement := ?_ }
  intro left right target_ne
  calc
    (certificate₁.alpha + certificate₂.alpha) *
        tomographicInner (fun coordinate => left coordinate - right coordinate)
          (fun coordinate => left coordinate - right coordinate) =
      certificate₁.alpha *
          tomographicInner (fun coordinate => left coordinate - right coordinate)
            (fun coordinate => left coordinate - right coordinate) +
        certificate₂.alpha *
          tomographicInner (fun coordinate => left coordinate - right coordinate)
            (fun coordinate => left coordinate - right coordinate) := by ring
    _ ≤
        (∑ view, weight₁ view *
          (tomographicProjection rows₁ left view -
            tomographicProjection rows₁ right view) ^ 2) +
        ∑ view, weight₂ view *
          (tomographicProjection rows₂ left view -
            tomographicProjection rows₂ right view) ^ 2 :=
      add_le_add
        (certificate₁.lower_on_target_disagreement target_ne)
        (certificate₂.lower_on_target_disagreement target_ne)

def tomographicHeterogeneousTaskFrameCertificate_mono_weights
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ weight₁' : View₁ → ℝ)
    (weight₂ weight₂' : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁ weight₂ target)
    (weight₁_order : ∀ view, weight₁ view ≤ weight₁' view)
    (weight₂_order : ∀ view, weight₂ view ≤ weight₂' view) :
    TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁' weight₂' target := by
  refine
    { alpha := certificate.alpha
      alpha_positive := certificate.alpha_positive
      weight₁_nonnegative := fun view =>
        (certificate.weight₁_nonnegative view).trans (weight₁_order view)
      weight₂_nonnegative := fun view =>
        (certificate.weight₂_nonnegative view).trans (weight₂_order view)
      lower_on_target_disagreement := ?_ }
  intro left right target_ne
  calc
    certificate.alpha *
        tomographicInner (fun coordinate => left coordinate - right coordinate)
          (fun coordinate => left coordinate - right coordinate) ≤
      (∑ view, weight₁ view *
        (tomographicProjection rows₁ left view -
          tomographicProjection rows₁ right view) ^ 2) +
      ∑ view, weight₂ view *
        (tomographicProjection rows₂ left view -
          tomographicProjection rows₂ right view) ^ 2 :=
      certificate.lower_on_target_disagreement target_ne
    _ ≤
        (∑ view, weight₁' view *
          (tomographicProjection rows₁ left view -
            tomographicProjection rows₁ right view) ^ 2) +
        ∑ view, weight₂' view *
          (tomographicProjection rows₂ left view -
            tomographicProjection rows₂ right view) ^ 2 := by
      apply add_le_add
      · apply Finset.sum_le_sum
        intro view _
        exact mul_le_mul_of_nonneg_right (weight₁_order view) (sq_nonneg _)
      · apply Finset.sum_le_sum
        intro view _
        exact mul_le_mul_of_nonneg_right (weight₂_order view) (sq_nonneg _)

theorem tomographicHeterogeneousTaskFrameCertificate_positive_weight_separates
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁ weight₂ target)
    (left right : Coordinate → ℝ) (target_ne : target left ≠ target right) :
    (∃ view, 0 < weight₁ view ∧
      tomographicProjection rows₁ left view ≠
        tomographicProjection rows₁ right view) ∨
    (∃ view, 0 < weight₂ view ∧
      tomographicProjection rows₂ left view ≠
        tomographicProjection rows₂ right view) := by
  by_contra no_separating_view
  have no_left : ¬ ∃ view, 0 < weight₁ view ∧
      tomographicProjection rows₁ left view ≠
        tomographicProjection rows₁ right view := by
    intro witness
    exact no_separating_view (Or.inl witness)
  have no_right : ¬ ∃ view, 0 < weight₂ view ∧
      tomographicProjection rows₂ left view ≠
        tomographicProjection rows₂ right view := by
    intro witness
    exact no_separating_view (Or.inr witness)
  have left_equal (view : View₁) (positive : 0 < weight₁ view) :
      tomographicProjection rows₁ left view =
        tomographicProjection rows₁ right view := by
    by_contra unequal
    exact no_left ⟨view, positive, unequal⟩
  have right_equal (view : View₂) (positive : 0 < weight₂ view) :
      tomographicProjection rows₂ left view =
        tomographicProjection rows₂ right view := by
    by_contra unequal
    exact no_right ⟨view, positive, unequal⟩
  let difference : Coordinate → ℝ := fun coordinate =>
    left coordinate - right coordinate
  have left_energy_zero :
      (∑ view, weight₁ view *
        (tomographicProjection rows₁ left view -
          tomographicProjection rows₁ right view) ^ 2) = 0 := by
    apply Finset.sum_eq_zero
    intro view view_mem
    by_cases positive : 0 < weight₁ view
    · simp [left_equal view positive]
    · have weight_zero : weight₁ view = 0 := by
        exact le_antisymm (not_lt.mp positive)
          (certificate.weight₁_nonnegative view)
      simp [weight_zero]
  have right_energy_zero :
      (∑ view, weight₂ view *
        (tomographicProjection rows₂ left view -
          tomographicProjection rows₂ right view) ^ 2) = 0 := by
    apply Finset.sum_eq_zero
    intro view view_mem
    by_cases positive : 0 < weight₂ view
    · simp [right_equal view positive]
    · have weight_zero : weight₂ view = 0 := by
        exact le_antisymm (not_lt.mp positive)
          (certificate.weight₂_nonnegative view)
      simp [weight_zero]
  have upper : certificate.alpha * tomographicInner difference difference ≤ 0 := by
    calc
      certificate.alpha * tomographicInner difference difference ≤
          (∑ view, weight₁ view *
            (tomographicProjection rows₁ left view -
              tomographicProjection rows₁ right view) ^ 2) +
          ∑ view, weight₂ view *
            (tomographicProjection rows₂ left view -
              tomographicProjection rows₂ right view) ^ 2 := by
        simpa [difference] using
          certificate.lower_on_target_disagreement target_ne
      _ = 0 := by simp [left_energy_zero, right_energy_zero]
  have lower_nonnegative : 0 ≤ certificate.alpha * tomographicInner difference difference :=
    mul_nonneg (le_of_lt certificate.alpha_positive)
      (tomographicInner_nonnegative difference)
  have product_zero : certificate.alpha * tomographicInner difference difference = 0 :=
    le_antisymm upper lower_nonnegative
  have state_energy_zero : tomographicInner difference difference = 0 :=
    (mul_eq_zero.mp product_zero).resolve_left (ne_of_gt certificate.alpha_positive)
  have every_square_zero : (fun coordinate => difference coordinate ^ 2) = 0 := by
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
      sq_nonneg (difference coordinate))).mp
    simpa [tomographicInner, pow_two] using state_energy_zero
  have difference_zero : difference = 0 := by
    funext coordinate
    exact sq_eq_zero_iff.mp (congrFun every_square_zero coordinate)
  apply target_ne
  apply congrArg target
  funext coordinate
  exact sub_eq_zero.mp (congrFun difference_zero coordinate)

theorem tomographicHeterogeneousTaskFrameCertificate_task_pairwise_resolution
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁ weight₂ target) :
    TomographicTaskPairwiseResolution
      (tomographicHeterogeneousProjection rows₁ rows₂) target := by
  intro left right target_ne
  obtain (⟨view, positive, unequal⟩ | ⟨view, positive, unequal⟩) :=
    tomographicHeterogeneousTaskFrameCertificate_positive_weight_separates
      rows₁ rows₂ weight₁ weight₂ target certificate left right target_ne
  · exact ⟨⟨(Sum.inl view : Sum View₁ View₂),
      |tomographicProjection rows₁ left view -
        tomographicProjection rows₁ right view|,
      abs_pos.mpr (sub_ne_zero.mpr unequal), le_rfl⟩⟩
  · exact ⟨⟨(Sum.inr view : Sum View₁ View₂),
      |tomographicProjection rows₂ left view -
        tomographicProjection rows₂ right view|,
      abs_pos.mpr (sub_ne_zero.mpr unequal), le_rfl⟩⟩

theorem tomographicHeterogeneousTaskFrameCertificate_task_decoder
    [Nonempty Answer]
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁ weight₂ target) :
    ∃ decode : (Sum View₁ View₂ → ℝ) → Answer, ∀ state,
      decode (fun view => tomographicHeterogeneousProjection rows₁ rows₂ view state) =
        target state := by
  apply (tomographic_task_decoder_iff
    (project := tomographicHeterogeneousProjection rows₁ rows₂)
    target).2
  intro left right same
  by_contra target_ne
  obtain ⟨resolution⟩ :=
    tomographicHeterogeneousTaskFrameCertificate_task_pairwise_resolution
      rows₁ rows₂ weight₁ weight₂ target certificate target_ne
  exact (tomographicPairResolutionCertificate_distinguishes
    (tomographicHeterogeneousProjection rows₁ rows₂) left right resolution)
    (congrFun same resolution.view)

theorem tomographicHeterogeneousTaskFrameCertificate_difference_state_energy_bound
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁ weight₂ target)
    (left right : Coordinate → ℝ)
    (target_ne : target left ≠ target right)
    (budget : ℝ)
    (projection_energy_upper :
      (∑ view, weight₁ view *
        (tomographicProjection rows₁ left view -
          tomographicProjection rows₁ right view) ^ 2) +
      ∑ view, weight₂ view *
        (tomographicProjection rows₂ left view -
          tomographicProjection rows₂ right view) ^ 2 ≤ budget) :
    tomographicInner
        (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) ≤
      budget / certificate.alpha := by
  apply (le_div_iff₀ certificate.alpha_positive).mpr
  calc
    tomographicInner (fun coordinate => left coordinate - right coordinate)
          (fun coordinate => left coordinate - right coordinate) * certificate.alpha =
        certificate.alpha *
        tomographicInner (fun coordinate => left coordinate - right coordinate)
          (fun coordinate => left coordinate - right coordinate) := by ring
    _ ≤
      (∑ view, weight₁ view *
        (tomographicProjection rows₁ left view -
          tomographicProjection rows₁ right view) ^ 2) +
      ∑ view, weight₂ view *
        (tomographicProjection rows₂ left view -
          tomographicProjection rows₂ right view) ^ 2 :=
      certificate.lower_on_target_disagreement target_ne
    _ ≤ budget := projection_energy_upper

theorem tomographicHeterogeneousTaskFrameCertificate_difference_state_energy_bound_of_observation_residual
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁ weight₂ target)
    (left right : Coordinate → ℝ)
    (target_ne : target left ≠ target right)
    (budget : ℝ)
    (residual_upper :
      tomographicHeterogeneousWeightedDataResidualEnergy
        weight₁ weight₂
        (fun view state => tomographicProjection rows₁ state view)
        (fun view state => tomographicProjection rows₂ state view)
        (fun view => tomographicProjection rows₁ right view)
        (fun view => tomographicProjection rows₂ right view)
        left ≤ budget) :
    tomographicInner
        (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) ≤
      budget / certificate.alpha := by
  apply tomographicHeterogeneousTaskFrameCertificate_difference_state_energy_bound
    rows₁ rows₂ weight₁ weight₂ target certificate left right target_ne budget
  simpa [tomographicHeterogeneousWeightedDataResidualEnergy] using residual_upper

theorem tomographicHeterogeneousTaskFrameCertificate_noisy_task_decoder_exists
    [Nonempty Answer]
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁ weight₂ target)
    (noise : Sum View₁ View₂ → (Coordinate → ℝ) → ℝ)
    (error_budget : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (tomographicHeterogeneousProjection rows₁ rows₂) left right,
        |noise resolution.view left| + |noise resolution.view right| <
          resolution.margin) :
    ∃ decode : (∀ _ : Sum View₁ View₂, ℝ) → Answer, ∀ state,
      decode (tomographicNoisyFusedImage
        (tomographicHeterogeneousProjection rows₁ rows₂)
        noise state) = target state := by
  apply tomographic_noisy_task_decoder_exists_of_task_pairwise_resolution
    (project := tomographicHeterogeneousProjection rows₁ rows₂)
    (noise := noise)
    (target := target)
    (resolution :=
      tomographicHeterogeneousTaskFrameCertificate_task_pairwise_resolution
        rows₁ rows₂ weight₁ weight₂ target certificate)
  intro left right target_ne resolution
  exact error_budget target_ne resolution

theorem tomographicHeterogeneousTaskFrameCertificate_uniform_noisy_task_decoder_exists
    [Nonempty Answer]
    (rows₁ : View₁ → Coordinate → ℝ)
    (rows₂ : View₂ → Coordinate → ℝ)
    (weight₁ : View₁ → ℝ) (weight₂ : View₂ → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicHeterogeneousTaskFrameCertificate
      rows₁ rows₂ weight₁ weight₂ target)
    (noise : Sum View₁ View₂ → (Coordinate → ℝ) → ℝ)
    (epsilon : ℝ) (epsilon_nonnegative : 0 ≤ epsilon)
    (noise_bound : ∀ view state, |noise view state| ≤ epsilon)
    (margin_bound : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (tomographicHeterogeneousProjection rows₁ rows₂) left right,
        2 * epsilon < resolution.margin) :
    ∃ decode : (∀ _ : Sum View₁ View₂, ℝ) → Answer, ∀ state,
      decode (tomographicNoisyFusedImage
        (tomographicHeterogeneousProjection rows₁ rows₂)
        noise state) = target state := by
  apply tomographicHeterogeneousTaskFrameCertificate_noisy_task_decoder_exists
    rows₁ rows₂ weight₁ weight₂ target certificate noise
  intro left right target_ne resolution
  have left_bound := noise_bound resolution.view left
  have right_bound := noise_bound resolution.view right
  have margin := margin_bound target_ne resolution
  nlinarith

end HeterogeneousFrameBridge

end OCKIndividuationMSpaceComposition
