import OCKIndividuationMSpaceComposition.GovernancePropagation

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

/-!
# Finite countermodels for continuation, reference and governance

These models refute endpoint-, pointer- and component-only identity rules.  The
positive theorems remain explicitly relative to a context and a witnessed path.
-/

inductive AxeState where
  | a0 | a1 | a2 | b | reassembled
  deriving DecidableEq, Repr

inductive AxeAction where
  | replaceHandle | replaceHead | pointerLink | reassemble
  deriving DecidableEq, Repr

inductive AxeEvidence where
  | maintenance | pointerOnly | partsOnly
  deriving DecidableEq, Repr

inductive AxeHistoricalTransition : AxeState → AxeAction → AxeState → Prop
  | replaceHandle : AxeHistoricalTransition .a0 .replaceHandle .a1
  | replaceHead : AxeHistoricalTransition .a1 .replaceHead .a2

inductive AxePointerTransition : AxeState → AxeAction → AxeState → Prop
  | replaceHandle : AxePointerTransition .a0 .replaceHandle .a1
  | replaceHead : AxePointerTransition .a1 .replaceHead .a2
  | pointerLink : AxePointerTransition .a0 .pointerLink .b

structure AxePhysicalState where
  handleReplaced : Bool
  headReplaced : Bool
  deriving DecidableEq, Repr

def axePhysicalProjection : AxeState → AxePhysicalState
  | .a0 => ⟨false, false⟩
  | .a1 => ⟨true, false⟩
  | .a2 => ⟨true, true⟩
  | .b => ⟨true, true⟩
  | .reassembled => ⟨false, false⟩

theorem axe_same_terminal_physical_state :
    axePhysicalProjection .a2 = axePhysicalProjection .b := rfl

def axeHistoricalContext :
    ContinuationContext AxeState AxeAction AxeEvidence Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := AxeHistoricalTransition
  edgeAdmissible := fun _ _ _ evidence => evidence = .maintenance
  evidenceSufficient := fun evidence => evidence = .maintenance
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

def axePointerContext :
    ContinuationContext AxeState AxeAction AxeEvidence Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := AxePointerTransition
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

def axeA0A1History :
    OpenHistory AxeHistoricalTransition .a0 .a1 :=
  .extend .start .replaceHandle .replaceHandle

def axeA0A1Evidence : HistoryEvidence axeHistoricalContext axeA0A1History :=
  .extend .start AxeAction.replaceHandle AxeHistoricalTransition.replaceHandle
    AxeEvidence.maintenance rfl rfl

def axeA0A1Witness : ContinuationWitness axeHistoricalContext .a0 .a1 :=
  ⟨axeA0A1History, axeA0A1Evidence, trivial⟩

def axeA0A2History :
    OpenHistory AxeHistoricalTransition .a0 .a2 :=
  .extend axeA0A1History .replaceHead .replaceHead

def axeA0A2Evidence : HistoryEvidence axeHistoricalContext axeA0A2History :=
  .extend axeA0A1Evidence AxeAction.replaceHead AxeHistoricalTransition.replaceHead
    AxeEvidence.maintenance rfl rfl

def axeA0A2Witness : ContinuationWitness axeHistoricalContext .a0 .a2 :=
  ⟨axeA0A2History, axeA0A2Evidence, trivial⟩

def axePointerHistory :
    OpenHistory AxePointerTransition .a0 .b :=
  .extend .start .pointerLink .pointerLink

def axePointerEvidence : HistoryEvidence axePointerContext axePointerHistory :=
  .extend .start AxeAction.pointerLink AxePointerTransition.pointerLink
    AxeEvidence.pointerOnly trivial trivial

def axePointerWitness : ContinuationWitness axePointerContext .a0 .b :=
  ⟨axePointerHistory, axePointerEvidence, trivial⟩

theorem no_historical_history_a0_b :
    OpenHistory AxeHistoricalTransition .a0 .b → False := by
  intro history
  cases history with
  | extend previous input edge => cases edge

theorem no_historical_history_a1_a0 :
    OpenHistory AxeHistoricalTransition .a1 .a0 → False := by
  intro history
  cases history with
  | extend previous input edge => cases edge

theorem no_historical_history_a0_reassembled :
    OpenHistory AxeHistoricalTransition .a0 .reassembled → False := by
  intro history
  cases history with
  | extend previous input edge => cases edge

theorem terminal_projection_does_not_determine_continuation :
    axePhysicalProjection .a2 = axePhysicalProjection .b ∧
    Continues axeHistoricalContext .a0 .a2 ∧
    ¬ Continues axeHistoricalContext .a0 .b := by
  refine ⟨rfl, ⟨axeA0A2Witness⟩, ?_⟩
  rintro ⟨witness⟩
  exact no_historical_history_a0_b witness.history

theorem continuation_is_not_generally_symmetric :
    Continues axeHistoricalContext .a0 .a1 ∧
    ¬ Continues axeHistoricalContext .a1 .a0 := by
  refine ⟨⟨axeA0A1Witness⟩, ?_⟩
  rintro ⟨witness⟩
  exact no_historical_history_a1_a0 witness.history

theorem original_parts_do_not_force_historical_continuation :
    ¬ Continues axeHistoricalContext .a0 .reassembled := by
  rintro ⟨witness⟩
  exact no_historical_history_a0_reassembled witness.history

def RawPointerEvidence (source target : AxeState) : Prop :=
  source = .a0 ∧ target = .b

theorem erased_pointer_lineage_has_no_historical_converse :
    LineageGenerated RawPointerEvidence .a0 .b ∧
    ¬ Continues axeHistoricalContext .a0 .b := by
  refine ⟨.ofEvidence ⟨rfl, rfl⟩, ?_⟩
  rintro ⟨witness⟩
  exact no_historical_history_a0_b witness.history

theorem pointer_context_does_not_transport_to_historical_context :
    ContextCompatibility axePointerContext axeHistoricalContext → False :=
  no_context_compatibility_of_counterexample
    ⟨axePointerWitness⟩
    (by
      rintro ⟨witness⟩
      exact no_historical_history_a0_b witness.history)

/-! A frame change is not a stable refinement, even when it prunes candidates. -/

def coarseReferenceQuery : ReferenceQuery Unit Bool Unit Bool Unit Bool where
  signal := ()
  task := ()
  frame := false
  projection := ()
  activeConstraint := fun _ => False
  satisfiesConstraint := fun candidate constraint => candidate = constraint

def fineReferenceQuery : ReferenceQuery Unit Bool Unit Bool Unit Bool where
  signal := ()
  task := ()
  frame := true
  projection := ()
  activeConstraint := fun constraint => constraint = true
  satisfiesConstraint := fun candidate constraint => candidate = constraint

theorem frame_shift_is_not_stable_refinement :
    StableReferenceRefinement coarseReferenceQuery fineReferenceQuery → False := by
  intro refinement
  cases refinement.frameStable

/-! Same endpoint, two histories: only one is governance-safe. -/

inductive GovernanceState where
  | root | safeMiddle | riskyMiddle | terminal
  deriving DecidableEq, Repr

inductive GovernanceAction where
  | safeStart | safeFinish | riskyStart | riskyFinish
  deriving DecidableEq, Repr

inductive GovernanceEvidence where
  | ordinary | requalification
  deriving DecidableEq, Repr

inductive GovernanceTransition :
    GovernanceState → GovernanceAction → GovernanceState → Prop
  | safeStart : GovernanceTransition .root .safeStart .safeMiddle
  | safeFinish : GovernanceTransition .safeMiddle .safeFinish .terminal
  | riskyStart : GovernanceTransition .root .riskyStart .riskyMiddle
  | riskyFinish : GovernanceTransition .riskyMiddle .riskyFinish .terminal

def governanceContext :
    ContinuationContext
      GovernanceState GovernanceAction GovernanceEvidence Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := GovernanceTransition
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

def safeGovernanceHistory :
    OpenHistory GovernanceTransition .root .terminal :=
  .extend (.extend .start .safeStart .safeStart) .safeFinish .safeFinish

def safeGovernanceEvidence : HistoryEvidence governanceContext safeGovernanceHistory :=
  .extend
    (.extend .start GovernanceAction.safeStart GovernanceTransition.safeStart
      GovernanceEvidence.ordinary trivial trivial)
    GovernanceAction.safeFinish GovernanceTransition.safeFinish
    GovernanceEvidence.ordinary trivial trivial

def safeGovernanceWitness :
    ContinuationWitness governanceContext .root .terminal :=
  ⟨safeGovernanceHistory, safeGovernanceEvidence, trivial⟩

def riskyGovernanceHistory :
    OpenHistory GovernanceTransition .root .terminal :=
  .extend (.extend .start .riskyStart .riskyStart) .riskyFinish .riskyFinish

def riskyGovernanceEvidence : HistoryEvidence governanceContext riskyGovernanceHistory :=
  .extend
    (.extend .start GovernanceAction.riskyStart GovernanceTransition.riskyStart
      GovernanceEvidence.ordinary trivial trivial)
    GovernanceAction.riskyFinish GovernanceTransition.riskyFinish
    GovernanceEvidence.requalification trivial trivial

def riskyGovernanceWitness :
    ContinuationWitness governanceContext .root .terminal :=
  ⟨riskyGovernanceHistory, riskyGovernanceEvidence, trivial⟩

def governanceDecision :
    GovernanceDecision GovernanceState GovernanceEvidence Unit Unit Unit where
  subject := .root
  scope := ()
  policy := ()
  requiredInvariant := fun _ => True
  evidenceRequired := fun _ => True
  requalificationTrigger := fun evidence => evidence = .requalification
  validAt := fun _ => True
  revokedAt := fun _ => False

def safe_governance_propagation :
    GovernancePropagationWitness governanceContext governanceDecision .terminal () where
  continuation := safeGovernanceWitness
  scopeCompatible := rfl
  decisionInvariantInitially := trivial
  decisionInvariantPreserved := by
    intro current next input currentInvariant edge
    trivial
  evidenceAdequate := by
    intro evidence member
    trivial
  noRequalificationTrigger := by
    intro evidence member
    simp [safeGovernanceWitness, safeGovernanceEvidence,
      HistoryEvidence.evidenceTrace] at member
    rcases member with rfl | rfl ; simp [governanceDecision]
  decisionValid := trivial
  decisionNotRevoked := by simp [governanceDecision]

theorem risky_history_contains_requalification :
    GovernanceEvidence.requalification ∈
      riskyGovernanceWitness.evidence.evidenceTrace := by
  simp [riskyGovernanceWitness, riskyGovernanceEvidence,
    HistoryEvidence.evidenceTrace]

theorem risky_path_cannot_satisfy_no_trigger
    (claimedNoTrigger :
      ∀ evidence,
        evidence ∈ riskyGovernanceWitness.evidence.evidenceTrace →
          ¬ governanceDecision.requalificationTrigger evidence) : False := by
  exact claimedNoTrigger .requalification
    risky_history_contains_requalification rfl

def axeDecision :
    GovernanceDecision AxeState AxeEvidence Unit Unit Unit where
  subject := .a0
  scope := ()
  policy := ()
  requiredInvariant := fun _ => True
  evidenceRequired := fun evidence => evidence = .maintenance
  requalificationTrigger := fun _ => False
  validAt := fun _ => True
  revokedAt := fun _ => False

def axe_governance_propagates_to_a2 :
    GovernancePropagationWitness axeHistoricalContext axeDecision .a2 () where
  continuation := axeA0A2Witness
  scopeCompatible := rfl
  decisionInvariantInitially := trivial
  decisionInvariantPreserved := by
    intro current next input currentInvariant edge
    trivial
  evidenceAdequate := by
    intro evidence member
    simp [axeA0A2Witness, axeA0A2Evidence, axeA0A1Evidence,
      HistoryEvidence.evidenceTrace] at member
    rcases member with rfl | rfl ; rfl
  noRequalificationTrigger := by
    intro evidence member
    simp [axeDecision]
  decisionValid := trivial
  decisionNotRevoked := by simp [axeDecision]

theorem identity_laundering_blocked :
    axePhysicalProjection .a2 = axePhysicalProjection .b ∧
    Propagates axeHistoricalContext axeDecision .a2 () ∧
    ¬ Propagates axeHistoricalContext axeDecision .b () := by
  refine ⟨rfl, ⟨axe_governance_propagates_to_a2⟩, ?_⟩
  rintro ⟨propagation⟩
  have continuation := propagation_implies_continuation propagation
  rcases continuation with ⟨witness⟩
  exact no_historical_history_a0_b witness.history

end OCKIndividuationMSpaceComposition
