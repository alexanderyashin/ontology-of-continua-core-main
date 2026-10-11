import OCKIndividuationMSpaceComposition.TomographicCapturedField
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

universe uWorld uView uReading uAnswer uExtra

/-!
# Additional-observation obligations

An unobserved channel is useful only if it breaks the task-relevant aliases
that remain in the captured field.  This module states that requirement
without mutating the original field or pretending that a proposed channel has
already been acquired.
-/

section AdditionalObservation

variable {World : Type uWorld} {View : Type uView}
  {Reading : View → Type uReading} {Answer : Type uAnswer}
  {Extra : Type uExtra}

variable
  (field : TomographicCapturedField (World := World) (View := View)
    (Reading := Reading))
  (target : World → Answer)
  (extra : World → Extra)
  (extra_reading : Extra)

/-- Compatibility after a proposed additional channel is included.  The
original captured field remains read-only; only a hypothetical extra reading
is added to the conjunction. -/
def tomographicExtendedCompatible (world : World) : Prop :=
  tomographicCapturedFieldCompatible field world ∧ extra world = extra_reading

/-- The new channel is task-separating exactly where the old field still has a
task-relevant collision. -/
def TomographicAdditionalViewSeparates : Prop :=
  ∀ left right,
    tomographicCapturedFieldCompatible field left →
    tomographicCapturedFieldCompatible field right →
    target left ≠ target right →
    extra left ≠ extra right

theorem tomographicExtendedClaimSupported_of_separates
    (separates : TomographicAdditionalViewSeparates field target extra) :
    ∀ left right,
      tomographicExtendedCompatible field extra extra_reading left →
      tomographicExtendedCompatible field extra extra_reading right →
      target left = target right := by
  intro left right left_compatible right_compatible
  by_contra different
  have extra_different : extra left ≠ extra right :=
    separates left right left_compatible.1 right_compatible.1 different
  exact extra_different (left_compatible.2.trans right_compatible.2.symm)

theorem tomographicAdditionalView_missing_pair_refutes_separation
    (left right : World)
    (left_compatible : tomographicCapturedFieldCompatible field left)
    (right_compatible : tomographicCapturedFieldCompatible field right)
    (task_different : target left ≠ target right)
    (extra_equal : extra left = extra right) :
    ¬ TomographicAdditionalViewSeparates field target extra := by
  intro separates
  exact (separates left right left_compatible right_compatible task_different)
    extra_equal

theorem tomographicExtendedCompatible_implies_old_compatible
    {world : World}
    (compatible : tomographicExtendedCompatible field extra extra_reading world) :
    tomographicCapturedFieldCompatible field world :=
  compatible.1

end AdditionalObservation

end OCKIndividuationMSpaceComposition
