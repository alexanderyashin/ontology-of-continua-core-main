import OCKIndividuationMSpaceComposition.CausalAdmissionContract
import OCKIndividuationMSpaceComposition.TypedCausalContinuationTransport

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uCausalContext

/-!
# Causal-admission / typed-transport correspondence

The admission contract is not a second, competing transport theory.  This
module composes its P1-P7 witness with the existing typed continuation and
causal-effect certificate.  Thus the mathematical conclusion is available
only when both layers are present; a positive observational score alone cannot
manufacture the transport certificate.
-/

structure AdmittedTypedExactCausalContinuationTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    (CausalContext : Type uCausalContext) [Fintype CausalContext]
    (premises : CausalAdmissionPremises) where
  admission : TransportedCausalAdmission premises
  transport : TypedExactCausalContinuationTransport source target CausalContext

theorem admitted_typed_exact_transport_certifies_continuation_and_effect
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {premises : CausalAdmissionPremises}
    (certificate : AdmittedTypedExactCausalContinuationTransport
      (source := source) (target := target) CausalContext premises)
    {initial endpoint : State}
    (sourceWitness : ContinuationWitness source initial endpoint) :
    Continues target initial endpoint ∧
      reweightedSourceEffect certificate.transport.causal.sourceWeight
          certificate.transport.causal.targetWeight
          certificate.transport.causal.sourceEffect =
        domainAverageEffect certificate.transport.causal.targetWeight
          certificate.transport.causal.targetEffect := by
  exact typed_exact_transport_certifies_continuation_and_effect
    (source := source) (target := target) (CausalContext := CausalContext)
    certificate.transport sourceWitness

theorem missing_transport_blocks_admitted_typed_exact_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.transport) :
    ¬ Nonempty (AdmittedTypedExactCausalContinuationTransport
      (source := source) (target := target) CausalContext premises) := by
  rintro ⟨certificate⟩
  exact missing certificate.admission.2

theorem frame_mismatch_blocks_admitted_typed_exact_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {premises : CausalAdmissionPremises}
    (mismatch : source.frame ≠ target.frame) :
    ¬ Nonempty (AdmittedTypedExactCausalContinuationTransport
      (source := source) (target := target) CausalContext premises) := by
  rintro ⟨certificate⟩
  exact frame_mismatch_blocks_typed_exact_causal_transport mismatch
    ⟨certificate.transport⟩

end OCKIndividuationMSpaceComposition
