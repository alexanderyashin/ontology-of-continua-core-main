import OCKIndividuationMSpaceComposition.SymmetryNativeConstitutiveNaturalityBoundary

namespace OCKIndividuationMSpaceComposition

universe uIndex uChild uParent uEquiv

namespace NativeConstitutiveRelabelingComposition

open NativeConstitutiveNaturalityBoundary
open ConstitutiveBridge

variable {Index : Type uIndex}
variable {ChildState : Index → Type uChild}
variable {ParentState : Type uParent}

/-!
# Composition of explicit constitutive relabelings

`ConstitutiveRelabeling` is the explicit local symmetry interface from the
preceding slice.  This file proves its smallest closure laws: identity and
composition preserve admissibility and realization, and the resulting parent
configuration availability transports through a finite relabeling chain.

The preservation fields remain premises of each input relabeling.  The
composition theorem therefore does not manufacture symmetry from an
admissibility predicate, and it does not claim that arbitrary OC
transformations carry such a relabeling.  The asymmetric-parent countermodel
and the distinction between admissibility and realization remain the G7
boundary.

No causal dependency, action, rank, dimension, exchange, or continuum claim
is introduced.
-/

def composeEquiv {α : Type uEquiv} (first second : α ≃ α) : α ≃ α where
  toFun := fun value => second (first value)
  invFun := fun value => first.symm (second.symm value)
  left_inv := by
    intro value
    simp
  right_inv := by
    intro value
    simp

namespace ConstitutiveRelabeling

def id (bridge : ConstitutiveBridge Index ChildState ParentState) :
    ConstitutiveRelabeling bridge where
  configurationEquiv := Equiv.refl _
  parentEquiv := Equiv.refl _
  admissible_iff := by
    intro configuration
    simp
  realizes_iff := by
    intro configuration parent
    simp

def comp
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (first second : ConstitutiveRelabeling bridge) :
    ConstitutiveRelabeling bridge where
  configurationEquiv :=
    composeEquiv first.configurationEquiv second.configurationEquiv
  parentEquiv :=
    composeEquiv first.parentEquiv second.parentEquiv
  admissible_iff := by
    intro configuration
    simpa [composeEquiv] using
      (first.admissible_iff configuration).trans
        (second.admissible_iff (first.configurationEquiv configuration))
  realizes_iff := by
    intro configuration parent
    simpa [composeEquiv] using
      (first.realizes_iff configuration parent).trans
        (second.realizes_iff
          (first.configurationEquiv configuration)
          (first.parentEquiv parent))

end ConstitutiveRelabeling

theorem comp_preserves_parentConfigurationAvailable
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (first second : ConstitutiveRelabeling bridge)
    {parent : ParentState} :
    ParentConfigurationAvailable bridge parent →
      ParentConfigurationAvailable bridge
        ((ConstitutiveRelabeling.comp first second).parentEquiv parent) := by
  intro available
  have firstMapped := parentConfigurationAvailable_relabel first available
  have secondMapped := parentConfigurationAvailable_relabel second
    (parent := first.parentEquiv parent) firstMapped
  simpa [ConstitutiveRelabeling.comp, composeEquiv] using secondMapped

theorem comp_preserves_parentConfigurationAvailable_iff
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (first second : ConstitutiveRelabeling bridge)
    {parent : ParentState} :
    ParentConfigurationAvailable bridge parent ↔
      ParentConfigurationAvailable bridge
        ((ConstitutiveRelabeling.comp first second).parentEquiv parent) := by
  exact parentConfigurationAvailable_relabel_iff
    (ConstitutiveRelabeling.comp first second)

theorem comp_configuration_apply_assoc
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (first second third : ConstitutiveRelabeling bridge)
    (configuration : JointConfiguration Index ChildState) :
    (ConstitutiveRelabeling.comp
      (ConstitutiveRelabeling.comp first second) third).configurationEquiv
        configuration =
      (ConstitutiveRelabeling.comp first
        (ConstitutiveRelabeling.comp second third)).configurationEquiv
          configuration := by
  rfl

theorem comp_parent_apply_assoc
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (first second third : ConstitutiveRelabeling bridge)
    (parent : ParentState) :
    (ConstitutiveRelabeling.comp
      (ConstitutiveRelabeling.comp first second) third).parentEquiv parent =
      (ConstitutiveRelabeling.comp first
        (ConstitutiveRelabeling.comp second third)).parentEquiv parent := by
  rfl

theorem comp_id_parent_apply
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (relabeling : ConstitutiveRelabeling bridge)
    (parent : ParentState) :
    (ConstitutiveRelabeling.comp relabeling
      (ConstitutiveRelabeling.id bridge)).parentEquiv parent =
      relabeling.parentEquiv parent := by
  rfl

theorem id_comp_parent_apply
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (relabeling : ConstitutiveRelabeling bridge)
    (parent : ParentState) :
    (ConstitutiveRelabeling.comp
      (ConstitutiveRelabeling.id bridge) relabeling).parentEquiv parent =
      relabeling.parentEquiv parent := by
  rfl

end NativeConstitutiveRelabelingComposition

end OCKIndividuationMSpaceComposition
