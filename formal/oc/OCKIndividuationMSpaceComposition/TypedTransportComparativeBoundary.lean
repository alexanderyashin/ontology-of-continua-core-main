import OCKIndividuationMSpaceComposition.TypedCausalContinuationTransport
import OCKIndividuationMSpaceComposition.OCContextAndContinuumBridge

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uCausalContext

/-!
# Comparative boundary for typed causal-continuation transport

The typed static certificate is not a replacement for graphical causal
transport or provenance.  It is exactly an adapter pairing a mature causal
transport contract with OC context compatibility.  The projection theorems
below make reuse explicit; strictness comes from the fact that the causal
projection can remain inhabited across a frame mismatch while the typed
certificate cannot.
-/

/-- Project the mature causal-effect transport component. -/
def TypedExactCausalContinuationTransport.toCausalContract
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (certificate : TypedExactCausalContinuationTransport source target CausalContext) :
    StaticEffectTransportContract CausalContext := certificate.causal

/-- Project the OC continuation/context component. -/
def TypedExactCausalContinuationTransport.toContextCompatibility
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (certificate : TypedExactCausalContinuationTransport source target CausalContext) :
    ContextCompatibility source target := certificate.continuation

/-- The adapter introduces no hidden third assumption: its two projections suffice. -/
theorem typed_exact_transport_exists_iff_components_exist
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext] :
    Nonempty (TypedExactCausalContinuationTransport source target CausalContext) ↔
      Nonempty (ContextCompatibility source target) ∧
        Nonempty (StaticEffectTransportContract CausalContext) := by
  constructor
  · rintro ⟨certificate⟩
    exact ⟨⟨certificate.continuation⟩, ⟨certificate.causal⟩⟩
  · rintro ⟨⟨continuation⟩, ⟨causal⟩⟩
    exact ⟨⟨continuation, causal⟩⟩

/--
Strict-difference boundary: a causal transport contract alone may survive a
frame mismatch, but the OC-typed adapter is then impossible.
-/
theorem causal_transport_alone_is_strictly_weaker_at_frame_mismatch
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (causal : StaticEffectTransportContract CausalContext)
    (frameMismatch : source.frame ≠ target.frame) :
    Nonempty (StaticEffectTransportContract CausalContext) ∧
      ¬ Nonempty (TypedExactCausalContinuationTransport source target CausalContext) := by
  exact ⟨⟨causal⟩,
    frame_mismatch_blocks_typed_exact_causal_transport frameMismatch⟩

/-- Successful typed application projects to target-side provenance lineage. -/
theorem typed_exact_transport_application_has_target_lineage
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
    LineageGenerated
      (fun first last =>
        ∃ input evidence,
          target.transition first input last ∧
          target.edgeAdmissible first input last evidence ∧
          target.evidenceSufficient evidence)
      initial endpoint :=
  (certificate.continuation.transport initial endpoint sourceWitness).toLineage

/-- Existing OC countermodel: provenance reachability does not reconstruct continuation. -/
theorem provenance_lineage_projection_has_no_general_continuation_converse :
    LineageGenerated
        (fun source target => ∃ input, bridgeTransition source input target)
        .initial .terminal ∧
      ¬ Continues (bridgeContext false false) .initial .terminal :=
  raw_lineage_does_not_determine_contextual_continuation

end OCKIndividuationMSpaceComposition
