import OCKIndividuationMSpaceComposition.TomographicCapturedField
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

universe uWorld uView uReading uAnswer

/-!
# Observation, claim and reconstruction support

The three support levels are deliberately distinct.  Observation support is
the set of worlds compatible with the readings that were actually captured.
Claim support asks only that a named task be constant on that set.  Full
reconstruction support asks for a singleton compatible set.  No level is
silently promoted to the next one.
-/

section SupportBoundary

variable {World : Type uWorld} {View : Type uView}
  {Reading : View → Type uReading} {Answer : Type uAnswer}

variable
  (field : TomographicCapturedField (World := World) (View := View)
    (Reading := Reading))
  (target : World → Answer)

/-- Worlds supported by the registered captured observations. -/
def tomographicObservationSupport : Set World :=
  {world | tomographicCapturedFieldCompatible field world}

/-- The strongest support level: the captured field has at most one compatible
world.  Existence of a compatible world remains a separate question. -/
def tomographicReconstructionSupport : Prop :=
  ∀ left right,
    left ∈ tomographicObservationSupport field →
    right ∈ tomographicObservationSupport field →
    left = right

/-- A task is supported when its answer is constant over observation support. -/
def tomographicClaimSupport : Prop :=
  ∀ left right,
    left ∈ tomographicObservationSupport field →
    right ∈ tomographicObservationSupport field →
    target left = target right

theorem tomographicObservationSupport_mem_iff (world : World) :
    world ∈ tomographicObservationSupport field ↔
      tomographicCapturedFieldCompatible field world := by
  rfl

theorem tomographicReconstructionSupport_implies_claimSupport
    (reconstructs : tomographicReconstructionSupport field) :
    tomographicClaimSupport field target := by
  intro left right left_supported right_supported
  exact congrArg target (reconstructs left right left_supported right_supported)

theorem tomographicReconstructionSupport_implies_uniqueCompatible
    (reconstructs : tomographicReconstructionSupport field) :
    ∀ left right,
      tomographicCapturedFieldCompatible field left →
      tomographicCapturedFieldCompatible field right →
      left = right := by
  intro left right left_compatible right_compatible
  exact reconstructs left right left_compatible right_compatible

theorem tomographicClaimSupport_iff_no_missing_observation :
    tomographicClaimSupport field target ↔
      ¬ TomographicMissingObservation field target := by
  constructor
  · intro supported missing
    obtain ⟨left, right, left_compatible, right_compatible, different⟩ := missing
    exact different (supported left right left_compatible right_compatible)
  · intro no_missing left right left_supported right_supported
    by_contra different
    exact no_missing ⟨left, right, left_supported, right_supported, different⟩

theorem tomographicClaimSupport_of_capturedFieldClaimSupported
    (supported : tomographicCapturedFieldClaimSupported field target) :
    tomographicClaimSupport field target := by
  intro left right left_supported right_supported
  exact supported left right left_supported right_supported

/-! A non-singleton support can still yield a quantitative task envelope when
the target has a declared modulus and the compatible worlds have bounded
diameter.  This is an uncertainty bound, not a unique reconstruction claim. -/
theorem tomographicClaimSupport_target_distance_bound
    [PseudoMetricSpace World] [PseudoMetricSpace Answer]
    (radius modulus : ℝ) (radius_nonnegative : 0 ≤ radius)
    (modulus_nonnegative : 0 ≤ modulus)
    (target_modulus : ∀ left right,
      dist (target left) (target right) ≤ modulus * dist left right)
    (support_diameter : ∀ left right,
      left ∈ tomographicObservationSupport field →
      right ∈ tomographicObservationSupport field →
      dist left right ≤ radius) :
    ∀ left right,
      left ∈ tomographicObservationSupport field →
      right ∈ tomographicObservationSupport field →
      dist (target left) (target right) ≤ modulus * radius := by
  intro left right left_supported right_supported
  exact le_trans (target_modulus left right)
    (mul_le_mul_of_nonneg_left
      (support_diameter left right left_supported right_supported)
      modulus_nonnegative)

end SupportBoundary

end OCKIndividuationMSpaceComposition