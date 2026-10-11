import OCKIndividuationMSpaceComposition.SymmetryNativeCausalFamilyClosure
import OCKIndividuationMSpaceComposition.SymmetryIntrinsicFinitaryRank
import Mathlib.Data.Fin.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uMechanism

namespace JointCompositionBoundary

/-!
# Joint composition is an additional closure premise

The current `ActiveConstraintModel.familyGenerated` is a union of singleton
`GeneratedKernel`s.  Its existing boundary theorem therefore correctly rules
out a genuinely joint target.  This file keeps that result intact and adds a
separate, explicit premise for a future multi-root composition law.

`JointClosurePremise` does not redefine `familyGenerated` and does not claim
exchange, idempotence, rank, or any other closure law.  It only says how an
explicit binary composition witness is admitted into a separately supplied
joint-generation relation.  The concrete finite model at the end has ordinary
extensive, monotone and idempotent closure, a genuine two-root target, and no
exchange law.  Thus a joint witness alone cannot be promoted to intrinsic rank.
-/

/-! ## Existing singleton boundary -/

theorem singleton_family_generation_forbids_genuine_joint
    {Mechanism : Type uMechanism} {Intervention : Type uMechanism}
    {Outcome : Type uMechanism}
    (model : ActiveConstraintModel Mechanism Intervention Outcome) :
    ¬ ∃ (seed : Finset Mechanism) (target : Mechanism),
      ActiveConstraintModel.JointlyGeneratedBy model seed target := by
  exact ActiveConstraintModel.familyGenerated_has_no_genuine_joint_generator
    model

/-! ## Explicit joint-composition premise -/

/-- A binary composition operation is supplied as a premise, not inferred
from singleton causal generation.  No algebraic law is built into this
interface. -/
structure JointComposition (Mechanism : Type uMechanism) where
  combine : Mechanism → Mechanism → Mechanism

/-- A separately supplied joint-generation relation admits the result of the
binary composition operation on a two-root seed.  This is the only closure
premise used below; exchange and rank are intentionally absent. -/
structure JointClosurePremise (Mechanism : Type uMechanism)
    [DecidableEq Mechanism] where
  composition : JointComposition Mechanism
  jointGenerated : Finset Mechanism → Mechanism → Prop
  pair_rule : ∀ (first second : Mechanism),
    jointGenerated ({first, second} : Finset Mechanism)
      (composition.combine first second)

/-- An explicit witness identifies the target of the supplied binary
composition. -/
structure JointCompositionWitness
    {Mechanism : Type uMechanism} [DecidableEq Mechanism]
    (premise : JointClosurePremise Mechanism)
    (first second target : Mechanism) where
  target_eq : premise.composition.combine first second = target

theorem target_jointGenerated_of_two_roots
    {Mechanism : Type uMechanism} [DecidableEq Mechanism]
    (premise : JointClosurePremise Mechanism)
    {first second target : Mechanism}
    (witness : JointCompositionWitness premise first second target) :
    premise.jointGenerated ({first, second} : Finset Mechanism) target := by
  rw [← witness.target_eq]
  exact premise.pair_rule first second

/-! ## What the premise does not imply -/

/-- Exchange is a separate property of a finite closure relation. -/
def ExchangeLaw {Token : Type uMechanism} [DecidableEq Token]
    (close : Finset Token → Finset Token) : Prop :=
  ∀ (seed : Finset Token) (first second : Token),
    first ∈ close (insert second seed) →
    first ∉ close seed →
    second ∈ close (insert first seed)

/-- Independence and maximality for an ordinary finite closure.  These are
deliberately not identified with `FinitaryDistinctionClosure`, whose interface
already requires exchange. -/
def OrdinaryIndependent {Token : Type uMechanism} [DecidableEq Token]
    (close : Finset Token → Finset Token) (family : Finset Token) : Prop :=
  ∀ token ∈ family, token ∉ close (family.erase token)

def OrdinaryMaximalIndependent {Token : Type uMechanism} [DecidableEq Token]
    (close : Finset Token → Finset Token) (family : Finset Token) : Prop :=
  OrdinaryIndependent close family ∧
    ∀ token ∉ family,
      ¬ OrdinaryIndependent close (insert token family)

/-! ## A concrete two-root countermodel -/

abbrev TwoRootToken := Fin 4

/-- Roots `0` and `1` jointly generate `2`; root `0` alone also adds an
independent witness `3`.  This asymmetry creates unequal maximal-independent
families while preserving a genuine two-root target for `2`. -/
def twoRootClosure (seed : Finset TwoRootToken) : Finset TwoRootToken :=
  if (0 : TwoRootToken) ∈ seed then
    if (1 : TwoRootToken) ∈ seed then Finset.univ else insert 3 seed
  else seed

theorem twoRootClosure_extensive :
    ∀ seed : Finset TwoRootToken, seed ⊆ twoRootClosure seed := by
  intro seed
  by_cases hasZero : (0 : TwoRootToken) ∈ seed
  · by_cases hasOne : (1 : TwoRootToken) ∈ seed
    · simp [twoRootClosure, hasZero, hasOne]
    · intro token tokenMember
      simp [twoRootClosure, hasZero, hasOne, tokenMember]
  · intro token tokenMember
    simp [twoRootClosure, hasZero, tokenMember]

theorem twoRootClosure_monotone :
    ∀ {first second : Finset TwoRootToken}, first ⊆ second →
      twoRootClosure first ⊆ twoRootClosure second := by
  intro first second subset
  by_cases firstHasZero : (0 : TwoRootToken) ∈ first
  · have secondHasZero : (0 : TwoRootToken) ∈ second := subset firstHasZero
    by_cases firstHasOne : (1 : TwoRootToken) ∈ first
    · have secondHasOne : (1 : TwoRootToken) ∈ second := subset firstHasOne
      simp [twoRootClosure, firstHasZero, firstHasOne,
        secondHasZero, secondHasOne]
    · by_cases secondHasOne : (1 : TwoRootToken) ∈ second
      · simp [twoRootClosure, firstHasZero, firstHasOne,
          secondHasZero, secondHasOne]
      · intro token tokenMember
        have tokenMember' : token = 3 ∨ token ∈ first := by
          simpa [twoRootClosure, firstHasZero, firstHasOne] using tokenMember
        have inserted : token ∈ insert (3 : TwoRootToken) second := by
          rcases tokenMember' with rfl | tokenInFirst
          · simp
          · exact Finset.mem_insert_of_mem (subset tokenInFirst)
        simpa [twoRootClosure, secondHasZero, secondHasOne] using inserted
  · by_cases secondHasZero : (0 : TwoRootToken) ∈ second
    · by_cases secondHasOne : (1 : TwoRootToken) ∈ second
      · simp [twoRootClosure, firstHasZero, secondHasZero, secondHasOne]
      · intro token tokenMember
        have tokenInFirst : token ∈ first := by
          simpa [twoRootClosure, firstHasZero] using tokenMember
        have tokenInSecond : token ∈ second := subset tokenInFirst
        have inserted : token ∈ insert (3 : TwoRootToken) second :=
          Finset.mem_insert_of_mem tokenInSecond
        simpa [twoRootClosure, secondHasZero, secondHasOne] using inserted
    · simpa [twoRootClosure, firstHasZero, secondHasZero] using subset

theorem twoRootClosure_idempotent :
    ∀ seed : Finset TwoRootToken,
      twoRootClosure (twoRootClosure seed) = twoRootClosure seed := by
  intro seed
  by_cases hasZero : (0 : TwoRootToken) ∈ seed
  · by_cases hasOne : (1 : TwoRootToken) ∈ seed
    · simp [twoRootClosure, hasZero, hasOne]
    · simp [twoRootClosure, hasZero, hasOne]
  · simp [twoRootClosure, hasZero]

def twoRootComposition : JointComposition TwoRootToken where
  combine := fun first second =>
    if (first = 0 ∧ second = 1) ∨ (first = 1 ∧ second = 0) then 2 else first

def twoRootJointPremise : JointClosurePremise TwoRootToken where
  composition := twoRootComposition
  jointGenerated := fun seed target => target ∈ twoRootClosure seed
  pair_rule := by
    intro first second
    fin_cases first <;> fin_cases second <;>
      simp [twoRootComposition, twoRootClosure]

def twoRootWitness :
    JointCompositionWitness twoRootJointPremise 0 1 2 where
  target_eq := by decide

theorem twoRoot_target_is_joint :
    twoRootJointPremise.jointGenerated ({0, 1} : Finset TwoRootToken) 2 := by
  exact target_jointGenerated_of_two_roots twoRootJointPremise twoRootWitness

theorem twoRoot_target_not_singleton_generated :
    2 ∉ twoRootClosure ({0} : Finset TwoRootToken) ∧
      2 ∉ twoRootClosure ({1} : Finset TwoRootToken) := by
  simp [twoRootClosure]

theorem twoRootClosure_fails_exchange :
    ¬ ExchangeLaw twoRootClosure := by
  intro exchange
  have generated : (2 : TwoRootToken) ∈
      twoRootClosure (insert (1 : TwoRootToken) ({0} : Finset TwoRootToken)) := by
    simp [twoRootClosure]
  have new : (2 : TwoRootToken) ∉ twoRootClosure ({0} : Finset TwoRootToken) := by
    simp [twoRootClosure]
  have conclusion := exchange ({0} : Finset TwoRootToken) 2 1 generated new
  simpa [twoRootClosure] using conclusion

theorem twoRoot_maximal_independent_first :
    OrdinaryMaximalIndependent twoRootClosure ({0, 2} : Finset TwoRootToken) := by
  constructor
  · intro token tokenMember
    fin_cases token <;> simp [twoRootClosure] at tokenMember ⊢
  · intro token tokenNotMember
    fin_cases token
    · simp at tokenNotMember
    · intro independent
      have bad := independent (2 : TwoRootToken) (by simp)
      simpa [twoRootClosure] using bad
    · simp at tokenNotMember
    · intro independent
      have bad := independent (3 : TwoRootToken) (by simp)
      simpa [twoRootClosure] using bad

theorem twoRoot_maximal_independent_second :
    OrdinaryMaximalIndependent twoRootClosure ({1, 2, 3} : Finset TwoRootToken) := by
  constructor
  · intro token tokenMember
    fin_cases token <;> simp [twoRootClosure] at tokenMember ⊢
  · intro token tokenNotMember
    fin_cases token
    · intro independent
      have bad := independent (2 : TwoRootToken) (by simp)
      simpa [twoRootClosure] using bad
    · simp at tokenNotMember
    · simp at tokenNotMember
    · simp at tokenNotMember

theorem twoRoot_maximal_independent_cardinals_differ :
    ({0, 2} : Finset TwoRootToken).card ≠
      ({1, 2, 3} : Finset TwoRootToken).card := by
  decide

/-! The countermodel is a complete boundary witness: joint generation is
present, the ordinary closure laws hold, but exchange and unique maximal
independent cardinality do not follow. -/
theorem twoRoot_countermodel_boundary :
    (∀ seed : Finset TwoRootToken, seed ⊆ twoRootClosure seed) ∧
    (∀ {first second : Finset TwoRootToken}, first ⊆ second →
      twoRootClosure first ⊆ twoRootClosure second) ∧
    (∀ seed : Finset TwoRootToken,
      twoRootClosure (twoRootClosure seed) = twoRootClosure seed) ∧
    twoRootJointPremise.jointGenerated ({0, 1} : Finset TwoRootToken) 2 ∧
    ¬ ExchangeLaw twoRootClosure ∧
    ({0, 2} : Finset TwoRootToken).card ≠
      ({1, 2, 3} : Finset TwoRootToken).card := by
  exact ⟨twoRootClosure_extensive, twoRootClosure_monotone,
    twoRootClosure_idempotent, twoRoot_target_is_joint,
    twoRootClosure_fails_exchange,
    twoRoot_maximal_independent_cardinals_differ⟩

end JointCompositionBoundary

end OCKIndividuationMSpaceComposition
