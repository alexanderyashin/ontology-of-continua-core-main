import OCKIndividuationMSpaceComposition.TomographicTaskReconstruction
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Compatible-state fibres of a fused observation

Tomography returns a fibre of states compatible with the registered fused
observation, not automatically a unique object.  This module makes that fibre
explicit and proves the task-relative consequence: an identifiable target is
constant on the fibre, while a task-separating compatible pair refutes
task-identifiability.
-/

section CompatibleSet

variable {World View : Type*} {Reading : View → Type*}

def TomographicCompatible
    (project : ∀ view, World → Reading view)
    (observation : ∀ view, Reading view)
    (world : World) : Prop :=
  MultiTaskSignature Reading project world = observation

def tomographicCompatibleSet
    (project : ∀ view, World → Reading view)
    (observation : ∀ view, Reading view) : Set World :=
  {world | TomographicCompatible project observation world}

def tomographicRefinedCompatibleSet
    {Extra : Type*}
    (project : ∀ view, World → Reading view)
    (observation : ∀ view, Reading view)
    (extra : World → Extra)
    (extraObservation : Extra) : Set World :=
  {world | TomographicCompatible project observation world ∧
    extra world = extraObservation}

theorem tomographicRefinedCompatibleSet_eq_inter
    {Extra : Type*}
    (project : ∀ view, World → Reading view)
    (observation : ∀ view, Reading view)
    (extra : World → Extra)
    (extraObservation : Extra) :
    tomographicRefinedCompatibleSet project observation extra extraObservation =
      tomographicCompatibleSet project observation ∩
        {world | extra world = extraObservation} := by
  rfl

theorem tomographicRefinedCompatibleSet_subset
    {Extra : Type*}
    (project : ∀ view, World → Reading view)
    (observation : ∀ view, Reading view)
    (extra : World → Extra)
    (extraObservation : Extra) :
    tomographicRefinedCompatibleSet project observation extra extraObservation ⊆
      tomographicCompatibleSet project observation := by
  intro world compatible
  exact compatible.1

theorem tomographicCompatible_iff_pointwise
    (project : ∀ view, World → Reading view)
    (observation : ∀ view, Reading view)
    (world : World) :
    TomographicCompatible project observation world ↔
      ∀ view, project view world = observation view := by
  constructor
  · intro same view
    exact congrFun same view
  · intro same
    funext view
    exact same view

theorem tomographicCompatible_self
    (project : ∀ view, World → Reading view)
    (world : World) :
    TomographicCompatible project (MultiTaskSignature Reading project world) world :=
  rfl

theorem tomographicCompatible_target_constant
    {Answer : Type*}
    (project : ∀ view, World → Reading view)
    (target : World → Answer)
    (identifiable : TomographicTaskIdentifiable project target)
    (observation : ∀ view, Reading view)
    {left right : World}
    (leftCompatible : TomographicCompatible project observation left)
    (rightCompatible : TomographicCompatible project observation right) :
    target left = target right := by
  apply identifiable left right
  exact leftCompatible.trans rightCompatible.symm

theorem tomographicCompatibleSet_target_constant
    {Answer : Type*}
    (project : ∀ view, World → Reading view)
    (target : World → Answer)
    (identifiable : TomographicTaskIdentifiable project target)
    (observation : ∀ view, Reading view) :
    ∀ left ∈ tomographicCompatibleSet project observation,
      ∀ right ∈ tomographicCompatibleSet project observation,
        target left = target right := by
  intro left leftMember right rightMember
  exact tomographicCompatible_target_constant project target identifiable
    observation leftMember rightMember

theorem tomographicCompatibleSet_pair_refutes_task_identifiability
    {Answer : Type*}
    (project : ∀ view, World → Reading view)
    (target : World → Answer)
    (observation : ∀ view, Reading view)
    {left right : World}
    (different : target left ≠ target right) :
    ∀ leftCompatible : TomographicCompatible project observation left,
      ∀ rightCompatible : TomographicCompatible project observation right,
        ¬ TomographicTaskIdentifiable project target := by
  intro leftCompatible rightCompatible identifiable
  apply different
  exact tomographicCompatible_target_constant project target identifiable
    observation leftCompatible rightCompatible

end CompatibleSet

end OCKIndividuationMSpaceComposition