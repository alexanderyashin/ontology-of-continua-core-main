import OCKIndividuationMSpaceComposition.TypedContinuationEffectTransport
import OCKIndividuationMSpaceComposition.TypedCausalContinuationTransport

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uA uB uCausalContext

/-!
# Boundary between transition weights and signed causal effects

A stochastic transition mass and a causal contrast are not the same kind of
number.  Transition masses are nonnegative and their positive locus is a
support relation.  Conditional causal effects are signed fields; a negative
effect is not an impossible transition.  This module makes the type split
explicit and proves the exact adapter from the existing static causal
transport contract.
-/

/-- A signed effect indexed by a context.  No support, normalization or causal
identification claim is hidden in this data type. -/
structure SignedEffectField (Index : Type uA) where
  value : Index → ℚ

/-- Exact change of index for a signed effect field. -/
structure ExactSignedEffectTransport
    {SourceIndex : Type uA} {TargetIndex : Type uB}
    (source : SignedEffectField SourceIndex)
    (target : SignedEffectField TargetIndex) where
  indexMap : SourceIndex → TargetIndex
  preserves_value : ∀ index,
    target.value (indexMap index) = source.value index

namespace ExactSignedEffectTransport

def identity
    {Index : Type uA}
    (effect : SignedEffectField Index) :
    ExactSignedEffectTransport effect effect where
  indexMap := id
  preserves_value := by intro _; rfl

def comp
    {IndexA : Type uA} {IndexB : Type uB} {IndexC : Type uCausalContext}
    {effectA : SignedEffectField IndexA}
    {effectB : SignedEffectField IndexB}
    {effectC : SignedEffectField IndexC}
    (first : ExactSignedEffectTransport effectA effectB)
    (second : ExactSignedEffectTransport effectB effectC) :
    ExactSignedEffectTransport effectA effectC where
  indexMap := second.indexMap ∘ first.indexMap
  preserves_value := by
    intro index
    exact (second.preserves_value (first.indexMap index)).trans
      (first.preserves_value index)

theorem comp_map_assoc
    {IndexA : Type uA} {IndexB : Type uB} {IndexC : Type uCausalContext}
    {effectA : SignedEffectField IndexA}
    {effectB : SignedEffectField IndexB}
    {effectC effectD : SignedEffectField IndexC}
    (first : ExactSignedEffectTransport effectA effectB)
    (second : ExactSignedEffectTransport effectB effectC)
    (third : ExactSignedEffectTransport effectC effectD)
    (index : IndexA) :
    ((first.comp second).comp third).indexMap index =
      (first.comp (second.comp third)).indexMap index :=
  rfl

end ExactSignedEffectTransport

/-- The source conditional-effect field of a static causal contract. -/
def StaticEffectTransportContract.sourceSignedEffect
    {Context : Type uCausalContext} [Fintype Context]
    (contract : StaticEffectTransportContract Context) :
    SignedEffectField Context :=
  ⟨contract.sourceEffect⟩

/-- The target conditional-effect field of a static causal contract. -/
def StaticEffectTransportContract.targetSignedEffect
    {Context : Type uCausalContext} [Fintype Context]
    (contract : StaticEffectTransportContract Context) :
    SignedEffectField Context :=
  ⟨contract.targetEffect⟩

/-- Conditional-effect stability is exactly an identity-index signed-effect
transport.  Population weights and overlap remain separate fields of the
causal contract. -/
def StaticEffectTransportContract.toExactSignedEffectTransport
    {Context : Type uCausalContext} [Fintype Context]
    (contract : StaticEffectTransportContract Context) :
    ExactSignedEffectTransport contract.sourceSignedEffect
      contract.targetSignedEffect where
  indexMap := id
  preserves_value := contract.conditionalEffectStable

/-- The existing OC typed causal certificate projects to the signed-effect
adapter without losing its continuation component. -/
theorem typed_causal_transport_certifies_continuation_and_signed_effect
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (certificate : TypedExactCausalContinuationTransport source target CausalContext)
    {initial endpoint : State}
    (witness : ContinuationWitness source initial endpoint)
    (context : CausalContext) :
    Continues target initial endpoint ∧
      certificate.causal.targetSignedEffect.value context =
        certificate.causal.sourceSignedEffect.value context := by
  exact ⟨⟨certificate.continuation.transport initial endpoint witness⟩,
    certificate.causal.conditionalEffectStable context⟩

/-- A signed field can be retained in the quantitative channel of the common
interface.  Its support is only the positive locus; it must not be read as a
reachability relation for signed causal effects. -/
def SignedEffectField.toPositiveLocusInterface
    {Index : Type uA}
    (effect : SignedEffectField Index) :
    TypedEffectInterface Index Unit where
  support := fun index _ => 0 < effect.value index
  quantitative := some (fun index _ => effect.value index)
  quantitative_support_exact := by
    intro weights sameWeights index target
    cases target
    have valueEq : (fun index : Index => fun _ : Unit => effect.value index) = weights :=
      Option.some.inj sameWeights
    rw [← valueEq]

private def negativeSignedEffect : SignedEffectField Unit :=
  ⟨fun _ => -1⟩

/-- A negative causal effect is quantitatively present but absent from the
positive-locus support.  Therefore that support cannot mean causal relevance
or physical possibility. -/
theorem negative_signed_effect_is_retained_but_not_supported :
    negativeSignedEffect.toPositiveLocusInterface.quantitative =
        some (fun _ _ => (-1 : ℚ)) ∧
      ¬ negativeSignedEffect.toPositiveLocusInterface.support () () := by
  constructor
  · rfl
  · norm_num [SignedEffectField.toPositiveLocusInterface, negativeSignedEffect]

/-- No stochastic transition kernel can encode a negative causal effect as a
probability mass. -/
theorem negative_causal_effect_is_not_stochastic_mass :
    ¬ ∃ effect : FiniteStochasticEffect Unit Unit,
      effect.mass () () = (-1 : ℚ) := by
  rintro ⟨effect, negativeMass⟩
  have nonnegative := effect.nonnegative () ()
  rw [negativeMass] at nonnegative
  norm_num at nonnegative

private def relabeledSourceEffect : SignedEffectField Bool :=
  ⟨fun context => if context then 1 else 0⟩

private def relabeledTargetEffect : SignedEffectField Bool :=
  ⟨fun context => if context then 0 else 1⟩

private def relabeledSignedTransport :
    ExactSignedEffectTransport relabeledSourceEffect relabeledTargetEffect where
  indexMap := Bool.not
  preserves_value := by
    intro context
    cases context <;>
      norm_num [relabeledSourceEffect, relabeledTargetEffect]

/-- Exact signed-effect transport under a relabeling does not imply the
pointwise conditional-effect stability required by the static causal
standardization contract.  An explicit context matching law is indispensable. -/
theorem relabeled_signed_transport_does_not_imply_pointwise_causal_stability :
    Nonempty (ExactSignedEffectTransport
      relabeledSourceEffect relabeledTargetEffect) ∧
      ¬ ∀ context,
        relabeledTargetEffect.value context = relabeledSourceEffect.value context := by
  constructor
  · exact ⟨relabeledSignedTransport⟩
  · intro stable
    have falseStable := stable false
    norm_num [relabeledSourceEffect, relabeledTargetEffect] at falseStable

end OCKIndividuationMSpaceComposition
