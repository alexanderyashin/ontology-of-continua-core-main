import OCKIndividuationMSpaceComposition.TomographicSupportBoundary
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

universe uWorld uView uReading uAnswer

/-!
# Multimodal support for fused projections

Two independently captured fields are fused by conjunction of their
compatibility predicates.  This is the conservative mathematical counterpart
of multimodal imaging: fusion may remove aliases, but it may not manufacture a
world that either source rejects.  Contradictory fields therefore produce an
empty support rather than an averaged or silently repaired observation.
-/

section MultimodalFusion

variable {World : Type uWorld} {View : Type uView}
  {Reading : View → Type uReading} {Answer : Type uAnswer}

variable
  (left right : TomographicCapturedField (World := World) (View := View)
    (Reading := Reading))
  (target : World → Answer)

/-- Compatibility with two captured fields at once. -/
def tomographicJointCompatible (world : World) : Prop :=
  tomographicCapturedFieldCompatible left world ∧
    tomographicCapturedFieldCompatible right world

/-- The fused multimodal support is the intersection of the two supports. -/
def tomographicJointSupport : Set World :=
  {world | tomographicJointCompatible left right world}

theorem tomographicJointSupport_mem_iff (world : World) :
    world ∈ tomographicJointSupport left right ↔
      tomographicCapturedFieldCompatible left world ∧
        tomographicCapturedFieldCompatible right world := by
  rfl

theorem tomographicJointSupport_subset_left :
    ∀ {world}, world ∈ tomographicJointSupport left right →
      world ∈ tomographicObservationSupport left := by
  intro world supported
  exact supported.1

theorem tomographicJointSupport_subset_right :
    ∀ {world}, world ∈ tomographicJointSupport left right →
      world ∈ tomographicObservationSupport right := by
  intro world supported
  exact supported.2

/-- Any incompatibility in either modality excludes the world from fusion. -/
theorem tomographicJointSupport_rejects_left_incompatible
    {world : World}
    (left_incompatible : ¬ tomographicCapturedFieldCompatible left world) :
    world ∉ tomographicJointSupport left right := by
  intro joint
  exact left_incompatible joint.1

theorem tomographicJointSupport_rejects_right_incompatible
    {world : World}
    (right_incompatible : ¬ tomographicCapturedFieldCompatible right world) :
    world ∉ tomographicJointSupport left right := by
  intro joint
  exact right_incompatible joint.2

/-- Task support survives fusion whenever either input field already supports
the task.  The theorem is deliberately one-way: a second modality may resolve
an alias that the first modality could not resolve. -/
def tomographicJointClaimSupport : Prop :=
  ∀ leftWorld rightWorld,
    leftWorld ∈ tomographicJointSupport left right →
    rightWorld ∈ tomographicJointSupport left right →
    target leftWorld = target rightWorld

theorem tomographicJointClaimSupport_of_left
    (left_supported : tomographicClaimSupport left target) :
    tomographicJointClaimSupport left right target := by
  intro leftWorld rightWorld left_joint right_joint
  exact left_supported leftWorld rightWorld left_joint.1 right_joint.1

theorem tomographicJointClaimSupport_of_right
    (right_supported : tomographicClaimSupport right target) :
    tomographicJointClaimSupport left right target := by
  intro leftWorld rightWorld left_joint right_joint
  exact right_supported leftWorld rightWorld left_joint.2 right_joint.2

/-! Intersecting modalities also intersects their quantitative uncertainty
    envelopes.  The conclusion is deliberately a minimum of two declared
    radii; it is not an assertion that fusion reconstructs a unique world. -/
theorem tomographicJointSupport_target_distance_bound
    [PseudoMetricSpace World]
    [PseudoMetricSpace Answer]
    (left_radius right_radius modulus : ℝ)
    (left_radius_nonnegative : 0 ≤ left_radius)
    (right_radius_nonnegative : 0 ≤ right_radius)
    (modulus_nonnegative : 0 ≤ modulus)
    (target_modulus : ∀ first second,
      dist (target first) (target second) ≤ modulus * dist first second)
    (left_diameter : ∀ first second,
      first ∈ tomographicObservationSupport left →
      second ∈ tomographicObservationSupport left →
      dist first second ≤ left_radius)
    (right_diameter : ∀ first second,
      first ∈ tomographicObservationSupport right →
      second ∈ tomographicObservationSupport right →
      dist first second ≤ right_radius) :
    ∀ first second,
      first ∈ tomographicJointSupport left right →
      second ∈ tomographicJointSupport left right →
      dist (target first) (target second) ≤
        modulus * min left_radius right_radius := by
  intro first second first_joint second_joint
  have left_bound := tomographicClaimSupport_target_distance_bound
    left target left_radius modulus left_radius_nonnegative modulus_nonnegative
    target_modulus left_diameter first second
    (tomographicJointSupport_subset_left left right first_joint)
    (tomographicJointSupport_subset_left left right second_joint)
  have right_bound := tomographicClaimSupport_target_distance_bound
    right target right_radius modulus right_radius_nonnegative modulus_nonnegative
    target_modulus right_diameter first second
    (tomographicJointSupport_subset_right left right first_joint)
    (tomographicJointSupport_subset_right left right second_joint)
  by_cases radius_order : left_radius ≤ right_radius
  · calc
      dist (target first) (target second) ≤ modulus * left_radius := left_bound
      _ = modulus * min left_radius right_radius := by
        rw [min_eq_left radius_order]
  · have reversed_order : right_radius ≤ left_radius := le_of_not_ge radius_order
    calc
      dist (target first) (target second) ≤ modulus * right_radius := right_bound
      _ = modulus * min left_radius right_radius := by
        rw [min_eq_right reversed_order]

end MultimodalFusion

section FiniteModalities

variable {Modality World Answer : Type*} [DecidableEq Modality]

/-! A finite family version avoids treating a two-sensor example as the
    universal fusion primitive.  Every modality contributes an explicit
    support predicate; adding modalities can only remove compatible worlds. -/
def tomographicFiniteJointSupport
    (supports : Modality → Set World)
    (modalities : Finset Modality) : Set World :=
  {world | ∀ modality, modality ∈ modalities → world ∈ supports modality}

theorem tomographicFiniteJointSupport_mem_iff
    (supports : Modality → Set World)
    (modalities : Finset Modality)
    (world : World) :
    world ∈ tomographicFiniteJointSupport supports modalities ↔
      ∀ modality, modality ∈ modalities → world ∈ supports modality := by
  rfl

theorem tomographicFiniteJointSupport_mono
    (supports : Modality → Set World)
    {small large : Finset Modality}
    (included : small ⊆ large) :
    tomographicFiniteJointSupport supports large ⊆
      tomographicFiniteJointSupport supports small := by
  intro world supported modality modality_member
  exact supported modality (included modality_member)

theorem tomographicFiniteJointSupport_claimSupport_of_member
    (supports : Modality → Set World)
    (modalities : Finset Modality)
    (target : World → Answer)
    (modality : Modality)
    (modality_member : modality ∈ modalities)
    (claim_supported : ∀ left right,
      left ∈ supports modality →
      right ∈ supports modality →
      target left = target right) :
    ∀ left right,
      left ∈ tomographicFiniteJointSupport supports modalities →
      right ∈ tomographicFiniteJointSupport supports modalities →
      target left = target right := by
  intro left right left_supported right_supported
  exact claim_supported left right
    (left_supported modality modality_member)
    (right_supported modality modality_member)

theorem tomographicFiniteJointSupport_claimSupport_mono
    (supports : Modality → Set World)
    {small large : Finset Modality}
    (included : small ⊆ large)
    (target : World → Answer)
    (claim_supported : ∀ left right,
      left ∈ tomographicFiniteJointSupport supports small →
      right ∈ tomographicFiniteJointSupport supports small →
      target left = target right) :
    ∀ left right,
      left ∈ tomographicFiniteJointSupport supports large →
      right ∈ tomographicFiniteJointSupport supports large →
      target left = target right := by
  intro left right left_supported right_supported
  apply claim_supported left right
  · exact tomographicFiniteJointSupport_mono supports included left_supported
  · exact tomographicFiniteJointSupport_mono supports included right_supported

theorem tomographicFiniteJointSupport_target_distance_bound_of_member
    [PseudoMetricSpace World]
    [PseudoMetricSpace Answer]
    (supports : Modality → Set World)
    (modalities : Finset Modality)
    (target : World → Answer)
    (modality : Modality)
    (modality_member : modality ∈ modalities)
    (radius modulus : ℝ)
    (modulus_nonnegative : 0 ≤ modulus)
    (target_modulus : ∀ first second,
      dist (target first) (target second) ≤ modulus * dist first second)
    (diameter : ∀ first second,
      first ∈ supports modality →
      second ∈ supports modality →
      dist first second ≤ radius) :
    ∀ first second,
      first ∈ tomographicFiniteJointSupport supports modalities →
      second ∈ tomographicFiniteJointSupport supports modalities →
      dist (target first) (target second) ≤ modulus * radius := by
  intro first second first_supported second_supported
  calc
    dist (target first) (target second) ≤ modulus * dist first second :=
      target_modulus first second
    _ ≤ modulus * radius := by
      exact mul_le_mul_of_nonneg_left
        (diameter first second
          (first_supported modality modality_member)
          (second_supported modality modality_member))
        modulus_nonnegative

end FiniteModalities

end OCKIndividuationMSpaceComposition