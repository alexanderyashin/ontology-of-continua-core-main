import OCKIndividuationMSpaceComposition.GovernancePropagation
import OCKIndividuationMSpaceComposition.PathAlignedSequentialCausalTransport

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uPolicy uTime uCausalContext

/-!
# Governance-safe sequential causal transport

Plain context compatibility transports a continuation witness, but does not by
itself promise that the transported evidence still satisfies a governance
decision or remains trigger-free.  This module supplies the missing minimum
contract and couples it to the existing path-aligned sequential causal
certificate through one source witness and one context transport.
-/

/-- Minimum additional contract required to transport one governance decision
through an existing continuation-context compatibility. -/
structure GovernanceContextTransportContract
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (decision : GovernanceDecision State Evidence Scope Policy Time) where
  context : ContextCompatibility source target
  targetDecisionInvariantPreserved :
    OpenHistory.PreservesInvariant target.transition decision.requiredInvariant
  evidenceAdequacyPreserved :
    ∀ {initial endpoint}
      (witness : ContinuationWitness source initial endpoint),
      (∀ evidence,
        evidence ∈ witness.evidence.evidenceTrace → decision.evidenceRequired evidence) →
      ∀ evidence,
        evidence ∈ (context.transport initial endpoint witness).evidence.evidenceTrace →
          decision.evidenceRequired evidence
  triggerFreedomPreserved :
    ∀ {initial endpoint}
      (witness : ContinuationWitness source initial endpoint),
      (∀ evidence,
        evidence ∈ witness.evidence.evidenceTrace →
          ¬ decision.requalificationTrigger evidence) →
      ∀ evidence,
        evidence ∈ (context.transport initial endpoint witness).evidence.evidenceTrace →
          ¬ decision.requalificationTrigger evidence

/-- Positive governance transport theorem.  Validity and revocation are fields
of the same decision at the same evaluation time; scope compatibility follows
by composition, while invariant and evidence obligations require the explicit
contract above. -/
def GovernanceContextTransportContract.transportPropagation
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    (contract : GovernanceContextTransportContract source target decision)
    {endpoint : State} {evaluationTime : Time}
    (sourcePropagation :
      GovernancePropagationWitness source decision endpoint evaluationTime) :
    GovernancePropagationWitness target decision endpoint evaluationTime where
  continuation := contract.context.transport decision.subject endpoint
    sourcePropagation.continuation
  scopeCompatible := sourcePropagation.scopeCompatible.trans
    contract.context.scopeCompatible
  decisionInvariantInitially := sourcePropagation.decisionInvariantInitially
  decisionInvariantPreserved := contract.targetDecisionInvariantPreserved
  evidenceAdequate := contract.evidenceAdequacyPreserved
    sourcePropagation.continuation sourcePropagation.evidenceAdequate
  noRequalificationTrigger := contract.triggerFreedomPreserved
    sourcePropagation.continuation sourcePropagation.noRequalificationTrigger
  decisionValid := sourcePropagation.decisionValid
  decisionNotRevoked := sourcePropagation.decisionNotRevoked

/-- Reader-facing consequence: the explicit governance transport contract maps
source propagation to target propagation. -/
theorem governance_context_transport_is_sound
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    (contract : GovernanceContextTransportContract source target decision)
    {endpoint : State} {evaluationTime : Time}
    (sourcePropagation :
      GovernancePropagationWitness source decision endpoint evaluationTime) :
    Propagates target decision endpoint evaluationTime :=
  ⟨contract.transportPropagation sourcePropagation⟩

/-! ## One coherent governance / sequential / causal certificate -/

/-- The full certificate shares both the source continuation witness and the
context transport.  This prevents governance evidence from being checked on
one path while the causal effect is transported along another. -/
structure GovernedPathAlignedSequentialCausalTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (decision : GovernanceDecision State Evidence Scope Policy Time)
    (CausalContext : Type uCausalContext) [Fintype CausalContext]
    (endpoint : State) (evaluationTime : Time) (horizon : Nat) where
  sourceGovernance :
    GovernancePropagationWitness source decision endpoint evaluationTime
  governanceTransport : GovernanceContextTransportContract source target decision
  sequentialCausal : PathAlignedSequentialCausalTransport source target CausalContext
    decision.subject endpoint horizon
  sameSourceContinuation :
    sequentialCausal.sequential.continuation = sourceGovernance.continuation
  sameContextTransport :
    sequentialCausal.compatibility.context = governanceTransport.context

/-- Flagship positive composition.  One coherent certificate establishes
target governance propagation, target referent continuation, horizon
preservation, target decision-invariant preservation, sequential causal
identification and the robust transported-effect bound. -/
theorem governed_path_aligned_sequential_causal_transport_is_sound
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {endpoint : State} {evaluationTime : Time} {horizon : Nat}
    (certificate : GovernedPathAlignedSequentialCausalTransport
      source target decision CausalContext endpoint evaluationTime horizon) :
    Propagates target decision endpoint evaluationTime ∧
      Continues target decision.subject endpoint ∧
      (certificate.sequentialCausal.causal.continuation.transport
        decision.subject endpoint
        certificate.sequentialCausal.sequential.continuation).history.length = horizon ∧
      decision.requiredInvariant endpoint ∧
      sequentialRegimeValue
          certificate.sequentialCausal.sequential.identification.identifiedStageEffect =
        sequentialRegimeValue
          certificate.sequentialCausal.sequential.identification.latentStageEffect ∧
      |domainAverageEffect certificate.sequentialCausal.causal.targetWeight
          certificate.sequentialCausal.causal.targetEffect -
        domainAverageEffect certificate.sequentialCausal.causal.sourceWeight
          certificate.sequentialCausal.causal.sourceEffect| ≤
        certificate.sequentialCausal.causal.mechanismDriftRadius +
          certificate.sequentialCausal.causal.effectMagnitudeBound *
            ∑ context,
              |certificate.sequentialCausal.causal.targetWeight context -
                certificate.sequentialCausal.causal.sourceWeight context| := by
  let targetPropagation :=
    certificate.governanceTransport.transportPropagation
      certificate.sourceGovernance
  have causalSound :=
    path_aligned_sequential_causal_transport_is_sound
      certificate.sequentialCausal
  exact ⟨⟨targetPropagation⟩, causalSound.1, causalSound.2.1,
    propagation_preserves_decision_invariant targetPropagation,
    causalSound.2.2.1, causalSound.2.2.2⟩

/-- Revocation blocks the full package because its governance component would
contradict the decision's required non-revocation premise. -/
theorem revoked_decision_blocks_governed_sequential_causal_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {endpoint : State} {evaluationTime : Time} {horizon : Nat}
    (revoked : decision.revokedAt evaluationTime) :
    ¬ Nonempty (GovernedPathAlignedSequentialCausalTransport
      source target decision CausalContext endpoint evaluationTime horizon) := by
  rintro ⟨certificate⟩
  exact certificate.sourceGovernance.decisionNotRevoked revoked

/-- A target continuation obstruction blocks the full package independently
of any scalar causal estimate. -/
theorem target_obstruction_blocks_governed_sequential_causal_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    {endpoint : State} {evaluationTime : Time} {horizon : Nat}
    (obstruction : ¬ Continues target decision.subject endpoint) :
    ¬ Nonempty (GovernedPathAlignedSequentialCausalTransport
      source target decision CausalContext endpoint evaluationTime horizon) := by
  rintro ⟨certificate⟩
  exact target_continuation_obstruction_blocks_path_aligned_sequential_causal_transport
    obstruction ⟨certificate.sequentialCausal⟩

/-! ## Sharp evidence-transport countermodel -/

private def toyGovernanceContext :
    ContinuationContext Unit Unit Bool Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := fun _ _ _ => True
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

private def toyCleanHistory :
    OpenHistory toyGovernanceContext.transition () () :=
  .extend .start () trivial

private def toyCleanEvidence :
    HistoryEvidence toyGovernanceContext toyCleanHistory :=
  .extend .start () trivial false trivial trivial

private def toyCleanWitness :
    ContinuationWitness toyGovernanceContext () () :=
  ⟨toyCleanHistory, toyCleanEvidence, trivial⟩

private def toyTriggeredHistory :
    OpenHistory toyGovernanceContext.transition () () :=
  .extend .start () trivial

private def toyTriggeredEvidence :
    HistoryEvidence toyGovernanceContext toyTriggeredHistory :=
  .extend .start () trivial true trivial trivial

private def toyTriggeredWitness :
    ContinuationWitness toyGovernanceContext () () :=
  ⟨toyTriggeredHistory, toyTriggeredEvidence, trivial⟩

private def triggerIntroducingCompatibility :
    ContextCompatibility toyGovernanceContext toyGovernanceContext where
  taskCompatible := rfl
  projectionCompatible := rfl
  boundaryCompatible := rfl
  scopeCompatible := rfl
  frameCompatible := rfl
  transport := by
    intro initial endpoint witness
    cases initial
    cases endpoint
    exact toyTriggeredWitness

/-- Plain context compatibility, even between a context and itself and with
the same one-step horizon, can replace clean evidence by trigger evidence.
Therefore governance preservation is not derivable from endpoint, frame,
scope, continuation existence or horizon preservation alone. -/
theorem context_compatibility_alone_does_not_preserve_trigger_freedom :
    (∀ evidence,
      evidence ∈ toyCleanWitness.evidence.evidenceTrace → evidence = false) ∧
    true ∈ (triggerIntroducingCompatibility.transport () ()
      toyCleanWitness).evidence.evidenceTrace ∧
    toyCleanWitness.history.length =
      (triggerIntroducingCompatibility.transport () ()
        toyCleanWitness).history.length := by
  constructor
  · intro evidence member
    simp [toyCleanWitness, toyCleanEvidence, HistoryEvidence.evidenceTrace] at member
    exact member
  · constructor
    · simp [triggerIntroducingCompatibility, toyTriggeredWitness,
        toyTriggeredEvidence, HistoryEvidence.evidenceTrace]
    · rfl

/-! ## Exact numerical sharpness fixture for the transported-effect term -/

private def balancedGovernanceWeight : Bool → ℚ := fun _ => (1 : ℚ) / 2

private def shiftedGovernanceWeight : Bool → ℚ := fun context =>
  if context then (3 : ℚ) / 4 else (1 : ℚ) / 4

private def signedGovernanceEffect : Bool → ℚ := fun context =>
  if context then 1 else -1

/-- With stable conditional effects, shifting context mass from `(1/2,1/2)`
to `(1/4,3/4)` changes the average effect by exactly `1/2`.  The robust
transport term `B * ||w_t-w_s||₁` is also exactly `1/2` for `B=1`, so the
weight-shift component of the bound is sharp. -/
theorem governed_causal_weight_shift_bound_is_sharp_on_bool_fixture :
    |domainAverageEffect shiftedGovernanceWeight signedGovernanceEffect -
        domainAverageEffect balancedGovernanceWeight signedGovernanceEffect| =
      (0 : ℚ) + 1 *
        ∑ context : Bool,
          |shiftedGovernanceWeight context - balancedGovernanceWeight context| := by
  norm_num [domainAverageEffect, shiftedGovernanceWeight,
    balancedGovernanceWeight, signedGovernanceEffect, Fintype.sum_bool]

end OCKIndividuationMSpaceComposition
