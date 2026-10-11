import OCKIndividuationMSpaceComposition.SymmetryNativeIrreducibilityBoundary
import OCKIndividuationMSpaceComposition.SymmetryJointCompositionBoundary
import Mathlib.Data.Fin.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uMechanism uIntervention uOutcome uOld

namespace NativeForcedExtensionBoundary

open ActiveConstraintModel
open JointCompositionBoundary
open NativeIrreducibilityBoundary

variable {Mechanism : Type uMechanism} [DecidableEq Mechanism]
variable {Intervention : Type uIntervention} {Outcome : Type uOutcome}

/-!
# Native closure/composition boundary for forced extension

This slice is the G3 boundary after the representation-preserving G2
criterion.  It does not add another rank or presentation bridge.  It records
which closure laws are genuinely supplied by the current OC relations, and
which laws fail for explicit finite countermodels.

The causal relation `familyGenerated` has closure-like laws, but its exact
singleton decomposition rules out genuine joint generation.  A separately
supplied joint-composition relation can have a genuine pair-only target and
even an extensive, monotone, idempotent finite closure, while exchange still
fails.  A bare pair rule does not even force extensivity.  Thus a forced
extension theorem requires its closure/composition premises explicitly.
-/

def FinsetClosureExtensive
    {Token : Type uMechanism} [DecidableEq Token]
    (close : Finset Token → Finset Token) : Prop :=
  ∀ seed : Finset Token, seed ⊆ close seed

def FinsetClosureMonotone
    {Token : Type uMechanism} [DecidableEq Token]
    (close : Finset Token → Finset Token) : Prop :=
  ∀ {first second : Finset Token}, first ⊆ second →
    close first ⊆ close second

def FinsetClosureIdempotent
    {Token : Type uMechanism} [DecidableEq Token]
    (close : Finset Token → Finset Token) : Prop :=
  ∀ seed : Finset Token, close (close seed) = close seed

def JointGeneratedExtensive
    {Token : Type uMechanism} [DecidableEq Token]
    (premise : JointClosurePremise Token) : Prop :=
  ∀ (seed : Finset Token) (target : Token),
    target ∈ seed → premise.jointGenerated seed target

/-! ## Existing causal generation: laws and exact no-go -/

theorem causal_family_generation_closure_boundary
    (model : ActiveConstraintModel Mechanism Intervention Outcome) :
    (∀ {seed : Set Mechanism} {root : Mechanism},
      root ∈ seed → familyGenerated model seed root) ∧
    (∀ {first second : Set Mechanism} {target : Mechanism},
      first ⊆ second → familyGenerated model first target →
        familyGenerated model second target) ∧
    (∀ (seed : Set Mechanism) (target : Mechanism),
      (∃ middle,
        familyGenerated model seed middle ∧
          familyGenerated model ({middle} : Set Mechanism) target) ↔
        familyGenerated model seed target) ∧
    (¬ ∃ (seed : Finset Mechanism) (target : Mechanism),
      JointlyGeneratedBy model seed target) := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro seed root root_member
    exact familyGenerated_extensive model root_member
  · intro first second target subset generated
    exact familyGenerated_mono model subset generated
  · intro seed target
    exact familyGenerated_idempotent model seed target
  · exact familyGenerated_has_no_genuine_joint_generator model

/-! ## A genuine joint closure with a failed exchange law -/

theorem twoRoot_joint_closure_boundary :
    FinsetClosureExtensive twoRootClosure ∧
    FinsetClosureMonotone twoRootClosure ∧
    FinsetClosureIdempotent twoRootClosure ∧
    twoRootJointPremise.jointGenerated
      ({0, 1} : Finset TwoRootToken) 2 ∧
    ¬ ExchangeLaw twoRootClosure := by
  exact ⟨twoRootClosure_extensive, twoRootClosure_monotone,
    twoRootClosure_idempotent, twoRoot_target_is_joint,
    twoRootClosure_fails_exchange⟩

/-! ## Pair composition alone does not force closure -/

def pairOnlyComposition : JointComposition (Fin 2) where
  combine := fun _ _ => 0

def pairOnlyPremise : JointClosurePremise (Fin 2) where
  composition := pairOnlyComposition
  jointGenerated := fun seed target =>
    ∃ first second : Fin 2,
      seed = ({first, second} : Finset (Fin 2)) ∧ target = 0
  pair_rule := by
    intro first second
    exact ⟨first, second, rfl, rfl⟩

theorem pair_rule_does_not_entail_extensivity :
    (∀ (first second : Fin 2),
      pairOnlyPremise.jointGenerated
        ({first, second} : Finset (Fin 2))
        (pairOnlyPremise.composition.combine first second)) ∧
    ¬ JointGeneratedExtensive pairOnlyPremise := by
  constructor
  · intro first second
    exact pairOnlyPremise.pair_rule first second
  · intro extensive
    have member_is_generated := extensive
      ({0, 1} : Finset (Fin 2)) (1 : Fin 2) (by simp)
    change (∃ first second : Fin 2,
      ({0, 1} : Finset (Fin 2)) = {first, second} ∧
        (1 : Fin 2) = 0) at member_is_generated
    rcases member_is_generated with ⟨first, second, _, target_eq⟩
    exact (by decide : (1 : Fin 2) ≠ 0) target_eq

/-! ## A finite forced-extension theorem -/

theorem positive_extension_forces_old_carrier_card_at_least_three
    {Old : Type uOld} [Fintype Old]
    (oldGeneration : Old → Old → Prop)
    (representation : FaithfulOldRepresentation
      noDependencyModel positiveSeed positiveTarget Old oldGeneration) :
    3 ≤ Fintype.card Old := by
  have card_bound :
      Fintype.card (ExtensionPoint positiveSeed positiveTarget) ≤
        Fintype.card Old :=
    Fintype.card_le_of_injective representation.encode representation.injective
  rw [positive_extension_card] at card_bound
  exact card_bound

theorem positive_extension_forces_new_capacity_at_old_two_point_bound
    {Old : Type uOld} [Fintype Old]
    (oldGeneration : Old → Old → Prop)
    (oldCard : Fintype.card Old ≤ 2) :
    RepresentationPreservingIrreducible
      noDependencyModel positiveSeed positiveTarget Old oldGeneration := by
  intro representation
  rcases representation with ⟨representation⟩
  have lower := positive_extension_forces_old_carrier_card_at_least_three
    oldGeneration representation
  omega

/-! The finite forced-extension result is deliberately conditional: it is a
capacity obstruction for one explicit OC-native witness, not a generic rank
or dimension theorem. -/

theorem g3_forced_extension_boundary :
    (¬ causallyDerivable noDependencyModel positiveSeed positiveTarget ∧
      RepresentationPreservingIrreducible
        noDependencyModel positiveSeed positiveTarget (Fin 2)
        (fun _ _ => True)) ∧
    (¬ causallyDerivable toyConstraintModel negativeSeed negativeTarget ∧
      ¬ RepresentationPreservingIrreducible
        toyConstraintModel negativeSeed negativeTarget
        (ExtensionPoint negativeSeed negativeTarget) negativeOldGeneration) ∧
    ConstitutiveJointEmergence twoRootJointPremise 0 1 2 ∧
    ¬ JointGeneratedExtensive pairOnlyPremise := by
  exact ⟨
    ⟨positive_target_not_causally_derivable,
      positive_witness_is_representation_preserving_irreducible⟩,
    ⟨negative_target_not_causally_derivable,
      negative_witness_is_not_irreducible⟩,
    twoRoot_constitutive_joint_emergence,
    pair_rule_does_not_entail_extensivity.2⟩

end NativeForcedExtensionBoundary

end OCKIndividuationMSpaceComposition
