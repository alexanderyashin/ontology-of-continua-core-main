import OCKIndividuationMSpaceComposition.CausalAdmissionContract

namespace OCKIndividuationMSpaceComposition

/-!
# OC14-OB-MATH-03: typed causal identity adapter

This slice fixes the weakest exact interface for the causal-identity gap.  A
source identity predicate, a target identity predicate, a typed map, an
explicit P1-P7 admission witness, and an effect relation are separate fields.
The forward theorem is available only from the adapter's declared witness.
The converse is a separate reflection/faithfulness field, and the Boolean
countermodel below shows that it cannot be inferred from admission alone.
-/

universe uSource uTarget

/-- A typed source-to-target identity adapter with explicit causal admission. -/
structure CausalIdentityAdapter
    (SourceState : Type uSource) (TargetState : Type uTarget) where
  encode : SourceState → TargetState
  sourceIdentity : SourceState → SourceState → Prop
  targetIdentity : TargetState → TargetState → Prop
  premises : CausalAdmissionPremises
  admission : TransportedCausalAdmission premises
  effectRelation : SourceState → TargetState → Prop
  identityPreserved : ∀ {sourceLeft sourceRight},
    sourceIdentity sourceLeft sourceRight →
      targetIdentity (encode sourceLeft) (encode sourceRight)
  effectTransported : ∀ source, effectRelation source (encode source)

/-/ The P1-P7 witness is directly recoverable from an admitted adapter. -/
theorem causalIdentityAdapter_is_admitted
    {SourceState : Type uSource} {TargetState : Type uTarget}
    (adapter : CausalIdentityAdapter SourceState TargetState) :
    TransportedCausalAdmission adapter.premises :=
  adapter.admission

/-/ Forward identity preservation and effect transport are one typed result. -/
theorem causalIdentityAdapter_preserves_identity_and_effect
    {SourceState : Type uSource} {TargetState : Type uTarget}
    (adapter : CausalIdentityAdapter SourceState TargetState)
    {sourceLeft sourceRight : SourceState}
    (identity : adapter.sourceIdentity sourceLeft sourceRight) :
    adapter.targetIdentity (adapter.encode sourceLeft)
        (adapter.encode sourceRight) ∧
      adapter.effectRelation sourceLeft (adapter.encode sourceLeft) := by
  exact ⟨adapter.identityPreserved identity,
    adapter.effectTransported sourceLeft⟩

/-- The converse requires an explicit reflection/faithfulness contract. -/
structure FaithfulCausalIdentityAdapter
    (SourceState : Type uSource) (TargetState : Type uTarget)
    extends CausalIdentityAdapter SourceState TargetState where
  identityReflected : ∀ {sourceLeft sourceRight},
    targetIdentity (encode sourceLeft) (encode sourceRight) →
      sourceIdentity sourceLeft sourceRight

theorem faithfulCausalIdentityAdapter_reflects_identity
    {SourceState : Type uSource} {TargetState : Type uTarget}
    (adapter : FaithfulCausalIdentityAdapter SourceState TargetState)
    {sourceLeft sourceRight : SourceState}
    (identity : adapter.targetIdentity (adapter.encode sourceLeft)
        (adapter.encode sourceRight)) :
    adapter.sourceIdentity sourceLeft sourceRight :=
  adapter.identityReflected identity

/-! A concrete countermodel: every source is encoded as `false`, while the
target identity predicate is universal.  All seven premises are `True`, so
causal admission is present, but target identity cannot reflect source
identity. -/

def allTrueCausalPremises : CausalAdmissionPremises where
  intervention := True
  consistency := True
  exchangeability := True
  positivity := True
  selection := True
  measurement := True
  transport := True

theorem allTrueCausalPremises_admitted :
    TransportedCausalAdmission allTrueCausalPremises := by
  change (True ∧ True ∧ True ∧ True ∧ True ∧ True) ∧ True
  exact ⟨⟨True.intro, True.intro, True.intro, True.intro, True.intro,
    True.intro⟩, True.intro⟩

def constantBooleanCausalIdentityAdapter :
    CausalIdentityAdapter Bool Bool where
  encode := fun _ => false
  sourceIdentity := Eq
  targetIdentity := fun _ _ => True
  premises := allTrueCausalPremises
  admission := allTrueCausalPremises_admitted
  effectRelation := fun _ _ => True
  identityPreserved := by
    intro sourceLeft sourceRight _
    exact True.intro
  effectTransported := by
    intro source
    exact True.intro

structure CausalIdentityCountermodel where
  adapter : CausalIdentityAdapter Bool Bool
  sourceHasDistinctStates : ∃ left right : Bool, left ≠ right
  targetIdentityCollapsesImage : ∀ left right : Bool,
    adapter.targetIdentity (adapter.encode left) (adapter.encode right)
  identityReflectionFails : ¬ (∀ left right : Bool,
    adapter.targetIdentity (adapter.encode left) (adapter.encode right) →
      adapter.sourceIdentity left right)

def constantBooleanCausalIdentityCountermodel : CausalIdentityCountermodel where
  adapter := constantBooleanCausalIdentityAdapter
  sourceHasDistinctStates := ⟨false, true, by decide⟩
  targetIdentityCollapsesImage := by
    intro left right
    exact True.intro
  identityReflectionFails := by
    intro reflected
    exact (by decide : (false : Bool) ≠ true)
      (reflected false true True.intro)

theorem admitted_causal_identity_need_not_reflect_source_identity :
    ¬ (∀ left right : Bool,
      constantBooleanCausalIdentityAdapter.targetIdentity
          (constantBooleanCausalIdentityAdapter.encode left)
          (constantBooleanCausalIdentityAdapter.encode right) →
        constantBooleanCausalIdentityAdapter.sourceIdentity left right) :=
  constantBooleanCausalIdentityCountermodel.identityReflectionFails

end OCKIndividuationMSpaceComposition
