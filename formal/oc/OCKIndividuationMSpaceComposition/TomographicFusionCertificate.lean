import OCKIndividuationMSpaceComposition.TomographicViewJoin
import OCKIndividuationMSpaceComposition.TomographicInverseCertificate
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Certified fusion of a finite projection family

The fused image is the complete registered family of measurements.  This
module adds the missing contract between that image and a reconstruction
operator: exact recovery on the declared model class plus a finite noise gain.
The certificate is intentionally supplied by the caller; merely concatenating
views does not prove injectivity, calibration, or semantic identification.
-/

section FusionCertificate

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View]

/-- The finite multidimensional measurement image of a state. -/
def tomographicFiniteFusedImage
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) : View → ℝ :=
  tomographicProjection rows state

@[simp] theorem tomographicFiniteFusedImage_coordinate
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) (view : View) :
    tomographicFiniteFusedImage rows state view =
      tomographicProjection rows state view := rfl

theorem tomographicFiniteFusedImage_add
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicFiniteFusedImage rows (fun coordinate =>
      left coordinate + right coordinate) =
      fun view => tomographicFiniteFusedImage rows left view +
        tomographicFiniteFusedImage rows right view := by
  classical
  exact tomographicProjection_add rows left right

theorem tomographicFiniteFusedImage_smul
    (rows : View → Coordinate → ℝ)
    (scalar : ℝ) (state : Coordinate → ℝ) :
    tomographicFiniteFusedImage rows (fun coordinate =>
      scalar * state coordinate) =
      fun view => scalar * tomographicFiniteFusedImage rows state view := by
  classical
  exact tomographicProjection_smul rows scalar state

theorem tomographicFiniteFusedImage_eq_iff
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicFiniteFusedImage rows left =
        tomographicFiniteFusedImage rows right ↔
      ∀ view, tomographicProjection rows left view =
        tomographicProjection rows right view := by
  constructor
  · intro equal view
    exact congrFun equal view
  · intro equal
    exact funext equal

/-! A fusion certificate is an exact left inverse with an explicit stability
constant.  It is the finite analogue of a tomography reconstruction guarantee,
not a claim that a particular numerical algorithm has already been certified.
-/
structure TomographicFusionCertificate
    (rows : View → Coordinate → ℝ) where
  reconstruct : (View → ℝ) → Coordinate → ℝ
  exact_on_model : ∀ state,
    reconstruct (tomographicFiniteFusedImage rows state) = state
  noiseGain : ℝ
  noiseGain_nonnegative : 0 ≤ noiseGain
  reconstruct_lipschitz : ∀ first second,
    dist (reconstruct first) (reconstruct second) ≤
      noiseGain * dist first second

def TomographicFusionCertificate.asStableLeftInverse
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFusionCertificate rows) :
    TomographicStableLeftInverse rows :=
  { reconstruct := certificate.reconstruct
    left_inverse := certificate.exact_on_model
    lipschitzConstant := certificate.noiseGain
    lipschitz_nonnegative := certificate.noiseGain_nonnegative
    reconstruct_lipschitz := certificate.reconstruct_lipschitz }

theorem tomographicFusion_exact_reconstruction
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFusionCertificate rows)
    (state : Coordinate → ℝ) :
    certificate.reconstruct (tomographicFiniteFusedImage rows state) = state :=
  certificate.exact_on_model state

theorem tomographicFusion_injective_of_certificate
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFusionCertificate rows) :
    Function.Injective (tomographicFiniteFusedImage rows) := by
  exact tomographicProjection_injective_of_left_inverse
    { reconstruct := certificate.reconstruct
      left_inverse := certificate.exact_on_model }

theorem tomographicFusion_target_equal_of_certificate
    {Answer : Type*}
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFusionCertificate rows)
    (target : (Coordinate → ℝ) → Answer)
    (left right : Coordinate → ℝ)
    (fused_equal : tomographicFiniteFusedImage rows left =
      tomographicFiniteFusedImage rows right) :
    target left = target right := by
  exact congrArg target
    ((tomographicFusion_injective_of_certificate certificate) fused_equal)

theorem tomographicFusion_target_decoder_of_certificate
    {Answer : Type*}
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFusionCertificate rows)
    (target : (Coordinate → ℝ) → Answer) :
    ∃ decode : (View → ℝ) → Answer, ∀ state,
      decode (tomographicFiniteFusedImage rows state) = target state := by
  refine ⟨fun data => target (certificate.reconstruct data), ?_⟩
  intro state
  change target (certificate.reconstruct (tomographicFiniteFusedImage rows state)) =
    target state
  rw [certificate.exact_on_model]

theorem tomographicFusion_unique_reconstruction
    {rows : View → Coordinate → ℝ}
    (first second : (View → ℝ) → Coordinate → ℝ)
    (first_exact : ∀ state,
      first (tomographicFiniteFusedImage rows state) = state)
    (second_exact : ∀ state,
      second (tomographicFiniteFusedImage rows state) = state)
    (state : Coordinate → ℝ) :
    first (tomographicFiniteFusedImage rows state) =
      second (tomographicFiniteFusedImage rows state) := by
  rw [first_exact state, second_exact state]

theorem tomographicFusion_noise_bound
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFusionCertificate rows)
    (state : Coordinate → ℝ) (data : View → ℝ) (budget : ℝ)
    (measurementBound :
      dist data (tomographicFiniteFusedImage rows state) ≤ budget) :
    dist (certificate.reconstruct data) state ≤
      certificate.noiseGain * budget := by
  exact tomographicStableInverse_error_bound
    (TomographicFusionCertificate.asStableLeftInverse certificate)
    state data budget measurementBound

/-! A stable reconstruction budget can be transported directly to a task
    observable with an explicit state-to-task modulus. -/
theorem tomographicFusion_task_noise_bound
    {Answer : Type*} [PseudoMetricSpace Answer]
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFusionCertificate rows)
    (target : (Coordinate → ℝ) → Answer)
    (target_constant : ℝ) (target_constant_nonnegative : 0 ≤ target_constant)
    (target_modulus : ∀ first second,
      dist (target first) (target second) ≤
        target_constant * dist first second)
    (state : Coordinate → ℝ) (data : View → ℝ) (budget : ℝ)
    (measurementBound :
      dist data (tomographicFiniteFusedImage rows state) ≤ budget) :
    dist (target (certificate.reconstruct data)) (target state) ≤
      target_constant * certificate.noiseGain * budget := by
  have state_bound := tomographicFusion_noise_bound
    certificate state data budget measurementBound
  calc
    dist (target (certificate.reconstruct data)) (target state) ≤
        target_constant * dist (certificate.reconstruct data) state :=
      target_modulus _ _
    _ ≤ target_constant * (certificate.noiseGain * budget) :=
      mul_le_mul_of_nonneg_left state_bound target_constant_nonnegative
    _ = target_constant * certificate.noiseGain * budget := by
      simp [mul_assoc]

theorem tomographicFusion_target_decoder_with_noise_bound
    {Answer : Type*} [PseudoMetricSpace Answer]
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicFusionCertificate rows)
    (target : (Coordinate → ℝ) → Answer)
    (target_constant : ℝ) (target_constant_nonnegative : 0 ≤ target_constant)
    (target_modulus : ∀ first second,
      dist (target first) (target second) ≤
        target_constant * dist first second) :
    ∃ decode : (View → ℝ) → Answer,
      (∀ state,
        decode (tomographicFiniteFusedImage rows state) = target state) ∧
      (∀ state data budget,
        dist data (tomographicFiniteFusedImage rows state) ≤ budget →
          dist (decode data) (target state) ≤
            target_constant * certificate.noiseGain * budget) := by
  refine ⟨fun data => target (certificate.reconstruct data), ?_, ?_⟩
  · intro state
    change target (certificate.reconstruct (tomographicFiniteFusedImage rows state)) =
      target state
    rw [certificate.exact_on_model]
  · intro state data budget measurementBound
    exact tomographicFusion_task_noise_bound certificate target target_constant
      target_constant_nonnegative target_modulus state data budget
      measurementBound

end FusionCertificate

end OCKIndividuationMSpaceComposition
