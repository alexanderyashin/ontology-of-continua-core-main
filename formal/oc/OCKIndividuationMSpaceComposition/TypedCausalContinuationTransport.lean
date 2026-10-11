import OCKIndividuationMSpaceComposition.QuantitativeContextTransport
import OCKIndividuationMSpaceComposition.CrossDomainEffectTransport

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uCausalContext

/-!
# Typed causal transport guarded by continuation validity

Effect transport and object continuation answer different questions.  This
module prevents a numerically transportable effect from being applied to an
untransportable referent: a certificate must carry both the causal population
contract and an explicit `ContextCompatibility` witness.
-/

/-- Exact causal transport whose referent path is valid in the target context. -/
structure TypedExactCausalContinuationTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (CausalContext : Type uCausalContext) [Fintype CausalContext] where
  continuation : ContextCompatibility source target
  causal : StaticEffectTransportContract CausalContext

/-- A typed exact certificate transports both the referent witness and target ATE. -/
theorem typed_exact_transport_certifies_continuation_and_effect
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (certificate : TypedExactCausalContinuationTransport source target CausalContext)
    {initial endpoint : State}
    (sourceWitness : ContinuationWitness source initial endpoint) :
    Continues target initial endpoint ∧
      reweightedSourceEffect certificate.causal.sourceWeight
          certificate.causal.targetWeight certificate.causal.sourceEffect =
        domainAverageEffect certificate.causal.targetWeight
          certificate.causal.targetEffect := by
  exact ⟨⟨certificate.continuation.transport initial endpoint sourceWitness⟩,
    positive_overlap_reweighting_exact certificate.causal⟩

/-- Frame mismatch blocks a typed certificate even if scalar effects coincide. -/
theorem frame_mismatch_blocks_typed_exact_causal_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (mismatch : source.frame ≠ target.frame) :
    ¬ Nonempty (TypedExactCausalContinuationTransport source target CausalContext) := by
  rintro ⟨certificate⟩
  exact mismatch certificate.continuation.frameCompatible

/-- A target continuation obstruction blocks typed effect transport. -/
theorem target_continuation_obstruction_blocks_typed_exact_causal_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State}
    (sourceWitness : Continues source initial endpoint)
    (targetObstruction : ¬ Continues target initial endpoint) :
    ¬ Nonempty (TypedExactCausalContinuationTransport source target CausalContext) := by
  rintro ⟨certificate⟩
  exact no_context_compatibility_of_counterexample sourceWitness targetObstruction
    certificate.continuation

/-- Robust typed certificate with separately auditable causal error budgets. -/
structure TypedRobustCausalContinuationTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (CausalContext : Type uCausalContext) [Fintype CausalContext] where
  continuation : ContextCompatibility source target
  sourceWeight : CausalContext → ℚ
  targetWeight : CausalContext → ℚ
  sourceEffect : CausalContext → ℚ
  targetEffect : CausalContext → ℚ
  mechanismDriftRadius : ℚ
  effectMagnitudeBound : ℚ
  targetWeightNonnegative : ∀ context, 0 ≤ targetWeight context
  targetWeightNormalized : ∑ context, targetWeight context = 1
  mechanismDriftBound : ∀ context,
    |targetEffect context - sourceEffect context| ≤ mechanismDriftRadius
  sourceEffectBounded : ∀ context,
    |sourceEffect context| ≤ effectMagnitudeBound

/-- The robust typed certificate jointly yields referent continuation and error bound. -/
theorem typed_robust_transport_certifies_continuation_and_effect_bound
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (certificate : TypedRobustCausalContinuationTransport source target CausalContext)
    {initial endpoint : State}
    (sourceWitness : ContinuationWitness source initial endpoint) :
    Continues target initial endpoint ∧
      |domainAverageEffect certificate.targetWeight certificate.targetEffect -
        domainAverageEffect certificate.sourceWeight certificate.sourceEffect| ≤
      certificate.mechanismDriftRadius + certificate.effectMagnitudeBound *
        ∑ context,
          |certificate.targetWeight context - certificate.sourceWeight context| := by
  exact ⟨⟨certificate.continuation.transport initial endpoint sourceWitness⟩,
    combined_cross_domain_transport_bound certificate.sourceWeight
      certificate.targetWeight certificate.sourceEffect certificate.targetEffect
      certificate.mechanismDriftRadius certificate.effectMagnitudeBound
      certificate.targetWeightNonnegative certificate.targetWeightNormalized
      certificate.mechanismDriftBound certificate.sourceEffectBounded⟩

/-- A scalar error certificate cannot launder a missing continuation witness. -/
theorem numerical_transport_bound_does_not_override_continuation_obstruction
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State}
    (sourceWitness : Continues source initial endpoint)
    (targetObstruction : ¬ Continues target initial endpoint) :
    ¬ Nonempty (TypedRobustCausalContinuationTransport source target CausalContext) := by
  rintro ⟨certificate⟩
  exact no_context_compatibility_of_counterexample sourceWitness targetObstruction
    certificate.continuation

end OCKIndividuationMSpaceComposition
