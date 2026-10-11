import OCKIndividuationMSpaceComposition.CausalAdmissionContract
import OCKIndividuationMSpaceComposition.PathAlignedSequentialCausalTransport

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uCausalContext

/-!
# Causal-admission / sequential-intervention correspondence

The static correspondence is not enough for path-dependent predictions.  This
adapter carries the same P1-P7 admission witness into the existing
horizon-preserving sequential certificate, so stage alignment, sequential
identification, and the causal transport bound are proved in one object.
-/

structure AdmittedPathAlignedSequentialCausalTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (CausalContext : Type uCausalContext) [Fintype CausalContext]
    (initial endpoint : State) (horizon : Nat)
    (premises : CausalAdmissionPremises) where
  admission : TransportedCausalAdmission premises
  transport : PathAlignedSequentialCausalTransport source target CausalContext
    initial endpoint horizon

theorem admitted_path_aligned_sequential_transport_is_sound
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State} {horizon : Nat}
    {premises : CausalAdmissionPremises}
    (certificate : AdmittedPathAlignedSequentialCausalTransport
      source target CausalContext initial endpoint horizon premises) :
    Continues target initial endpoint ∧
      (certificate.transport.causal.continuation.transport initial endpoint
        certificate.transport.sequential.continuation).history.length = horizon ∧
      sequentialRegimeValue certificate.transport.sequential.identification.identifiedStageEffect =
        sequentialRegimeValue certificate.transport.sequential.identification.latentStageEffect ∧
      |domainAverageEffect certificate.transport.causal.targetWeight
          certificate.transport.causal.targetEffect -
        domainAverageEffect certificate.transport.causal.sourceWeight
          certificate.transport.causal.sourceEffect| ≤
        certificate.transport.causal.mechanismDriftRadius +
          certificate.transport.causal.effectMagnitudeBound *
            ∑ context,
              |certificate.transport.causal.targetWeight context -
                certificate.transport.causal.sourceWeight context| := by
  exact path_aligned_sequential_causal_transport_is_sound certificate.transport

theorem missing_transport_blocks_admitted_path_aligned_sequential_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State} {horizon : Nat}
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.transport) :
    ¬ Nonempty (AdmittedPathAlignedSequentialCausalTransport
      source target CausalContext initial endpoint horizon premises) := by
  rintro ⟨certificate⟩
  exact missing certificate.admission.2

theorem target_obstruction_blocks_admitted_path_aligned_sequential_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State} {horizon : Nat}
    {premises : CausalAdmissionPremises}
    (obstruction : ¬ Continues target initial endpoint) :
    ¬ Nonempty (AdmittedPathAlignedSequentialCausalTransport
      source target CausalContext initial endpoint horizon premises) := by
  rintro ⟨certificate⟩
  exact target_continuation_obstruction_blocks_path_aligned_sequential_causal_transport
    obstruction ⟨certificate.transport⟩

end OCKIndividuationMSpaceComposition
