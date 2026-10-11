import OCKIndividuationMSpaceComposition.FrameBoundGovernanceAdmission

namespace OCKIndividuationMSpaceComposition

/-!
Discrete first-passage semantics for governance expiry, revocation and observed
requalification evidence.  The results expose the exact temporal premises that
turn a static admission certificate into an operational validity horizon.
-/

/-- The first time an evidence stream satisfies the decision's trigger. -/
def EvidenceTriggerAt
    {State Evidence Scope Policy : Type*}
    (decision : GovernanceDecision State Evidence Scope Policy ℕ)
    (stream : ℕ → Evidence) (t : ℕ) : Prop :=
  decision.requalificationTrigger (stream t) ∧
    ∀ earlier, earlier < t → ¬ decision.requalificationTrigger (stream earlier)

theorem evidenceTriggerAt_unique
    {State Evidence Scope Policy : Type*}
    (decision : GovernanceDecision State Evidence Scope Policy ℕ)
    (stream : ℕ → Evidence) {first second : ℕ}
    (firstTrigger : EvidenceTriggerAt decision stream first)
    (secondTrigger : EvidenceTriggerAt decision stream second) :
    first = second := by
  rcases lt_trichotomy first second with before | equal | after
  · exact False.elim ((secondTrigger.2 first before) firstTrigger.1)
  · exact equal
  · exact False.elim ((firstTrigger.2 second after) secondTrigger.1)

theorem first_evidence_trigger_exists_of_occurs
    {State Evidence Scope Policy : Type*}
    (decision : GovernanceDecision State Evidence Scope Policy ℕ)
    [DecidablePred decision.requalificationTrigger]
    (stream : ℕ → Evidence) (observed : ℕ)
    (occurs : decision.requalificationTrigger (stream observed)) :
    ∃ first, EvidenceTriggerAt decision stream first := by
  let predicate : ℕ → Prop := fun t => decision.requalificationTrigger (stream t)
  have existsPredicate : ∃ t, predicate t := ⟨observed, occurs⟩
  refine ⟨Nat.find existsPredicate, Nat.find_spec existsPredicate, ?_⟩
  intro earlier before
  exact Nat.find_min existsPredicate before

/-- Exact half-open validity horizon `[0, cutoff)`. -/
def DecisionValidUntil
    {State Evidence Scope Policy : Type*}
    (decision : GovernanceDecision State Evidence Scope Policy ℕ)
    (cutoff : ℕ) : Prop :=
  ∀ t, decision.validAt t ↔ t < cutoff

/-- Exact revocation horizon `[cutoff, ∞)`. -/
def DecisionRevokedFrom
    {State Evidence Scope Policy : Type*}
    (decision : GovernanceDecision State Evidence Scope Policy ℕ)
    (cutoff : ℕ) : Prop :=
  ∀ t, decision.revokedAt t ↔ cutoff ≤ t

theorem admission_precedes_validity_cutoff
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy ℕ}
    {evaluationTime cutoff : ℕ}
    (validUntil : DecisionValidUntil decision cutoff)
    (admission : FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime) :
    evaluationTime < cutoff :=
  (validUntil evaluationTime).mp admission.decisionValid

theorem admission_precedes_revocation_cutoff
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy ℕ}
    {evaluationTime cutoff : ℕ}
    (revokedFrom : DecisionRevokedFrom decision cutoff)
    (admission : FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
      query sourceReferent targetReferent decision evaluationTime) :
    evaluationTime < cutoff := by
  exact Nat.lt_of_not_ge (fun atOrAfter =>
    admission.decisionNotRevoked ((revokedFrom evaluationTime).mpr atOrAfter))

theorem at_or_after_validity_cutoff_blocks_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy ℕ}
    {evaluationTime cutoff : ℕ}
    (validUntil : DecisionValidUntil decision cutoff)
    (atOrAfter : cutoff ≤ evaluationTime) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal query
      sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact (Nat.not_lt_of_ge atOrAfter) (admission_precedes_validity_cutoff validUntil admission)

theorem at_or_after_revocation_cutoff_blocks_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy ℕ}
    {evaluationTime cutoff : ℕ}
    (revokedFrom : DecisionRevokedFrom decision cutoff)
    (atOrAfter : cutoff ≤ evaluationTime) :
    FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal query
      sourceReferent targetReferent decision evaluationTime → False := by
  intro admission
  exact (Nat.not_lt_of_ge atOrAfter) (admission_precedes_revocation_cutoff revokedFrom admission)

theorem first_observed_trigger_blocks_admission
    {Signal State Input Evidence Task Projection Boundary Constraint Scope Frame Policy : Type*}
    {context : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {signalLineage : Signal → Signal → Prop} {sourceSignal targetSignal : Signal}
    {query : ReferenceQuery Signal State Task Frame Projection Constraint}
    {sourceReferent targetReferent : State}
    {decision : GovernanceDecision State Evidence Scope Policy ℕ}
    {evaluationTime first : ℕ}
    (stream : ℕ → Evidence)
    (firstTrigger : EvidenceTriggerAt decision stream first) :
    ∀ admission : FrameBoundGovernanceAdmission context signalLineage sourceSignal targetSignal
        query sourceReferent targetReferent decision evaluationTime,
      stream first ∈ admission.referentContinuation.evidence.evidenceTrace → False := by
  intro admission member
  exact (admission.noRequalificationTrigger (stream first) member) firstTrigger.1

/-- Any expiry, revocation or trigger occurrence is a governance barrier. -/
def GovernanceBarrierAt
    {State Evidence Scope Policy : Type*}
    (decision : GovernanceDecision State Evidence Scope Policy ℕ)
    (stream : ℕ → Evidence) (t : ℕ) : Prop :=
  ¬ decision.validAt t ∨ decision.revokedAt t ∨
    decision.requalificationTrigger (stream t)

/-- A barrier occurrence together with absence of every earlier barrier. -/
def FirstGovernanceBarrierAt
    {State Evidence Scope Policy : Type*}
    (decision : GovernanceDecision State Evidence Scope Policy ℕ)
    (stream : ℕ → Evidence) (t : ℕ) : Prop :=
  GovernanceBarrierAt decision stream t ∧
    ∀ earlier, earlier < t → ¬ GovernanceBarrierAt decision stream earlier

theorem firstGovernanceBarrierAt_unique
    {State Evidence Scope Policy : Type*}
    (decision : GovernanceDecision State Evidence Scope Policy ℕ)
    (stream : ℕ → Evidence) {first second : ℕ}
    (firstBarrier : FirstGovernanceBarrierAt decision stream first)
    (secondBarrier : FirstGovernanceBarrierAt decision stream second) :
    first = second := by
  rcases lt_trichotomy first second with before | equal | after
  · exact False.elim ((secondBarrier.2 first before) firstBarrier.1)
  · exact equal
  · exact False.elim ((firstBarrier.2 second after) secondBarrier.1)

theorem first_governance_barrier_exists_of_occurs
    {State Evidence Scope Policy : Type*}
    (decision : GovernanceDecision State Evidence Scope Policy ℕ)
    [DecidablePred decision.validAt]
    [DecidablePred decision.revokedAt]
    [DecidablePred decision.requalificationTrigger]
    (stream : ℕ → Evidence) (observed : ℕ)
    (occurs : GovernanceBarrierAt decision stream observed) :
    ∃ first, FirstGovernanceBarrierAt decision stream first := by
  let predicate : ℕ → Prop := fun t => GovernanceBarrierAt decision stream t
  letI : DecidablePred predicate := fun t => by
    dsimp [predicate, GovernanceBarrierAt]
    infer_instance
  have existsPredicate : ∃ t, predicate t := ⟨observed, occurs⟩
  refine ⟨Nat.find existsPredicate, Nat.find_spec existsPredicate, ?_⟩
  intro earlier before
  exact Nat.find_min existsPredicate before

end OCKIndividuationMSpaceComposition
