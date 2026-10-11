import OCKIndividuationMSpaceComposition.PathDependentSequentialIntervention

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uCausalContext

/-!
# One-contract composition of continuation, sequential intervention and effect transport

The preceding modules establish two necessary facts separately: a finite
sequential intervention may be identified along an OC continuation path, and a
causal effect may be transported only with a typed continuation contract.  This
module makes their shared dependency explicit.  The effect certificate and the
path-aligned sequential certificate must use *the same* horizon-preserving
context transport; a numerically sound effect bound cannot be paired with an
unrelated referent transport.
-/

/--
A finite sequential intervention and a robust causal-effect transport coupled
through one exact horizon-preserving continuation transport.
-/
structure PathAlignedSequentialCausalTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (CausalContext : Type uCausalContext) [Fintype CausalContext]
    (initial endpoint : State) (horizon : Nat) where
  compatibility : HorizonPreservingContextCompatibility source target
  sequential : PathDependentSequentialIntervention source initial endpoint horizon
  causal : TypedRobustCausalContinuationTransport source target CausalContext
  causalUsesSameCompatibility : causal.continuation = compatibility.context

/--
The path transported by the causal certificate is exactly the path whose
horizon is certified by the sequential intervention contract.
-/
theorem path_aligned_causal_transport_preserves_sequential_horizon
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State} {horizon : Nat}
    (certificate : PathAlignedSequentialCausalTransport source target CausalContext
      initial endpoint horizon) :
    (certificate.causal.continuation.transport initial endpoint
      certificate.sequential.continuation).history.length = horizon := by
  rw [certificate.causalUsesSameCompatibility]
  exact (certificate.compatibility.lengthPreserved initial endpoint
    certificate.sequential.continuation).trans certificate.sequential.horizonAligned

/--
Positive composition theorem: one shared contract certifies target referent
continuation, intervention-horizon preservation, sequential identification,
and the causal-effect transport error bound.
-/
theorem path_aligned_sequential_causal_transport_is_sound
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State} {horizon : Nat}
    (certificate : PathAlignedSequentialCausalTransport source target CausalContext
      initial endpoint horizon) :
    Continues target initial endpoint ∧
      (certificate.causal.continuation.transport initial endpoint
        certificate.sequential.continuation).history.length = horizon ∧
      sequentialRegimeValue certificate.sequential.identification.identifiedStageEffect =
        sequentialRegimeValue certificate.sequential.identification.latentStageEffect ∧
      |domainAverageEffect certificate.causal.targetWeight certificate.causal.targetEffect -
        domainAverageEffect certificate.causal.sourceWeight certificate.causal.sourceEffect| ≤
        certificate.causal.mechanismDriftRadius + certificate.causal.effectMagnitudeBound *
          ∑ context,
            |certificate.causal.targetWeight context - certificate.causal.sourceWeight context| := by
  refine ⟨⟨certificate.causal.continuation.transport initial endpoint
    certificate.sequential.continuation⟩, ?_, ?_, ?_⟩
  · exact path_aligned_causal_transport_preserves_sequential_horizon certificate
  · exact sequential_g_contract_identifies_regime_value certificate.sequential.identification
  · exact (typed_robust_transport_certifies_continuation_and_effect_bound
      certificate.causal certificate.sequential.continuation).2

/--
No scalar causal bound can bypass a target continuation obstruction: the shared
transport contract would itself construct the forbidden target witness.
-/
theorem target_continuation_obstruction_blocks_path_aligned_sequential_causal_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State} {horizon : Nat}
    (targetObstruction : ¬ Continues target initial endpoint) :
    ¬ Nonempty (PathAlignedSequentialCausalTransport source target CausalContext
      initial endpoint horizon) := by
  rintro ⟨certificate⟩
  apply targetObstruction
  exact ⟨certificate.causal.continuation.transport initial endpoint
    certificate.sequential.continuation⟩

end OCKIndividuationMSpaceComposition
