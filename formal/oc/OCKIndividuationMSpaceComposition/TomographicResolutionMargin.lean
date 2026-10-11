import OCKIndividuationMSpaceComposition.TomographicTaskReconstruction
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite tomographic resolution margins

A positive separation margin is a source-bound distinguishability certificate
for one pair of declared states and one registered scalar view.  It is a
finite task/model contract: no physical Rayleigh limit, sampling theorem,
noise calibration, or global resolution constant is inferred.
-/

section ResolutionMargin

variable {World View Answer : Type*}

/-- A positive scalar margin witnessed by one registered projection. -/
structure TomographicPairResolutionCertificate
    (project : View → World → ℝ) (left right : World) where
  view : View
  margin : ℝ
  margin_positive : 0 < margin
  lower_bound : margin ≤ |project view left - project view right|

theorem tomographicPairResolutionCertificate_distinguishes
    (project : View → World → ℝ) (left right : World)
    (certificate : TomographicPairResolutionCertificate project left right) :
    project certificate.view left ≠ project certificate.view right := by
  intro equal
  have lower := certificate.lower_bound
  simp [equal] at lower
  linarith [certificate.margin_positive]

theorem tomographicPairResolutionCertificate_robust_to_bounded_error
    (project : View → World → ℝ) (left right : World)
    (certificate : TomographicPairResolutionCertificate project left right)
    (left_error right_error : ℝ)
    (error_budget : |left_error| + |right_error| < certificate.margin) :
    project certificate.view left + left_error ≠
      project certificate.view right + right_error := by
  intro equal
  have base_eq :
      project certificate.view left - project certificate.view right =
        right_error - left_error := by
    linarith
  have abs_bound :
      |project certificate.view left - project certificate.view right| ≤
        |right_error| + |left_error| := by
    rw [base_eq]
    simpa using (abs_sub_le (right_error : ℝ) (0 : ℝ) (left_error : ℝ))
  have lower := certificate.lower_bound
  nlinarith

/-- Every distinct pair has a positive-margin registered witness. -/
def TomographicPairwiseResolution
    (project : View → World → ℝ) : Prop :=
  ∀ ⦃left right : World⦄, left ≠ right →
    Nonempty (TomographicPairResolutionCertificate project left right)

/-- A task-relative resolution contract need only separate pairs whose target
    values differ.  This is strictly weaker than state injectivity and is the
    appropriate boundary for enterprise questions that do not require a
    unique reconstruction of every hidden state. -/
def TomographicTaskPairwiseResolution
    (project : View → World → ℝ) (target : World → Answer) : Prop :=
  ∀ ⦃left right : World⦄, target left ≠ target right →
    Nonempty (TomographicPairResolutionCertificate project left right)

/-! A scalar fused image with an explicitly registered additive error field. -/
def tomographicNoisyFusedImage
    (project : View → World → ℝ) (noise : View → World → ℝ) :
    World → View → ℝ :=
  fun world view => project view world + noise view world

theorem tomographic_noisy_fused_image_injective_of_pairwise_resolution
    (project : View → World → ℝ) (noise : View → World → ℝ)
    (resolution : TomographicPairwiseResolution project)
    (error_budget : ∀ ⦃left right : World⦄, left ≠ right →
      ∀ certificate : TomographicPairResolutionCertificate project left right,
        |noise certificate.view left| + |noise certificate.view right| <
          certificate.margin) :
    Function.Injective (tomographicNoisyFusedImage project noise) := by
  intro left right same
  by_cases equal : left = right
  · exact equal
  · obtain ⟨certificate⟩ := resolution equal
    have budget := error_budget equal certificate
    have unequal := tomographicPairResolutionCertificate_robust_to_bounded_error
      project left right certificate (noise certificate.view left)
      (noise certificate.view right) budget
    exact False.elim (unequal (congrFun same certificate.view))

theorem tomographic_noisy_fused_image_injective_of_uniform_error_bound
    (project : View → World → ℝ) (noise : View → World → ℝ)
    (resolution : TomographicPairwiseResolution project)
    (epsilon : ℝ) (epsilon_nonnegative : 0 ≤ epsilon)
    (noise_bound : ∀ view world, |noise view world| ≤ epsilon)
    (margin_bound : ∀ ⦃left right : World⦄, left ≠ right →
      ∀ certificate : TomographicPairResolutionCertificate project left right,
        2 * epsilon < certificate.margin) :
    Function.Injective (tomographicNoisyFusedImage project noise) := by
  apply tomographic_noisy_fused_image_injective_of_pairwise_resolution
    project noise resolution
  intro left right different certificate
  have left_bound := noise_bound certificate.view left
  have right_bound := noise_bound certificate.view right
  have margin := margin_bound different certificate
  nlinarith

theorem tomographic_noisy_fused_image_taskIdentifiable_of_task_pairwise_resolution
    (project : View → World → ℝ) (noise : View → World → ℝ)
    (target : World → Answer)
    (resolution : TomographicTaskPairwiseResolution project target)
    (error_budget : ∀ ⦃left right : World⦄, target left ≠ target right →
      ∀ certificate : TomographicPairResolutionCertificate project left right,
        |noise certificate.view left| + |noise certificate.view right| <
          certificate.margin) :
    TomographicTaskIdentifiable
      (fun view world => tomographicNoisyFusedImage project noise world view)
      target := by
  intro left right same
  by_contra different
  obtain ⟨certificate⟩ := resolution different
  have budget := error_budget different certificate
  have unequal := tomographicPairResolutionCertificate_robust_to_bounded_error
    project left right certificate (noise certificate.view left)
    (noise certificate.view right) budget
  exact unequal (congrFun same certificate.view)

theorem tomographic_noisy_fused_image_taskIdentifiable_of_uniform_task_resolution
    (project : View → World → ℝ) (noise : View → World → ℝ)
    (target : World → Answer)
    (resolution : TomographicTaskPairwiseResolution project target)
    (epsilon : ℝ) (epsilon_nonnegative : 0 ≤ epsilon)
    (noise_bound : ∀ view world, |noise view world| ≤ epsilon)
    (margin_bound : ∀ ⦃left right : World⦄, target left ≠ target right →
      ∀ certificate : TomographicPairResolutionCertificate project left right,
        2 * epsilon < certificate.margin) :
    TomographicTaskIdentifiable
      (fun view world => tomographicNoisyFusedImage project noise world view)
      target := by
  apply tomographic_noisy_fused_image_taskIdentifiable_of_task_pairwise_resolution
    project noise target resolution
  intro left right different certificate
  have left_bound := noise_bound certificate.view left
  have right_bound := noise_bound certificate.view right
  have margin := margin_bound different certificate
  nlinarith

theorem tomographic_noisy_task_decoder_exists_of_task_pairwise_resolution
    [Nonempty Answer]
    (project : View → World → ℝ) (noise : View → World → ℝ)
    (target : World → Answer)
    (resolution : TomographicTaskPairwiseResolution project target)
    (error_budget : ∀ ⦃left right : World⦄, target left ≠ target right →
      ∀ certificate : TomographicPairResolutionCertificate project left right,
        |noise certificate.view left| + |noise certificate.view right| <
          certificate.margin) :
    ∃ decode : (∀ _ : View, ℝ) → Answer, ∀ world,
      decode (tomographicNoisyFusedImage project noise world) = target world := by
  apply (tomographic_task_decoder_iff
    (project := fun view world => tomographicNoisyFusedImage project noise world view)
    target).2
  exact tomographic_noisy_fused_image_taskIdentifiable_of_task_pairwise_resolution
    project noise target resolution error_budget

theorem tomographic_view_separation_of_pairwise_resolution
    (project : View → World → ℝ)
    (resolution : TomographicPairwiseResolution project) :
    TomographicViewSeparation project := by
  intro left right different
  obtain ⟨certificate⟩ := resolution different
  exact ⟨certificate.view,
    tomographicPairResolutionCertificate_distinguishes project left right certificate⟩

theorem tomographic_fused_image_injective_of_pairwise_resolution
    (project : View → World → ℝ)
    (resolution : TomographicPairwiseResolution project) :
    Function.Injective (tomographicFusedImage project) := by
  exact tomographic_fused_image_injective_of_view_separation project
    (tomographic_view_separation_of_pairwise_resolution project resolution)

end ResolutionMargin

end OCKIndividuationMSpaceComposition
