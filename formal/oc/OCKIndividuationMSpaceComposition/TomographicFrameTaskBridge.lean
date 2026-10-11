import OCKIndividuationMSpaceComposition.TomographicNormalOperator
import OCKIndividuationMSpaceComposition.TomographicTaskReconstruction
import OCKIndividuationMSpaceComposition.TomographicResolutionMargin
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Frame-certified task decoding

This bridge keeps the quantitative frame premise in the normal-operator layer
and transports only its injectivity consequence into the existing task decoder
contract.  It does not construct a numerical solver or infer a frame bound.
-/

section FrameTaskBridge

variable {Coordinate View Answer : Type*}
  [Fintype Coordinate] [Fintype View] [DecidableEq View]

structure TomographicWeightedTaskFrameCertificate
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (target : (Coordinate → ℝ) → Answer) where
  alpha : ℝ
  alpha_positive : 0 < alpha
  weight_nonnegative : ∀ view, 0 ≤ weight view
  lower_on_target_disagreement : ∀ {left right : Coordinate → ℝ},
    target left ≠ target right →
      alpha *
          tomographicInner (fun coordinate => left coordinate - right coordinate)
            (fun coordinate => left coordinate - right coordinate) ≤
        ∑ view, weight view *
          (tomographicProjection rows left view -
            tomographicProjection rows right view) ^ 2

def tomographicWeightedFrameCertificate_mono_weights
    (rows : View → Coordinate → ℝ) (weight weight' : View → ℝ)
    (certificate : TomographicWeightedFrameCertificate rows weight)
    (weight_le : ∀ view, weight view ≤ weight' view) :
    TomographicWeightedFrameCertificate rows weight' := by
  refine
    { alpha := certificate.alpha
      alpha_positive := certificate.alpha_positive
      weight_nonnegative := ?_
      lower := ?_ }
  · intro view
    exact (certificate.weight_nonnegative view).trans (weight_le view)
  · intro state
    calc
      certificate.alpha * tomographicInner state state ≤
          tomographicInner
            (tomographicWeightedNormalOperator rows weight state) state :=
        certificate.lower state
      _ = ∑ view, weight view *
            (tomographicProjection rows state view) ^ 2 :=
        tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy
          rows weight state
      _ ≤ ∑ view, weight' view *
            (tomographicProjection rows state view) ^ 2 := by
        apply Finset.sum_le_sum
        intro view view_mem
        exact mul_le_mul_of_nonneg_right (weight_le view) (sq_nonneg _)
       _ = tomographicInner
           (tomographicWeightedNormalOperator rows weight' state) state := by
         symm
         exact tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy
           rows weight' state

def tomographicWeightedFrameCertificate_add_weights
    (rows : View → Coordinate → ℝ)
    (weight₁ weight₂ : View → ℝ)
    (certificate₁ : TomographicWeightedFrameCertificate rows weight₁)
    (certificate₂ : TomographicWeightedFrameCertificate rows weight₂) :
    TomographicWeightedFrameCertificate rows
      (fun view => weight₁ view + weight₂ view) := by
  refine
    { alpha := certificate₁.alpha + certificate₂.alpha
      alpha_positive := add_pos certificate₁.alpha_positive certificate₂.alpha_positive
      weight_nonnegative := ?_
      lower := ?_ }
  · intro view
    exact add_nonneg (certificate₁.weight_nonnegative view)
      (certificate₂.weight_nonnegative view)
  · intro state
    rw [tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy]
    calc
      (certificate₁.alpha + certificate₂.alpha) *
          tomographicInner state state =
          certificate₁.alpha * tomographicInner state state +
            certificate₂.alpha * tomographicInner state state := by ring
      _ ≤ tomographicInner
            (tomographicWeightedNormalOperator rows weight₁ state) state +
          tomographicInner
            (tomographicWeightedNormalOperator rows weight₂ state) state :=
        add_le_add (certificate₁.lower state) (certificate₂.lower state)
      _ = (∑ view, weight₁ view *
            (tomographicProjection rows state view) ^ 2) +
          ∑ view, weight₂ view *
            (tomographicProjection rows state view) ^ 2 := by
        rw [tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy,
          tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy]
      _ = ∑ view, (weight₁ view + weight₂ view) *
            (tomographicProjection rows state view) ^ 2 := by
        symm
        calc
          ∑ view, (weight₁ view + weight₂ view) *
              (tomographicProjection rows state view) ^ 2 =
              ∑ view, (weight₁ view *
                (tomographicProjection rows state view) ^ 2 +
                weight₂ view *
                  (tomographicProjection rows state view) ^ 2) := by
            apply Finset.sum_congr rfl
            intro view view_mem
            ring
          _ = (∑ view, weight₁ view *
                (tomographicProjection rows state view) ^ 2) +
              ∑ view, weight₂ view *
                (tomographicProjection rows state view) ^ 2 :=
            Finset.sum_add_distrib

def tomographicWeightedTaskFrameCertificate_mono_weights
    (rows : View → Coordinate → ℝ) (weight weight' : View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicWeightedTaskFrameCertificate rows weight target)
    (weight_le : ∀ view, weight view ≤ weight' view) :
    TomographicWeightedTaskFrameCertificate rows weight' target := by
  refine
    { alpha := certificate.alpha
      alpha_positive := certificate.alpha_positive
      weight_nonnegative := ?_
      lower_on_target_disagreement := ?_ }
  · intro view
    exact (certificate.weight_nonnegative view).trans (weight_le view)
  · intro left right target_ne
    calc
      certificate.alpha *
          tomographicInner (fun coordinate => left coordinate - right coordinate)
            (fun coordinate => left coordinate - right coordinate) ≤
          ∑ view, weight view *
            (tomographicProjection rows left view -
              tomographicProjection rows right view) ^ 2 :=
        certificate.lower_on_target_disagreement target_ne
      _ ≤ ∑ view, weight' view *
            (tomographicProjection rows left view -
              tomographicProjection rows right view) ^ 2 := by
        apply Finset.sum_le_sum
        intro view view_mem
        exact mul_le_mul_of_nonneg_right (weight_le view) (sq_nonneg _)

def tomographicWeightedTaskFrameCertificate_add_weights
    (rows : View → Coordinate → ℝ)
    (weight₁ weight₂ : View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate₁ : TomographicWeightedTaskFrameCertificate rows weight₁ target)
    (certificate₂ : TomographicWeightedTaskFrameCertificate rows weight₂ target) :
    TomographicWeightedTaskFrameCertificate rows
      (fun view => weight₁ view + weight₂ view) target := by
  refine
    { alpha := certificate₁.alpha + certificate₂.alpha
      alpha_positive := add_pos certificate₁.alpha_positive certificate₂.alpha_positive
      weight_nonnegative := ?_
      lower_on_target_disagreement := ?_ }
  · intro view
    exact add_nonneg (certificate₁.weight_nonnegative view)
      (certificate₂.weight_nonnegative view)
  · intro left right target_ne
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
      _ ≤ (∑ view, weight₁ view *
            (tomographicProjection rows left view -
              tomographicProjection rows right view) ^ 2) +
          ∑ view, weight₂ view *
            (tomographicProjection rows left view -
              tomographicProjection rows right view) ^ 2 :=
        add_le_add (certificate₁.lower_on_target_disagreement target_ne)
          (certificate₂.lower_on_target_disagreement target_ne)
      _ = ∑ view, (weight₁ view + weight₂ view) *
            (tomographicProjection rows left view -
              tomographicProjection rows right view) ^ 2 := by
        symm
        calc
          ∑ view, (weight₁ view + weight₂ view) *
              (tomographicProjection rows left view -
                tomographicProjection rows right view) ^ 2 =
              ∑ view, (weight₁ view *
                (tomographicProjection rows left view -
                  tomographicProjection rows right view) ^ 2 +
                weight₂ view *
                  (tomographicProjection rows left view -
                    tomographicProjection rows right view) ^ 2) := by
            apply Finset.sum_congr rfl
            intro view view_mem
            ring
          _ = (∑ view, weight₁ view *
                (tomographicProjection rows left view -
                  tomographicProjection rows right view) ^ 2) +
              ∑ view, weight₂ view *
                (tomographicProjection rows left view -
                  tomographicProjection rows right view) ^ 2 :=
            Finset.sum_add_distrib

theorem tomographicWeightedFrameCertificate_positive_weight_separates
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (certificate : TomographicWeightedFrameCertificate rows weight)
    (left right : Coordinate → ℝ) (different : left ≠ right) :
    ∃ view, 0 < weight view ∧
      tomographicProjection rows left view ≠
        tomographicProjection rows right view := by
  by_contra no_separating_view
  have positive_projection_equal (view : View) (weight_positive : 0 < weight view) :
      tomographicProjection rows left view =
        tomographicProjection rows right view := by
    by_contra unequal
    exact no_separating_view ⟨view, weight_positive, unequal⟩
  let difference : Coordinate → ℝ := fun coordinate =>
    left coordinate - right coordinate
  have invisible : ∀ view, 0 < weight view →
      tomographicProjection rows difference view = 0 := by
    intro view weight_positive
    simpa [difference, tomographicProjection_sub,
      positive_projection_equal view weight_positive]
  have normal_zero : tomographicWeightedNormalOperator rows weight difference = 0 :=
    (tomographicWeightedNormalOperator_zero_iff_invisible_on_positive_weight
      rows weight difference certificate.weight_nonnegative).2 invisible
  have normal_energy_zero :
      tomographicInner
          (tomographicWeightedNormalOperator rows weight difference) difference = 0 := by
    simp [normal_zero, tomographicInner]
  have upper : certificate.alpha * tomographicInner difference difference ≤ 0 := by
    calc
      certificate.alpha * tomographicInner difference difference ≤
          tomographicInner
            (tomographicWeightedNormalOperator rows weight difference) difference :=
        certificate.lower difference
      _ = 0 := normal_energy_zero
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
  exact different (by
    funext coordinate
    exact sub_eq_zero.mp (congrFun difference_zero coordinate))

theorem tomographicWeightedTaskFrameCertificate_positive_weight_separates
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicWeightedTaskFrameCertificate rows weight target)
    (left right : Coordinate → ℝ) (target_ne : target left ≠ target right) :
    ∃ view, 0 < weight view ∧
      tomographicProjection rows left view ≠
        tomographicProjection rows right view := by
  by_contra no_separating_view
  have positive_projection_equal (view : View) (weight_positive : 0 < weight view) :
      tomographicProjection rows left view =
        tomographicProjection rows right view := by
    by_contra unequal
    exact no_separating_view ⟨view, weight_positive, unequal⟩
  let difference : Coordinate → ℝ := fun coordinate =>
    left coordinate - right coordinate
  have invisible : ∀ view, 0 < weight view →
      tomographicProjection rows difference view = 0 := by
    intro view weight_positive
    simpa [difference, tomographicProjection_sub,
      positive_projection_equal view weight_positive]
  have normal_zero : tomographicWeightedNormalOperator rows weight difference = 0 :=
    (tomographicWeightedNormalOperator_zero_iff_invisible_on_positive_weight
      rows weight difference certificate.weight_nonnegative).2 invisible
  have normal_energy_zero :
      tomographicInner
          (tomographicWeightedNormalOperator rows weight difference) difference = 0 := by
    simp [normal_zero, tomographicInner]
  have upper : certificate.alpha * tomographicInner difference difference ≤ 0 := by
    calc
      certificate.alpha * tomographicInner difference difference ≤
          ∑ view, weight view *
            (tomographicProjection rows difference view) ^ 2 := by
        simpa [difference, tomographicProjection_sub] using
          certificate.lower_on_target_disagreement target_ne
      _ = tomographicInner
          (tomographicWeightedNormalOperator rows weight difference) difference := by
        symm
        exact tomographicWeightedNormalOperator_energy_eq_weighted_projection_energy
          rows weight difference
      _ = 0 := normal_energy_zero
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

theorem tomographicWeightedFrameCertificate_pair_resolution
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (certificate : TomographicWeightedFrameCertificate rows weight)
    (left right : Coordinate → ℝ) (different : left ≠ right) :
    ∃ view, 0 < weight view ∧
      Nonempty (TomographicPairResolutionCertificate
        (fun view state => tomographicProjection rows state view) left right) := by
  obtain ⟨view, weight_positive, projection_unequal⟩ :=
    tomographicWeightedFrameCertificate_positive_weight_separates
      rows weight certificate left right different
  refine ⟨view, weight_positive, ⟨?_⟩⟩
  refine
    { view := view
      margin := |tomographicProjection rows left view -
        tomographicProjection rows right view|
      margin_positive := abs_pos.mpr (sub_ne_zero.mpr projection_unequal)
      lower_bound := le_rfl }

theorem tomographicWeightedTaskFrameCertificate_task_pairwise_resolution
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicWeightedTaskFrameCertificate rows weight target) :
    TomographicTaskPairwiseResolution
      (fun view state => tomographicProjection rows state view) target := by
  intro left right target_ne
  obtain ⟨view, weight_positive, projection_unequal⟩ :=
    tomographicWeightedTaskFrameCertificate_positive_weight_separates
      rows weight target certificate left right target_ne
  exact ⟨
    { view := view
      margin := |tomographicProjection rows left view -
        tomographicProjection rows right view|
      margin_positive := abs_pos.mpr (sub_ne_zero.mpr projection_unequal)
      lower_bound := le_rfl }⟩

theorem tomographicWeightedTaskFrameCertificate_noisy_task_decoder_exists
    [Nonempty Answer]
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicWeightedTaskFrameCertificate rows weight target)
    (noise : View → (Coordinate → ℝ) → ℝ)
    (error_budget : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (fun view state => tomographicProjection rows state view) left right,
        |noise resolution.view left| + |noise resolution.view right| <
          resolution.margin) :
    ∃ decode : (∀ _ : View, ℝ) → Answer, ∀ state,
      decode (tomographicNoisyFusedImage
        (fun view state => tomographicProjection rows state view)
        noise state) = target state := by
  apply tomographic_noisy_task_decoder_exists_of_task_pairwise_resolution
    (project := fun view state => tomographicProjection rows state view)
    (noise := noise)
    (target := target)
    (resolution :=
      tomographicWeightedTaskFrameCertificate_task_pairwise_resolution
        rows weight target certificate)
  intro left right target_ne resolution
  exact error_budget target_ne resolution

theorem tomographicWeightedTaskFrameCertificate_uniform_noisy_task_decoder_exists
    [Nonempty Answer]
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicWeightedTaskFrameCertificate rows weight target)
    (noise : View → (Coordinate → ℝ) → ℝ)
    (epsilon : ℝ) (epsilon_nonnegative : 0 ≤ epsilon)
    (noise_bound : ∀ view state, |noise view state| ≤ epsilon)
    (margin_bound : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (fun view state => tomographicProjection rows state view) left right,
        2 * epsilon < resolution.margin) :
    ∃ decode : (∀ _ : View, ℝ) → Answer, ∀ state,
      decode (tomographicNoisyFusedImage
        (fun view state => tomographicProjection rows state view)
        noise state) = target state := by
  apply tomographicWeightedTaskFrameCertificate_noisy_task_decoder_exists
    rows weight target certificate noise
  intro left right target_ne resolution
  have left_bound := noise_bound resolution.view left
  have right_bound := noise_bound resolution.view right
  have margin := margin_bound target_ne resolution
  nlinarith

theorem tomographicWeightedTaskFrameCertificate_add_weights_noisy_task_decoder_exists
    [Nonempty Answer]
    (rows : View → Coordinate → ℝ)
    (weight₁ weight₂ : View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate₁ : TomographicWeightedTaskFrameCertificate rows weight₁ target)
    (certificate₂ : TomographicWeightedTaskFrameCertificate rows weight₂ target)
    (noise : View → (Coordinate → ℝ) → ℝ)
    (error_budget : ∀ ⦃left right : Coordinate → ℝ⦄,
      target left ≠ target right →
      ∀ resolution : TomographicPairResolutionCertificate
        (fun view state => tomographicProjection rows state view) left right,
        |noise resolution.view left| + |noise resolution.view right| <
          resolution.margin) :
    ∃ decode : (∀ _ : View, ℝ) → Answer, ∀ state,
      decode (tomographicNoisyFusedImage
        (fun view state => tomographicProjection rows state view)
        noise state) = target state := by
  exact tomographicWeightedTaskFrameCertificate_noisy_task_decoder_exists
    rows (fun view => weight₁ view + weight₂ view) target
    (tomographicWeightedTaskFrameCertificate_add_weights
      rows weight₁ weight₂ target certificate₁ certificate₂)
    noise error_budget

theorem tomographicWeightedTaskFrameCertificate_identifies_task
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (target : (Coordinate → ℝ) → Answer)
    (certificate : TomographicWeightedTaskFrameCertificate rows weight target) :
    TomographicTaskIdentifiable
      (fun view state => tomographicProjection rows state view) target := by
  intro left right same
  by_contra target_ne
  have lower := certificate.lower_on_target_disagreement target_ne
  have projection_energy_zero :
      (∑ view, weight view *
        (tomographicProjection rows left view -
          tomographicProjection rows right view) ^ 2) = 0 := by
    apply Finset.sum_eq_zero
    intro view view_mem
    have projection_equal :
        tomographicProjection rows left view =
          tomographicProjection rows right view := congrFun same view
    simp [projection_equal]
  have upper : certificate.alpha *
      tomographicInner (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) ≤ 0 := by
    simpa [projection_energy_zero] using lower
  have lower_nonnegative : 0 ≤ certificate.alpha *
      tomographicInner (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) :=
    mul_nonneg (le_of_lt certificate.alpha_positive)
      (tomographicInner_nonnegative (fun coordinate => left coordinate - right coordinate))
  have product_zero : certificate.alpha *
      tomographicInner (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) = 0 :=
    le_antisymm upper lower_nonnegative
  have state_energy_zero :
      tomographicInner (fun coordinate => left coordinate - right coordinate)
        (fun coordinate => left coordinate - right coordinate) = 0 :=
    (mul_eq_zero.mp product_zero).resolve_left (ne_of_gt certificate.alpha_positive)
  have every_square_zero :
      (fun coordinate => (left coordinate - right coordinate) ^ 2) = 0 := by
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
      sq_nonneg (left coordinate - right coordinate))).mp
    simpa [tomographicInner, pow_two] using state_energy_zero
  have difference_zero :
      (fun coordinate => left coordinate - right coordinate) = 0 := by
    funext coordinate
    exact sq_eq_zero_iff.mp (congrFun every_square_zero coordinate)
  have states_equal : left = right := by
    funext coordinate
    exact sub_eq_zero.mp (congrFun difference_zero coordinate)
  exact target_ne (congrArg target states_equal)

theorem tomographicWeightedFrameCertificate_projection_separation
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (certificate : TomographicWeightedFrameCertificate rows weight)
    (left right : Coordinate → ℝ) :
    certificate.alpha *
        tomographicInner (fun coordinate => left coordinate - right coordinate)
          (fun coordinate => left coordinate - right coordinate) ≤
      ∑ view, weight view *
        (tomographicProjection rows left view -
          tomographicProjection rows right view) ^ 2 := by
  have lower := certificate.lower (fun coordinate => left coordinate - right coordinate)
  rw [tomographicWeightedNormalOperator_difference_energy_eq_weighted_projection_difference_energy]
    at lower
  exact lower

theorem tomographicWeightedFrameCertificate_task_decoder
    [Nonempty Answer]
    (rows : View → Coordinate → ℝ) (weight : View → ℝ)
    (certificate : TomographicWeightedFrameCertificate rows weight)
    (target : (Coordinate → ℝ) → Answer) :
    ∃ decode : (View → ℝ) → Answer,
      ∀ state, decode (tomographicProjection rows state) = target state := by
  let project : ∀ view, (Coordinate → ℝ) → ℝ := fun view state =>
    tomographicProjection rows state view
  have project_injective : Function.Injective
      (MultiTaskSignature (fun _ : View => ℝ) project) := by
    intro left right same
    apply tomographicWeightedFrameCertificate_projection_injective
      rows weight certificate
    funext view
    exact congrFun same view
  have task_identifiable : TomographicTaskIdentifiable project target := by
    exact jointly_injective_projections_identify_task project target
      project_injective
  have decoder_exists :=
    (tomographic_task_decoder_iff project target).2 task_identifiable
  obtain ⟨decode, correct⟩ := decoder_exists
  refine ⟨decode, ?_⟩
  intro state
  exact correct state

end FrameTaskBridge

end OCKIndividuationMSpaceComposition
