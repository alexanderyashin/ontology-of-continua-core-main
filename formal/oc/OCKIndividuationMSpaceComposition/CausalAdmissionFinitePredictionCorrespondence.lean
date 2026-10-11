import OCKIndividuationMSpaceComposition.CausalAdmissionSequentialCorrespondence
import OCKIndividuationMSpaceComposition.FiniteObservationLearning

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uCausalContext uHypothesis

/-!
# Causal admission / finite prediction correspondence

The sequential P1--P7 certificate is a causal transport contract, while the
finite-observation certificate is a statistical contract.  This module keeps
them separate in the structure and composes them only when both are present.
It therefore turns a numerical confidence budget into an operational
prediction certificate without treating an observational estimate as a causal
effect by itself.
-/

structure AdmittedSequentialFinitePredictionCertificate
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (CausalContext : Type uCausalContext) [Fintype CausalContext]
    (initial endpoint : State) (horizon : Nat)
    (premises : CausalAdmissionPremises)
    (Hypothesis : Type uHypothesis)
    (sampleSize hypothesisCount : Nat) (epsilon delta failureProbability : ℝ)
    (trueRisk empiricalRisk : Hypothesis → ℝ)
    (chosen comparator : Hypothesis) where
  admissionTransport : AdmittedPathAlignedSequentialCausalTransport
    source target CausalContext initial endpoint horizon premises
  concentration : UniformConcentrationCertificate
    sampleSize hypothesisCount epsilon delta
  failureBound : failureProbability ≤
    2 * (hypothesisCount : ℝ) * Real.exp (-2 * (sampleSize : ℝ) * epsilon ^ 2)
  uniformDeviation : ∀ hypothesis,
    |empiricalRisk hypothesis - trueRisk hypothesis| ≤ epsilon
  empiricalOptimal : empiricalRisk chosen ≤ empiricalRisk comparator

theorem admitted_sequential_finite_prediction_is_sound
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State} {horizon : Nat}
    {premises : CausalAdmissionPremises}
    {Hypothesis : Type uHypothesis}
    {sampleSize hypothesisCount : Nat} {epsilon delta failureProbability : ℝ}
    {trueRisk empiricalRisk : Hypothesis → ℝ}
    {chosen comparator : Hypothesis}
    (certificate : AdmittedSequentialFinitePredictionCertificate
      source target CausalContext initial endpoint horizon premises Hypothesis
      sampleSize hypothesisCount epsilon delta failureProbability
      trueRisk empiricalRisk chosen comparator) :
    Continues target initial endpoint ∧
      (certificate.admissionTransport.transport.causal.continuation.transport
        initial endpoint
        certificate.admissionTransport.transport.sequential.continuation).history.length = horizon ∧
      sequentialRegimeValue
          certificate.admissionTransport.transport.sequential.identification.identifiedStageEffect =
        sequentialRegimeValue
          certificate.admissionTransport.transport.sequential.identification.latentStageEffect ∧
      trueRisk chosen ≤ trueRisk comparator + 2 * epsilon ∧
      failureProbability ≤ delta := by
  have transportSound :=
    admitted_path_aligned_sequential_transport_is_sound
      certificate.admissionTransport
  have riskSound := uniform_deviation_erm_excess_risk
    trueRisk empiricalRisk chosen comparator epsilon
    certificate.uniformDeviation certificate.empiricalOptimal
  have confidenceSound := concentration_bound_meets_declared_confidence
    sampleSize hypothesisCount epsilon delta failureProbability
    certificate.failureBound certificate.concentration
  exact ⟨transportSound.1, transportSound.2.1, transportSound.2.2.1,
    riskSound, confidenceSound⟩

theorem missing_transport_blocks_admitted_sequential_finite_prediction
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State} {horizon : Nat}
    {premises : CausalAdmissionPremises}
    {Hypothesis : Type uHypothesis}
    {sampleSize hypothesisCount : Nat} {epsilon delta failureProbability : ℝ}
    {trueRisk empiricalRisk : Hypothesis → ℝ}
    {chosen comparator : Hypothesis}
    (missing : ¬ premises.transport) :
    ¬ Nonempty (AdmittedSequentialFinitePredictionCertificate
      source target CausalContext initial endpoint horizon premises Hypothesis
      sampleSize hypothesisCount epsilon delta failureProbability
      trueRisk empiricalRisk chosen comparator) := by
  rintro ⟨certificate⟩
  exact missing certificate.admissionTransport.admission.2

theorem missing_concentration_blocks_admitted_sequential_finite_prediction
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {initial endpoint : State} {horizon : Nat}
    {premises : CausalAdmissionPremises}
    {Hypothesis : Type uHypothesis}
    {sampleSize hypothesisCount : Nat} {epsilon delta failureProbability : ℝ}
    {trueRisk empiricalRisk : Hypothesis → ℝ}
    {chosen comparator : Hypothesis}
    (missing : ¬ UniformConcentrationCertificate
      sampleSize hypothesisCount epsilon delta) :
    ¬ Nonempty (AdmittedSequentialFinitePredictionCertificate
      source target CausalContext initial endpoint horizon premises Hypothesis
      sampleSize hypothesisCount epsilon delta failureProbability
      trueRisk empiricalRisk chosen comparator) := by
  rintro ⟨certificate⟩
  exact missing certificate.concentration

end OCKIndividuationMSpaceComposition
