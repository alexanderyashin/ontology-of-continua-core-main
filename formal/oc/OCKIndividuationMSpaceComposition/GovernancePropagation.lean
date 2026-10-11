import OCKIndividuationMSpaceComposition.ContextualReferenceResolution

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uPolicy uTime uInstitution uRole

/-!
# Conditional propagation of governance decisions

Object continuation is necessary but not sufficient.  A decision propagates
only when its scope matches, its own invariant is preserved, its evidence
policy holds on every witnessed step, no requalification trigger occurs and
the decision is both valid and unrevoked at the evaluation time.
-/

structure GovernanceDecision
    (State : Type uState)
    (Evidence : Type uEvidence)
    (Scope : Type uScope)
    (Policy : Type uPolicy)
    (Time : Type uTime) where
  subject : State
  scope : Scope
  policy : Policy
  requiredInvariant : State → Prop
  evidenceRequired : Evidence → Prop
  requalificationTrigger : Evidence → Prop
  validAt : Time → Prop
  revokedAt : Time → Prop

structure GovernancePropagationWitness
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Policy : Type uPolicy}
    {Time : Type uTime}
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (decision : GovernanceDecision State Evidence Scope Policy Time)
    (target : State)
    (evaluationTime : Time) : Type _ where
  continuation : ContinuationWitness context decision.subject target
  scopeCompatible : decision.scope = context.scope
  decisionInvariantInitially : decision.requiredInvariant decision.subject
  decisionInvariantPreserved :
    OpenHistory.PreservesInvariant context.transition decision.requiredInvariant
  evidenceAdequate :
    ∀ evidence,
      evidence ∈ continuation.evidence.evidenceTrace → decision.evidenceRequired evidence
  noRequalificationTrigger :
    ∀ evidence,
      evidence ∈ continuation.evidence.evidenceTrace →
        ¬ decision.requalificationTrigger evidence
  decisionValid : decision.validAt evaluationTime
  decisionNotRevoked : ¬ decision.revokedAt evaluationTime

def Propagates
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Policy : Type uPolicy}
    {Time : Type uTime}
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (decision : GovernanceDecision State Evidence Scope Policy Time)
    (target : State)
    (evaluationTime : Time) : Prop :=
  Nonempty (GovernancePropagationWitness context decision target evaluationTime)

/-- Zero-step applicability is available only under the decision's own contracts. -/
def reflexive_governance_propagation
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Policy : Type uPolicy}
    {Time : Type uTime}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (contextInvariant : context.invariant decision.subject)
    (scopeCompatible : decision.scope = context.scope)
    (decisionInvariant : decision.requiredInvariant decision.subject)
    (decisionInvariantPreserved :
      OpenHistory.PreservesInvariant context.transition decision.requiredInvariant)
    (decisionValid : decision.validAt evaluationTime)
    (decisionNotRevoked : ¬ decision.revokedAt evaluationTime) :
    GovernancePropagationWitness context decision decision.subject evaluationTime where
  continuation := .refl contextInvariant
  scopeCompatible := scopeCompatible
  decisionInvariantInitially := decisionInvariant
  decisionInvariantPreserved := decisionInvariantPreserved
  evidenceAdequate := by simp [HistoryEvidence.evidenceTrace, ContinuationWitness.refl]
  noRequalificationTrigger := by simp [HistoryEvidence.evidenceTrace, ContinuationWitness.refl]
  decisionValid := decisionValid
  decisionNotRevoked := decisionNotRevoked

theorem propagation_implies_continuation
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Policy : Type uPolicy}
    {Time : Type uTime}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {target : State}
    {evaluationTime : Time}
    (propagation : GovernancePropagationWitness context decision target evaluationTime) :
    Continues context decision.subject target :=
  ⟨propagation.continuation⟩

theorem propagation_preserves_decision_invariant
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Policy : Type uPolicy}
    {Time : Type uTime}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {target : State}
    {evaluationTime : Time}
    (propagation : GovernancePropagationWitness context decision target evaluationTime) :
    decision.requiredInvariant target :=
  propagation.continuation.history.invariant
    propagation.decisionInvariantInitially
    propagation.decisionInvariantPreserved

/-- Extend a valid propagation only with a tail satisfying the same decision contract. -/
def extend_governance_propagation
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Policy : Type uPolicy}
    {Time : Type uTime}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {middle target : State}
    {evaluationTime : Time}
    (prefixPropagation : GovernancePropagationWitness context decision middle evaluationTime)
    (tail : ContinuationWitness context middle target)
    (tailEvidenceAdequate :
      ∀ evidence, evidence ∈ tail.evidence.evidenceTrace → decision.evidenceRequired evidence)
    (tailHasNoTrigger :
      ∀ evidence, evidence ∈ tail.evidence.evidenceTrace →
        ¬ decision.requalificationTrigger evidence) :
    GovernancePropagationWitness context decision target evaluationTime := by
  let combined := prefixPropagation.continuation.comp tail
  refine {
    continuation := combined
    scopeCompatible := prefixPropagation.scopeCompatible
    decisionInvariantInitially := prefixPropagation.decisionInvariantInitially
    decisionInvariantPreserved := prefixPropagation.decisionInvariantPreserved
    evidenceAdequate := ?_
    noRequalificationTrigger := ?_
    decisionValid := prefixPropagation.decisionValid
    decisionNotRevoked := prefixPropagation.decisionNotRevoked
  }
  · intro evidence member
    have traceEquation := HistoryEvidence.evidenceTrace_append
      prefixPropagation.continuation.evidence tail.evidence
    change evidence ∈ combined.evidence.evidenceTrace at member
    rw [show combined.evidence.evidenceTrace =
      tail.evidence.evidenceTrace ++ prefixPropagation.continuation.evidence.evidenceTrace from traceEquation] at member
    rcases List.mem_append.mp member with tailMember | prefixMember
    · exact tailEvidenceAdequate evidence tailMember
    · exact prefixPropagation.evidenceAdequate evidence prefixMember
  · intro evidence member
    have traceEquation := HistoryEvidence.evidenceTrace_append
      prefixPropagation.continuation.evidence tail.evidence
    change evidence ∈ combined.evidence.evidenceTrace at member
    rw [show combined.evidence.evidenceTrace =
      tail.evidence.evidenceTrace ++ prefixPropagation.continuation.evidence.evidenceTrace from traceEquation] at member
    rcases List.mem_append.mp member with tailMember | prefixMember
    · exact tailHasNoTrigger evidence tailMember
    · exact prefixPropagation.noRequalificationTrigger evidence prefixMember

theorem revoked_decision_does_not_propagate
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Policy : Type uPolicy}
    {Time : Type uTime}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {target : State}
    {evaluationTime : Time}
    (revoked : decision.revokedAt evaluationTime) :
    GovernancePropagationWitness context decision target evaluationTime → False := by
  intro propagation
  exact propagation.decisionNotRevoked revoked

theorem expired_decision_does_not_propagate
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Policy : Type uPolicy}
    {Time : Type uTime}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {target : State}
    {evaluationTime : Time}
    (expired : ¬ decision.validAt evaluationTime) :
    GovernancePropagationWitness context decision target evaluationTime → False := by
  intro propagation
  exact expired propagation.decisionValid

/--
A waiver is separately authorized.  It is not evidence that the original
decision invariant survived and is never inserted into a continuation witness.
-/
structure GovernanceWaiver
    (State : Type uState)
    (Scope : Type uScope)
    (Policy : Type uPolicy)
    (Evidence : Type uEvidence)
    (Time : Type uTime) where
  subject : State
  scope : Scope
  waivedPolicy : Policy
  authorityEvidence : Evidence
  validAt : Time → Prop

/--
Responsibility is supplied by an institutional domain adapter; it is not
derived merely from continuation or governance propagation.
-/
structure InstitutionalResponsibilityAdapter
    (State : Type uState)
    (Institution : Type uInstitution)
    (Role : Type uRole) where
  responsible : Institution → Role → State → Prop
  responsibilityTransport : State → State → Prop
  transportRule :
    ∀ institution role source target,
      responsible institution role source →
      responsibilityTransport source target →
      responsible institution role target

theorem responsibility_propagates_only_via_adapter
    {State : Type uState}
    {Institution : Type uInstitution}
    {Role : Type uRole}
    (adapter : InstitutionalResponsibilityAdapter State Institution Role)
    {institution : Institution}
    {role : Role}
    {source target : State}
    (sourceResponsibility : adapter.responsible institution role source)
    (institutionalTransport : adapter.responsibilityTransport source target) :
    adapter.responsible institution role target :=
  adapter.transportRule institution role source target
    sourceResponsibility institutionalTransport

end OCKIndividuationMSpaceComposition
