import OCKIndividuationMSpaceComposition.PathDependentContinuation
import Mathlib.Data.Real.Basic

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uFamily

/-!
# Sequential evidence inheritance across object revisions

An implementation SHA, path, deployment or status is a projection of a
revision, not the identity of the statistical experiment.  This module makes
the inherited statistical state explicit and states the edge contract needed
to transport it along a `ContinuationWitness`.
-/

/-- Quantitative state that must not be silently reset when the implementation
of one monitoring family is revised.  `eValue` need not be monotone: valid
e-processes can move in either direction. -/
structure SequentialEvidenceAccount (Family : Type uFamily) where
  family : Family
  lookIndex : ℕ
  cumulativeAlphaSpend : ℝ
  eValue : ℝ
  calibrationDebt : ℝ

/-- Per-edge contract for inheriting statistical state.  Ordinary observation
edges may change the e-value, but the experiment family is preserved and the
three irreversible counters cannot decrease.  A revision-only edge, which
contains no new observation, preserves the complete account exactly. -/
structure EvidenceInheritanceContract
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily}
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (account : State → SequentialEvidenceAccount Family)
    (revisionOnly : Evidence → Prop) where
  familyPreserved : ∀ {source target : State} {input : Input}
    {evidence : Evidence},
    context.transition source input target →
    context.edgeAdmissible source input target evidence →
    context.evidenceSufficient evidence →
    (account source).family = (account target).family
  lookIndexMonotone : ∀ {source target : State} {input : Input}
    {evidence : Evidence},
    context.transition source input target →
    context.edgeAdmissible source input target evidence →
    context.evidenceSufficient evidence →
    (account source).lookIndex ≤ (account target).lookIndex
  cumulativeSpendMonotone : ∀ {source target : State} {input : Input}
    {evidence : Evidence},
    context.transition source input target →
    context.edgeAdmissible source input target evidence →
    context.evidenceSufficient evidence →
    ((account source).cumulativeAlphaSpend : ℝ) ≤
      ((account target).cumulativeAlphaSpend : ℝ)
  calibrationDebtMonotone : ∀ {source target : State} {input : Input}
    {evidence : Evidence},
    context.transition source input target →
    context.edgeAdmissible source input target evidence →
    context.evidenceSufficient evidence →
    ((account source).calibrationDebt : ℝ) ≤
      ((account target).calibrationDebt : ℝ)
  revisionOnlyPreservesAccount : ∀ {source target : State} {input : Input}
    {evidence : Evidence},
    context.transition source input target →
    context.edgeAdmissible source input target evidence →
    context.evidenceSufficient evidence →
    revisionOnly evidence →
    account source = account target

namespace HistoryEvidence

/-- Positive composition theorem: all irreversible statistical coordinates
inherit monotonically along every admitted continuation history. -/
theorem sequentialEvidence_inherits_along_history
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {account : State → SequentialEvidenceAccount Family}
    {revisionOnly : Evidence → Prop}
    (contract : EvidenceInheritanceContract context account revisionOnly)
    {initial endpoint : State}
    {history : OpenHistory context.transition initial endpoint}
    (historyEvidence : HistoryEvidence context history) :
    (account initial).family = (account endpoint).family ∧
    (account initial).lookIndex ≤ (account endpoint).lookIndex ∧
    (account initial).cumulativeAlphaSpend ≤
      (account endpoint).cumulativeAlphaSpend ∧
    (account initial).calibrationDebt ≤ (account endpoint).calibrationDebt := by
  induction historyEvidence with
  | start => exact ⟨rfl, le_rfl, le_rfl, le_rfl⟩
  | extend previous input edge evidence admissible sufficient ih =>
      exact ⟨
        ih.1.trans (contract.familyPreserved edge admissible sufficient),
        ih.2.1.trans (contract.lookIndexMonotone edge admissible sufficient),
        ih.2.2.1.trans
          (contract.cumulativeSpendMonotone edge admissible sufficient),
        ih.2.2.2.trans
          (contract.calibrationDebtMonotone edge admissible sufficient)⟩

/-- A path consisting only of implementation revisions, with no new
observation, preserves the entire evidence account exactly. -/
theorem revisionOnly_history_preserves_account
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {account : State → SequentialEvidenceAccount Family}
    {revisionOnly : Evidence → Prop}
    (contract : EvidenceInheritanceContract context account revisionOnly)
    {initial endpoint : State}
    {history : OpenHistory context.transition initial endpoint}
    (historyEvidence : HistoryEvidence context history)
    (onlyRevisions : ∀ evidence,
      evidence ∈ historyEvidence.evidenceTrace → revisionOnly evidence) :
    account initial = account endpoint := by
  induction historyEvidence with
  | start => rfl
  | extend previous input edge evidence admissible sufficient ih =>
      have previousOnly : ∀ priorEvidence,
          priorEvidence ∈ previous.evidenceTrace →
            revisionOnly priorEvidence := by
        intro priorEvidence priorMember
        exact onlyRevisions priorEvidence (by
          simp only [HistoryEvidence.evidenceTrace, List.mem_cons]
          exact Or.inr priorMember)
      have currentEquality := ih previousOnly
      have edgeEquality := contract.revisionOnlyPreservesAccount
        edge admissible sufficient
        (onlyRevisions evidence (by
          simp [HistoryEvidence.evidenceTrace]))
      exact currentEquality.trans edgeEquality

end HistoryEvidence

namespace ContinuationWitness

theorem sequentialEvidence_inherits
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {account : State → SequentialEvidenceAccount Family}
    {revisionOnly : Evidence → Prop}
    (contract : EvidenceInheritanceContract context account revisionOnly)
    {initial endpoint : State}
    (witness : ContinuationWitness context initial endpoint) :
    (account initial).family = (account endpoint).family ∧
    (account initial).lookIndex ≤ (account endpoint).lookIndex ∧
    (account initial).cumulativeAlphaSpend ≤
      (account endpoint).cumulativeAlphaSpend ∧
    (account initial).calibrationDebt ≤ (account endpoint).calibrationDebt :=
  witness.evidence.sequentialEvidence_inherits_along_history contract

theorem revisionOnly_preserves_sequentialEvidence
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {account : State → SequentialEvidenceAccount Family}
    {revisionOnly : Evidence → Prop}
    (contract : EvidenceInheritanceContract context account revisionOnly)
    {initial endpoint : State}
    (witness : ContinuationWitness context initial endpoint)
    (onlyRevisions : ∀ evidence,
      evidence ∈ witness.evidence.evidenceTrace → revisionOnly evidence) :
    account initial = account endpoint :=
  witness.evidence.revisionOnly_history_preserves_account contract onlyRevisions

end ContinuationWitness

/-- No-go theorem for alpha laundering: under an admitted revision-only edge,
strictly reducing cumulative spend is contradictory. -/
theorem revisionOnly_cannot_reset_cumulativeSpend
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {account : State → SequentialEvidenceAccount Family}
    {revisionOnly : Evidence → Prop}
    (contract : EvidenceInheritanceContract context account revisionOnly)
    {source target : State} {input : Input} {evidence : Evidence}
    (edge : context.transition source input target)
    (admissible : context.edgeAdmissible source input target evidence)
    (sufficient : context.evidenceSufficient evidence)
    (revision : revisionOnly evidence)
    (claimedReset :
      (account target).cumulativeAlphaSpend <
        (account source).cumulativeAlphaSpend) : False := by
  have accountEquality := contract.revisionOnlyPreservesAccount
    edge admissible sufficient revision
  rw [← accountEquality] at claimedReset
  exact (lt_irrefl _ claimedReset)

/-- A new SHA/path/status token cannot by itself justify a fresh experiment:
if it is admitted only as an implementation revision, family, look, spend,
e-value and calibration debt all remain unchanged. -/
theorem revisionOnly_newProjection_has_no_freshEvidenceBudget
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamily}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {account : State → SequentialEvidenceAccount Family}
    {revisionOnly : Evidence → Prop}
    (contract : EvidenceInheritanceContract context account revisionOnly)
    {source target : State} {input : Input} {evidence : Evidence}
    (edge : context.transition source input target)
    (admissible : context.edgeAdmissible source input target evidence)
    (sufficient : context.evidenceSufficient evidence)
    (revision : revisionOnly evidence) :
    account source = account target :=
  contract.revisionOnlyPreservesAccount edge admissible sufficient revision

end OCKIndividuationMSpaceComposition
