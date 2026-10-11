import OCKIndividuationMSpaceComposition.SymmetryNativeConstitutiveJointComposition
import OCKIndividuationMSpaceComposition.SymmetryNativeCausalFamilyClosure
import OCKIndividuationMSpaceComposition.SymmetryJointCompositionBoundary
import Mathlib.Data.Fin.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uMechanism uIntervention uOutcome uOld

namespace NativeIrreducibilityBoundary

open ActiveConstraintModel
open JointCompositionBoundary

variable {Mechanism : Type uMechanism} [DecidableEq Mechanism]
variable {Intervention : Type uIntervention} {Outcome : Type uOutcome}

/-!
# Representation-preserving irreducibility

`familyGenerated` is the existing causal derivability relation.  Its failure
is a useful no-go fact, but by itself it is not irreducibility: a target can be
outside the current causal kernel while the whole finite extension still has a
faithful representation in an old carrier.

The representation interface below is deliberately independent of rank,
coordinates, exchange, or a closure imported as a primitive.  It asks for an
injective encoding of the old seed together with the candidate target, and for
exact preservation of the native one-root `GeneratedKernel` relation.  Only
the absence of such an encoding is called representation-preserving
irreducibility.
-/

abbrev ExtensionPoint
    (seed : Finset Mechanism) (target : Mechanism) :=
  {point // point ∈ insert target seed}

structure FaithfulOldRepresentation
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (seed : Finset Mechanism) (target : Mechanism)
    (Old : Type uOld)
    (oldGeneration : Old → Old → Prop) where
  encode : ExtensionPoint seed target → Old
  injective : Function.Injective encode
  generation_iff : ∀ (first second : ExtensionPoint seed target),
    GeneratedKernel model first.1 second.1 ↔
      oldGeneration (encode first) (encode second)

/-- Causal derivability remains the existing family-generated relation. -/
def causallyDerivable
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (seed : Finset Mechanism) (target : Mechanism) : Prop :=
  familyGenerated model (↑seed : Set Mechanism) target

/-! A constitutive joint result is kept as a separate relation.  It is not
identified with `familyGenerated`; the three conjuncts explicitly require
pair support and failure of each singleton support. -/

def ConstitutiveJointEmergence
    (premise : JointClosurePremise Mechanism)
    (first second target : Mechanism) : Prop :=
  premise.jointGenerated ({first, second} : Finset Mechanism) target ∧
    ¬ premise.jointGenerated ({first} : Finset Mechanism) target ∧
    ¬ premise.jointGenerated ({second} : Finset Mechanism) target

def RepresentationPreservingIrreducible
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (seed : Finset Mechanism) (target : Mechanism)
    (Old : Type uOld)
    (oldGeneration : Old → Old → Prop) : Prop :=
  ¬ Nonempty (FaithfulOldRepresentation model seed target Old oldGeneration)

/-! ## A positive finite obstruction -/

def noDependencyModel :
    ActiveConstraintModel (Fin 3) Unit Bool where
  response := fun _ _ => false
  responseWithout := fun _ _ _ => false
  port := fun _ => False

theorem noDependency_has_no_internal_dependency
    {first second : Fin 3} :
    ¬ InternalDependency noDependencyModel first second := by
  intro dependency
  rcases dependency.2 with essential | essential
  · rcases essential with ⟨witness⟩
    exact witness.changes rfl
  · rcases essential with ⟨witness⟩
    exact witness.changes rfl

theorem noDependency_generated_iff
    {root target : Fin 3} :
    GeneratedKernel noDependencyModel root target ↔ target = root := by
  constructor
  · intro generated
    induction generated with
    | ofRoot => rfl
    | ofInternalDependency previous dependency inductionHypothesis =>
        exact (noDependency_has_no_internal_dependency dependency).elim
  · intro target_eq
    cases target_eq
    exact .ofRoot

def positiveSeed : Finset (Fin 3) := {0, 1}

def positiveTarget : Fin 3 := 2

theorem positive_extension_card :
    Fintype.card (ExtensionPoint positiveSeed positiveTarget) = 3 := by
  decide

theorem positive_target_not_causally_derivable :
    ¬ causallyDerivable noDependencyModel positiveSeed positiveTarget := by
  intro generated
  rcases generated with ⟨root, root_member, path⟩
  have root_eq_target : positiveTarget = root :=
    (noDependency_generated_iff).mp path
  have target_member : positiveTarget ∈ positiveSeed := by
    rw [root_eq_target]
    simpa using root_member
  simp [positiveSeed, positiveTarget] at target_member

theorem positive_extension_not_representable_in_fin_two :
    ¬ Nonempty (FaithfulOldRepresentation
      noDependencyModel positiveSeed positiveTarget (Fin 2)
      (fun _ _ => True)) := by
  rintro ⟨representation⟩
  have card_bound :
      Fintype.card (ExtensionPoint positiveSeed positiveTarget) ≤
        Fintype.card (Fin 2) :=
    Fintype.card_le_of_injective representation.encode representation.injective
  rw [positive_extension_card] at card_bound
  simpa using card_bound

theorem positive_witness_is_representation_preserving_irreducible :
    RepresentationPreservingIrreducible
      noDependencyModel positiveSeed positiveTarget (Fin 2)
      (fun _ _ => True) := by
  exact positive_extension_not_representable_in_fin_two

/-! ## A negative witness: non-derivable does not entail irreducible -/

def negativeSeed : Finset ToyMechanism := {.left}

def negativeTarget : ToyMechanism := .environment

def negativeOldGeneration :
    ExtensionPoint negativeSeed negativeTarget →
      ExtensionPoint negativeSeed negativeTarget → Prop :=
  fun first second =>
    GeneratedKernel toyConstraintModel first.1 second.1

def negativeIdentityRepresentation :
    FaithfulOldRepresentation toyConstraintModel negativeSeed negativeTarget
      (ExtensionPoint negativeSeed negativeTarget) negativeOldGeneration where
  encode := id
  injective := Function.injective_id
  generation_iff := by
    intro first second
    rfl

theorem negative_target_not_causally_derivable :
    ¬ causallyDerivable toyConstraintModel negativeSeed negativeTarget := by
  intro generated
  rcases generated with ⟨root, root_member, path⟩
  have root_eq_left : root = .left := by
    simpa [negativeSeed] using root_member
  subst root
  exact (generatedKernel_contains_no_ports
    (model := toyConstraintModel)
    (root := ToyMechanism.left)
    (mechanism := ToyMechanism.environment)
    (by simp [toyConstraintModel]) path)
    (by simp [toyConstraintModel])

theorem negative_witness_is_not_irreducible :
    ¬ RepresentationPreservingIrreducible
      toyConstraintModel negativeSeed negativeTarget
      (ExtensionPoint negativeSeed negativeTarget) negativeOldGeneration := by
  intro irreducible
  exact irreducible ⟨negativeIdentityRepresentation⟩

/-! ## Constitutive joint emergence is a third, separate status -/

theorem twoRoot_constitutive_joint_emergence :
    ConstitutiveJointEmergence twoRootJointPremise 0 1 2 := by
  refine ⟨twoRoot_target_is_joint, ?_, ?_⟩
  · simpa [twoRootJointPremise] using
      twoRoot_target_not_singleton_generated.1
  · simpa [twoRootJointPremise] using
      twoRoot_target_not_singleton_generated.2

/-! The three witnesses are the G2 classification boundary: positive
representational obstruction, negative causal non-derivability with a faithful
old representation, and constitutive pair-only emergence. -/

theorem g2_witnesses_separate_derivability_joint_emergence_and_irreducibility :
    (¬ causallyDerivable noDependencyModel positiveSeed positiveTarget ∧
      RepresentationPreservingIrreducible
        noDependencyModel positiveSeed positiveTarget (Fin 2)
        (fun _ _ => True)) ∧
    (¬ causallyDerivable toyConstraintModel negativeSeed negativeTarget ∧
      ¬ RepresentationPreservingIrreducible
        toyConstraintModel negativeSeed negativeTarget
        (ExtensionPoint negativeSeed negativeTarget) negativeOldGeneration) ∧
    ConstitutiveJointEmergence twoRootJointPremise 0 1 2 := by
  exact ⟨⟨positive_target_not_causally_derivable,
      positive_witness_is_representation_preserving_irreducible⟩,
    ⟨negative_target_not_causally_derivable,
      negative_witness_is_not_irreducible⟩,
    twoRoot_constitutive_joint_emergence⟩

end NativeIrreducibilityBoundary

end OCKIndividuationMSpaceComposition
