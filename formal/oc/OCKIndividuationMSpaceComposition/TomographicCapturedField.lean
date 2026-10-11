import OCKIndividuationMSpaceComposition.TomographicTaskReconstruction
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

universe uWorld uView uReading uAnswer

/-!
# Captured fields and task claim ceilings

This module separates a registered observation field from the full family of
possible views.  A field records which views were actually captured and the
typed reading attached to each one.  Compatibility is therefore a property of
a world relative to the captured field, not an assumption that every possible
view has been observed.  The resulting claim ceiling is intentionally
task-relative and makes unresolved observational aliases explicit.
-/

section CapturedField

variable {World : Type uWorld} {View : Type uView}
  {Reading : View → Type uReading} {Answer : Type uAnswer}

/-- A source-bound finite or partial capture of a registered view family. -/
structure TomographicCapturedField where
  project : ∀ view, World → Reading view
  captured : Set View
  reading : ∀ view, captured view → Reading view

/-- A world is compatible with the readings that were actually captured. -/
def tomographicCapturedFieldCompatible
    (field : TomographicCapturedField (World := World) (View := View)
      (Reading := Reading)) (world : World) : Prop :=
  ∀ view (captured : field.captured view),
    field.project view world = field.reading view captured

/-- A task is supported by a captured field when it is constant on its
    compatible states.  This is the field-level claim ceiling. -/
def tomographicCapturedFieldClaimSupported
    (field : TomographicCapturedField (World := World) (View := View)
      (Reading := Reading)) (target : World → Answer) : Prop :=
  ∀ left right,
    tomographicCapturedFieldCompatible field left →
    tomographicCapturedFieldCompatible field right →
    target left = target right

/-- An explicit unresolved pair: the same captured field is compatible with
    two states that disagree on the requested task. -/
def TomographicMissingObservation
    (field : TomographicCapturedField (World := World) (View := View)
      (Reading := Reading)) (target : World → Answer) : Prop :=
  ∃ left right,
    tomographicCapturedFieldCompatible field left ∧
    tomographicCapturedFieldCompatible field right ∧
    target left ≠ target right

theorem tomographicCapturedField_claimSupported_iff_no_missing_observation
    (field : TomographicCapturedField (World := World) (View := View)
      (Reading := Reading)) (target : World → Answer) :
    tomographicCapturedFieldClaimSupported field target ↔
      ¬ TomographicMissingObservation field target := by
  constructor
  · intro supported missing
    obtain ⟨left, right, left_compatible, right_compatible, different⟩ := missing
    exact different (supported left right left_compatible right_compatible)
  · intro no_missing left right left_compatible right_compatible
    by_contra different
    exact no_missing ⟨left, right, left_compatible, right_compatible, different⟩

theorem tomographicCapturedField_claimSupported_of_unique_compatible
    (field : TomographicCapturedField (World := World) (View := View)
      (Reading := Reading)) (target : World → Answer)
    (unique : ∀ left right,
      tomographicCapturedFieldCompatible field left →
      tomographicCapturedFieldCompatible field right → left = right) :
    tomographicCapturedFieldClaimSupported field target := by
  intro left right left_compatible right_compatible
  exact congrArg target (unique left right left_compatible right_compatible)

theorem tomographicCapturedField_forward_compatible
    (field : TomographicCapturedField (World := World) (View := View)
      (Reading := Reading)) (world : World)
    (forward : ∀ view (captured : field.captured view),
      field.project view world = field.reading view captured) :
    tomographicCapturedFieldCompatible field world :=
  forward

theorem tomographicCapturedField_missing_observation_refutes_claim
    (field : TomographicCapturedField (World := World) (View := View)
      (Reading := Reading)) (target : World → Answer)
    (missing : TomographicMissingObservation field target) :
    ¬ tomographicCapturedFieldClaimSupported field target := by
  intro supported
  exact (tomographicCapturedField_claimSupported_iff_no_missing_observation
    field target).mp supported missing

end CapturedField

end OCKIndividuationMSpaceComposition