import OCKIndividuationMSpaceComposition.ContinuationCountermodels
import OCKIndividuationMSpaceComposition.OCContextAndContinuumBridge
import OCKIndividuationMSpaceComposition.FiniteReferenceDecision

namespace OCKIndividuationMSpaceComposition

/-!
# Research-closure countermodels and domain witnesses

These finite models discharge the previously open domain families.  They are
typed scientific countermodels, not claims that every real organisation,
fictional work or software repository has the same transition law.
-/

/-! ## Rollback is history-sensitive -/

inductive VersionState
  | v0 | v1 | rolledBack | recreated
  deriving DecidableEq, Repr

inductive VersionAction
  | revise | rollback
  deriving DecidableEq, Repr

inductive versionTransition : VersionState → VersionAction → VersionState → Prop
  | revise : versionTransition .v0 .revise .v1
  | rollback : versionTransition .v1 .rollback .rolledBack

def versionProjection : VersionState → Bool
  | .v0 | .rolledBack | .recreated => false
  | .v1 => true

def versionContext :
    ContinuationContext VersionState VersionAction Unit Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := versionTransition
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

def rollbackHistory : OpenHistory versionTransition .v0 .rolledBack :=
  .extend
    (.extend .start VersionAction.revise versionTransition.revise)
    VersionAction.rollback versionTransition.rollback

def rollbackEvidence : HistoryEvidence versionContext rollbackHistory :=
  .extend
    (.extend .start VersionAction.revise versionTransition.revise () trivial trivial)
    VersionAction.rollback versionTransition.rollback () trivial trivial

def rollbackWitness : ContinuationWitness versionContext .v0 .rolledBack :=
  ⟨rollbackHistory, rollbackEvidence, trivial⟩

theorem no_version_history_v0_recreated :
    OpenHistory versionTransition .v0 .recreated → False := by
  intro history
  cases history with
  | extend previous input edge => cases edge

theorem rollback_is_continuation_but_delete_recreate_is_not :
    versionProjection .rolledBack = versionProjection .recreated ∧
      Continues versionContext .v0 .rolledBack ∧
      ¬ Continues versionContext .v0 .recreated := by
  refine ⟨rfl, ⟨rollbackWitness⟩, ?_⟩
  rintro ⟨witness⟩
  exact no_version_history_v0_recreated witness.history

/-! ## Event anchoring and competing criteria -/

structure EventAnchoredReference
    {State Input Evidence Task Projection Boundary Constraint Scope Frame Event : Type}
    (context : ContinuationContext State Input Evidence Task Projection Boundary
      Constraint Scope Frame)
    (event : Event)
    (eventParticipant current : State) : Prop where
  continuation : Continues context eventParticipant current
  eventEvidenceBound : event = event

theorem eventAnchoredReference_implies_continuation
    {State Input Evidence Task Projection Boundary Constraint Scope Frame Event : Type}
    {context : ContinuationContext State Input Evidence Task Projection Boundary
      Constraint Scope Frame}
    {event : Event}
    {eventParticipant current : State}
    (reference : EventAnchoredReference context event eventParticipant current) :
    Continues context eventParticipant current :=
  reference.continuation

inductive AxeMaterialTransition : AxeState → AxeAction → AxeState → Prop
  | reassemble : AxeMaterialTransition .a0 .replaceHead .reassembled

def axeMaterialContext :
    ContinuationContext AxeState AxeAction AxeEvidence Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := AxeMaterialTransition
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

def axeMaterialHistory :
    OpenHistory AxeMaterialTransition .a0 .reassembled :=
  .extend .start AxeAction.replaceHead AxeMaterialTransition.reassemble

def axeMaterialEvidence :
    HistoryEvidence axeMaterialContext axeMaterialHistory :=
  .extend .start AxeAction.replaceHead AxeMaterialTransition.reassemble
    AxeEvidence.partsOnly trivial trivial

def axeMaterialWitness :
    ContinuationWitness axeMaterialContext .a0 .reassembled :=
  ⟨axeMaterialHistory, axeMaterialEvidence, trivial⟩

theorem no_material_history_a0_a2 :
    OpenHistory AxeMaterialTransition .a0 .a2 → False := by
  intro history
  cases history with
  | extend previous input edge => cases edge

theorem historical_and_material_criteria_conflict :
    Continues axeHistoricalContext .a0 .a2 ∧
      ¬ Continues axeHistoricalContext .a0 .reassembled ∧
      Continues axeMaterialContext .a0 .reassembled ∧
      ¬ Continues axeMaterialContext .a0 .a2 := by
  refine ⟨⟨axeA0A2Witness⟩, original_parts_do_not_force_historical_continuation,
    ⟨axeMaterialWitness⟩, ?_⟩
  rintro ⟨witness⟩
  exact no_material_history_a0_a2 witness.history

def axeFunction (_ : AxeState) : Bool := true

theorem function_only_cannot_select_historical_continuation :
    axeFunction .a2 = axeFunction .b ∧
      Continues axeHistoricalContext .a0 .a2 ∧
      ¬ Continues axeHistoricalContext .a0 .b := by
  exact ⟨rfl, terminal_projection_does_not_determine_continuation.2⟩

/-! ## Rename, co-reference, false common ground and attack evidence -/

inductive SolarSignal
  | sunEnglish | sunRussian
  deriving DecidableEq, Repr

inductive SolarReferent
  | sun | betelgeuse
  deriving DecidableEq, Repr

def solarBinding : SolarSignal → SolarReferent → Prop
  | .sunEnglish, .sun => True
  | .sunRussian, .sun => True
  | _, _ => False

theorem translation_corefers_without_signal_equality :
    SolarSignal.sunEnglish ≠ SolarSignal.sunRussian ∧
      solarBinding .sunEnglish .sun ∧ solarBinding .sunRussian .sun := by
  exact ⟨by decide, trivial, trivial⟩

def decoderEnglish (_ : Unit) : SolarReferent := .sun
def decoderMistaken (_ : Unit) : SolarReferent := .betelgeuse

theorem false_common_ground_is_task_distinguishable :
    decoderEnglish () ≠ decoderMistaken () := by decide

inductive EvidenceOrigin
  | trusted | attacker
  deriving DecidableEq, Repr

inductive InjectionCandidate
  | intended | injected
  deriving DecidableEq, Repr

def naiveAliasCandidate (_ : InjectionCandidate) : Prop := True

def provenanceBoundCandidate : EvidenceOrigin → InjectionCandidate → Prop
  | .trusted, .intended => True
  | _, _ => False

theorem provenance_filter_blocks_adversarial_injection :
    naiveAliasCandidate .injected ∧
      ¬ provenanceBoundCandidate .trusted .injected ∧
      provenanceBoundCandidate .trusted .intended := by
  exact ⟨trivial, by simp [provenanceBoundCandidate], trivial⟩

/-! ## Fiction and non-circular self-reference -/

inductive TypedReferent
  | physicalObject (id : Nat)
  | fictionalWorkEntity (workId : Nat)
  deriving DecidableEq, Repr

def harryPotterReferent : TypedReferent := .fictionalWorkEntity 1

theorem fictional_reference_does_not_imply_physical_continuant (id : Nat) :
    harryPotterReferent ≠ .physicalObject id := by
  intro equality
  cases equality

inductive DocumentSignal
  | thisDocument
  deriving DecidableEq, Repr

inductive DocumentReferent
  | researchOrder
  deriving DecidableEq, Repr

structure TypedSelfReference where
  signal : DocumentSignal
  referent : DocumentReferent
  binds : signal = .thisDocument ∧ referent = .researchOrder

def researchOrderSelfReference : TypedSelfReference :=
  ⟨.thisDocument, .researchOrder, rfl, rfl⟩

theorem self_reference_is_a_typed_binding_not_recursive_identity :
    researchOrderSelfReference.signal = .thisDocument ∧
      researchOrderSelfReference.referent = .researchOrder :=
  researchOrderSelfReference.binds

/-! ## Merge-specific governance and a full replacement chain -/

theorem conflicting_merge_evidence_blocks_propagation
    {State Input Evidence Task Projection Boundary Constraint Scope Frame Policy Time : Type}
    {context : ContinuationContext State Input Evidence Task Projection Boundary
      Constraint Scope Frame}
    {decision : GovernanceDecision State Evidence Scope Policy Time}
    {target : State}
    {evaluationTime : Time}
    (propagation : GovernancePropagationWitness context decision target evaluationTime)
    {mergeEvidence : Evidence}
    (inPath : mergeEvidence ∈ propagation.continuation.evidence.evidenceTrace)
    (conflicting : decision.requalificationTrigger mergeEvidence) : False :=
  propagation.noRequalificationTrigger mergeEvidence inPath conflicting

inductive AgentState
  | g0 | g1 | g2 | g3 | g4
  deriving DecidableEq, Repr

inductive AgentAction
  | replaceModel | replacePrompt | replaceTools | replaceRuntime
  deriving DecidableEq, Repr

inductive agentTransition : AgentState → AgentAction → AgentState → Prop
  | model : agentTransition .g0 .replaceModel .g1
  | prompt : agentTransition .g1 .replacePrompt .g2
  | tools : agentTransition .g2 .replaceTools .g3
  | runtime : agentTransition .g3 .replaceRuntime .g4

def agentContext :
    ContinuationContext AgentState AgentAction Unit Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := agentTransition
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

def agentFullReplacementHistory : OpenHistory agentTransition .g0 .g4 :=
  .extend
    (.extend
      (.extend
        (.extend .start AgentAction.replaceModel agentTransition.model)
        AgentAction.replacePrompt agentTransition.prompt)
      AgentAction.replaceTools agentTransition.tools)
    AgentAction.replaceRuntime agentTransition.runtime

def agentFullReplacementEvidence :
    HistoryEvidence agentContext agentFullReplacementHistory :=
  .extend
    (.extend
      (.extend
        (.extend .start AgentAction.replaceModel agentTransition.model () trivial trivial)
        AgentAction.replacePrompt agentTransition.prompt () trivial trivial)
      AgentAction.replaceTools agentTransition.tools () trivial trivial)
    AgentAction.replaceRuntime agentTransition.runtime () trivial trivial

def agentFullReplacementWitness :
    ContinuationWitness agentContext .g0 .g4 :=
  ⟨agentFullReplacementHistory, agentFullReplacementEvidence, trivial⟩

def sharesOriginalComponent : AgentState → AgentState → Prop
  | .g0, .g4 => False
  | _, _ => True

theorem full_component_replacement_can_have_witnessed_continuation :
    ¬ sharesOriginalComponent .g0 .g4 ∧ Continues agentContext .g0 .g4 := by
  exact ⟨by simp [sharesOriginalComponent], ⟨agentFullReplacementWitness⟩⟩

def agentDecision : GovernanceDecision AgentState Unit Unit Unit Unit where
  subject := .g0
  scope := ()
  policy := ()
  requiredInvariant := fun _ => True
  evidenceRequired := fun _ => True
  requalificationTrigger := fun _ => False
  validAt := fun _ => True
  revokedAt := fun _ => False

def agentFullReplacementPropagation :
    GovernancePropagationWitness agentContext agentDecision .g4 () where
  continuation := agentFullReplacementWitness
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
    simp [agentDecision]
  decisionValid := trivial
  decisionNotRevoked := by simp [agentDecision]

theorem full_replacement_decision_propagates_only_by_declared_contract :
    Propagates agentContext agentDecision .g4 () :=
  ⟨agentFullReplacementPropagation⟩

end OCKIndividuationMSpaceComposition
