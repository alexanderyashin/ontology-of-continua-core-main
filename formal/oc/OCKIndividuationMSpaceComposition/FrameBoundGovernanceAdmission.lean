import OCKIndividuationMSpaceComposition.FramePressureMSpaceAdapter
import OCKIndividuationMSpaceComposition.GovernancePropagation

namespace OCKIndividuationMSpaceComposition

/-!
A single admission contract joining task-relative reference binding to
path-dependent governance propagation.  Task/frame/projection compatibility,
lineage, candidate validity, decision validity and requalification triggers are
kept as separate fields so that none can be laundered through another.
-/

universe
  uSignal uState uInput uEvidence uTask uProjection uBoundary uConstraint
  uScope uFrame uPolicy uTime

/-- Complete proof object for one governed reference-transfer decision. -/
structure FrameBoundGovernanceAdmission
    {Signal : Type uSignal}
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
    (signalLineage : Signal → Signal → Prop)
    (sourceSignal targetSignal : Signal)
    (query : ReferenceQuery Signal State Task Frame Projection Constraint)
    (sourceReferent targetReferent : State)
    (decision : GovernanceDecision State Evidence Scope Policy Time)
    (evaluationTime : Time) where
  taskCompatible : query.task = context.task
  frameCompatible : query.frame = context.frame
  projectionCompatible : query.projection = context.projection
  signalContinues : signalLineage sourceSignal targetSignal
  referentContinuation : ContinuationWitness context sourceReferent targetReferent
  targetCandidate : CandidateSatisfies query targetReferent
  decisionSubject : decision.subject = sourceReferent
  scopeCompatible : decision.scope = context.scope
  decisionInvariantInitially : decision.requiredInvariant sourceReferent
  decisionInvariantPreserved :
    OpenHistory.PreservesInvariant context.transition decision.requiredInvariant
  evidenceAdequate :
    ∀ evidence,
      evidence ∈ referentContinuation.evidence.evidenceTrace →
        decision.evidenceRequired evidence
  noRequalificationTrigger :
    ∀ evidence,
      evidence ∈ referentContinuation.evidence.evidenceTrace →
        ¬ decision.requalificationTrigger evidence
  decisionValid : decision.validAt evaluationTime
  decisionNotRevoked : ¬ decision.revokedAt evaluationTime

/-- The admission contract constructs the existing reference-binding witness. -/
def FrameBoundGovernanceAdmission.toBindingWitness
    {Signal : Type uSignal} {State : Type uState} {Input : Type uInput}
    {Evidence : Type uEvidence} {Task : Type uTask}
    {Projection : Type uProjection} {Boundary : Type uBoundary}
    {Constraint : Type uConstraint} {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (admission : FrameBoundGovernanceAdmission context signalLineage
      sourceSignal targetSignal query sourceReferent targetReferent decision evaluationTime) :
    BindingWitness context signalLineage sourceSignal targetSignal query
      sourceReferent targetReferent where
  signalContinues := admission.signalContinues
  referentContinues := ⟨admission.referentContinuation⟩
  targetCandidate := admission.targetCandidate

/-- The same admission contract constructs the existing governance witness. -/
def FrameBoundGovernanceAdmission.toGovernancePropagationWitness
    {Signal : Type uSignal} {State : Type uState} {Input : Type uInput}
    {Evidence : Type uEvidence} {Task : Type uTask}
    {Projection : Type uProjection} {Boundary : Type uBoundary}
    {Constraint : Type uConstraint} {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (admission : FrameBoundGovernanceAdmission context signalLineage
      sourceSignal targetSignal query sourceReferent targetReferent decision evaluationTime) :
    GovernancePropagationWitness context decision targetReferent evaluationTime := by
  cases admission.decisionSubject
  exact {
    continuation := admission.referentContinuation
    scopeCompatible := admission.scopeCompatible
    decisionInvariantInitially := admission.decisionInvariantInitially
    decisionInvariantPreserved := admission.decisionInvariantPreserved
    evidenceAdequate := admission.evidenceAdequate
    noRequalificationTrigger := admission.noRequalificationTrigger
    decisionValid := admission.decisionValid
    decisionNotRevoked := admission.decisionNotRevoked
  }

/-- Positive theorem: the full frame yields both binding and propagation. -/
theorem frame_bound_admission_yields_binding_and_propagation
    {Signal : Type uSignal} {State : Type uState} {Input : Type uInput}
    {Evidence : Type uEvidence} {Task : Type uTask}
    {Projection : Type uProjection} {Boundary : Type uBoundary}
    {Constraint : Type uConstraint} {Scope : Type uScope} {Frame : Type uFrame}
    {Policy : Type uPolicy} {Time : Type uTime}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (admission : FrameBoundGovernanceAdmission context signalLineage
      sourceSignal targetSignal query sourceReferent targetReferent decision evaluationTime) :
    BindingWitness context signalLineage sourceSignal targetSignal query
        sourceReferent targetReferent ∧
      Propagates context decision targetReferent evaluationTime :=
  ⟨admission.toBindingWitness,
    ⟨admission.toGovernancePropagationWitness⟩⟩

theorem task_mismatch_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (mismatch : query.task ≠ context.task) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact mismatch admission.taskCompatible

theorem frame_mismatch_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (mismatch : query.frame ≠ context.frame) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact mismatch admission.frameCompatible

theorem projection_mismatch_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (mismatch : query.projection ≠ context.projection) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact mismatch admission.projectionCompatible

theorem missing_signal_lineage_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (missing : ¬ signalLineage sourceSignal targetSignal) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact missing admission.signalContinues

theorem missing_lineage_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (noLineage : ¬ Continues context sourceReferent targetReferent) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact noLineage ⟨admission.referentContinuation⟩

theorem invalid_candidate_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (invalid : ¬ CandidateSatisfies query targetReferent) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact invalid admission.targetCandidate

theorem subject_mismatch_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (mismatch : decision.subject ≠ sourceReferent) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact mismatch admission.decisionSubject

theorem scope_mismatch_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (mismatch : decision.scope ≠ context.scope) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact mismatch admission.scopeCompatible

theorem missing_initial_invariant_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (missing : ¬ decision.requiredInvariant sourceReferent) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact missing admission.decisionInvariantInitially

theorem missing_preservation_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (missing : ¬ OpenHistory.PreservesInvariant context.transition decision.requiredInvariant) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact missing admission.decisionInvariantPreserved

theorem inadequate_evidence_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (evidence : Evidence)
    (inadequate : ¬ decision.evidenceRequired evidence) :
    ∀ admission : FrameBoundGovernanceAdmission context signalLineage
        sourceSignal targetSignal query sourceReferent targetReferent decision evaluationTime,
      evidence ∈ admission.referentContinuation.evidence.evidenceTrace → False := by
  intro admission member
  exact inadequate (admission.evidenceAdequate evidence member)

theorem expired_decision_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (expired : ¬ decision.validAt evaluationTime) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact expired admission.decisionValid

theorem revoked_decision_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (revoked : decision.revokedAt evaluationTime) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact admission.decisionNotRevoked revoked

theorem witnessed_trigger_blocks_frame_bound_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {evaluationTime : Time}
    (evidence : Evidence)
    (triggered : decision.requalificationTrigger evidence) :
    ∀ admission : FrameBoundGovernanceAdmission context signalLineage
        sourceSignal targetSignal query sourceReferent targetReferent decision evaluationTime,
      evidence ∈ admission.referentContinuation.evidence.evidenceTrace → False := by
  intro admission member
  exact (admission.noRequalificationTrigger evidence member) triggered

end OCKIndividuationMSpaceComposition
