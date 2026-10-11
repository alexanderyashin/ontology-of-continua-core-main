import OCKIndividuationMSpaceComposition.UnifiedSynthesis

namespace OCKIndividuationMSpaceComposition

/-!
# Receipt-bound empirical theory gate

Lean proves the adjudication rule; it does not manufacture empirical facts.
`FrozenEmpiricalContract` records the pre-outcome commitments and
`ReceiptBoundGateEvidence` records only values copied from a sealed external
receipt.  A generated domain certificate can therefore be checked by Lean,
while the raw-data, licensing, sampling and statistical audits remain explicit
external evidence obligations.

The common theory-level gate requires independent physical, biological and
computational-organizational certificates.  One successful demonstrator is
formally insufficient for the cross-domain claim.
-/

/-- The three preregistered domains required by the first empirical gate. -/
inductive DemonstratorDomain
  | physical
  | biological
  | computationalOrganizational
  deriving DecidableEq, Repr

/--
The immutable part of one demonstrator, frozen before outcome access.
`decisionThreshold` is expressed in the protocol's declared oriented decision
statistic, so larger values are always better independently of the raw metric
convention.  The statistic may be a point gain, a simultaneous interval bound,
or another fully specified scalar; its meaning is carried by `decisionStatisticId`
and must not migrate between contracts.
-/
structure FrozenEmpiricalContract where
  contractId : String
  domain : DemonstratorDomain
  preregistrationDigest : String
  sourceBindingDigest : String
  predictorBundleDigest : String
  endpointId : String
  baselineId : String
  decisionStatisticId : String
  decisionThreshold : ℚ
  deriving Repr

/--
Every identifier and digest needed to bind a frozen contract is nonempty.
Digest syntax and cryptographic correctness remain external readback
obligations; Lean only rules out an all-empty or partially empty certificate.
-/
def FrozenEmpiricalContractWellFormed
    (contract : FrozenEmpiricalContract) : Prop :=
  contract.contractId ≠ "" ∧
  contract.preregistrationDigest ≠ "" ∧
  contract.sourceBindingDigest ≠ "" ∧
  contract.predictorBundleDigest ≠ "" ∧
  contract.endpointId ≠ "" ∧
  contract.baselineId ≠ "" ∧
  contract.decisionStatisticId ≠ ""

/--
Compact facts copied from an evaluator receipt.  Boolean fields are deliberate:
they make the generated certificate decidable and prevent a receipt adapter
from smuggling an unproved proposition into Lean.
-/
structure ReceiptBoundGateEvidence where
  receiptId : String
  receiptDigest : String
  observedContractId : String
  observedDomain : DemonstratorDomain
  observedEndpointId : String
  observedBaselineId : String
  observedDecisionStatisticId : String
  observedPreregistrationDigest : String
  observedSourceBindingDigest : String
  observedPredictorBundleDigest : String
  observedDecisionStatistic : ℚ
  heldOutSplitDisjoint : Bool
  outcomeFirewallIntact : Bool
  groupDirectionPassed : Bool
  negativeControlsPassed : Bool
  transportChecksPassed : Bool
  falsifierTriggered : Bool
  deriving Repr

/--
Every receipt-side identifier and digest used by the gate is nonempty.
This is a structural check only: external evidence must still establish that
the strings name immutable bytes produced by the declared roles.
-/
def ReceiptBoundGateEvidenceWellFormed
    (evidence : ReceiptBoundGateEvidence) : Prop :=
  evidence.receiptId ≠ "" ∧
  evidence.receiptDigest ≠ "" ∧
  evidence.observedContractId ≠ "" ∧
  evidence.observedEndpointId ≠ "" ∧
  evidence.observedBaselineId ≠ "" ∧
  evidence.observedDecisionStatisticId ≠ "" ∧
  evidence.observedPreregistrationDigest ≠ "" ∧
  evidence.observedSourceBindingDigest ≠ "" ∧
  evidence.observedPredictorBundleDigest ≠ ""

/--
The receipt names the complete frozen contract, not only its three payload
digests.  Digest computation and file readback remain external obligations;
Lean checks that the values imported by the adapter cannot migrate between
contracts, domains, endpoints or baselines.
-/
def ReceiptMatchesContract
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence) : Prop :=
  evidence.receiptId ≠ "" ∧
  evidence.receiptDigest ≠ "" ∧
  evidence.observedContractId = contract.contractId ∧
  evidence.observedDomain = contract.domain ∧
  evidence.observedEndpointId = contract.endpointId ∧
  evidence.observedBaselineId = contract.baselineId ∧
  evidence.observedDecisionStatisticId = contract.decisionStatisticId ∧
  evidence.observedPreregistrationDigest = contract.preregistrationDigest ∧
  evidence.observedSourceBindingDigest = contract.sourceBindingDigest ∧
  evidence.observedPredictorBundleDigest = contract.predictorBundleDigest

/-- The preregistered useful-effect and falsification decision rule. -/
def EmpiricalDecisionPass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence) : Prop :=
  contract.decisionThreshold < evidence.observedDecisionStatistic ∧
  evidence.heldOutSplitDisjoint = true ∧
  evidence.outcomeFirewallIntact = true ∧
  evidence.groupDirectionPassed = true ∧
  evidence.negativeControlsPassed = true ∧
  evidence.transportChecksPassed = true ∧
  evidence.falsifierTriggered = false

/-- Exact receipt/contract binding plus the preregistered decision rule. -/
def EmpiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence) : Prop :=
  FrozenEmpiricalContractWellFormed contract ∧
  ReceiptBoundGateEvidenceWellFormed evidence ∧
  ReceiptMatchesContract contract evidence ∧
  EmpiricalDecisionPass contract evidence

/-- A pass is domain-typed; a receipt cannot silently migrate between lanes. -/
def DomainEmpiricalGatePass
    (domain : DemonstratorDomain)
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence) : Prop :=
  contract.domain = domain ∧ EmpiricalGatePass contract evidence

/--
Artifact-level independence for the three evaluator receipts: their identifiers
and their content digests are pairwise distinct.  This does not by itself prove
statistical, causal or organizational independence; those remain external
protocol obligations.
-/
def CrossDomainEvidenceIndependent
    (physicalEvidence : ReceiptBoundGateEvidence)
    (biologicalEvidence : ReceiptBoundGateEvidence)
    (computationalOrganizationalEvidence : ReceiptBoundGateEvidence) : Prop :=
  physicalEvidence.receiptId ≠ biologicalEvidence.receiptId ∧
  physicalEvidence.receiptId ≠ computationalOrganizationalEvidence.receiptId ∧
  biologicalEvidence.receiptId ≠ computationalOrganizationalEvidence.receiptId ∧
  physicalEvidence.receiptDigest ≠ biologicalEvidence.receiptDigest ∧
  physicalEvidence.receiptDigest ≠ computationalOrganizationalEvidence.receiptDigest ∧
  biologicalEvidence.receiptDigest ≠ computationalOrganizationalEvidence.receiptDigest

/-- The first cross-domain gate: all three typed demonstrators must pass. -/
def CrossDomainEmpiricalGatePass
    (physicalContract : FrozenEmpiricalContract)
    (physicalEvidence : ReceiptBoundGateEvidence)
    (biologicalContract : FrozenEmpiricalContract)
    (biologicalEvidence : ReceiptBoundGateEvidence)
    (computationalOrganizationalContract : FrozenEmpiricalContract)
    (computationalOrganizationalEvidence : ReceiptBoundGateEvidence) : Prop :=
  CrossDomainEvidenceIndependent
      physicalEvidence biologicalEvidence computationalOrganizationalEvidence ∧
  DomainEmpiricalGatePass .physical physicalContract physicalEvidence ∧
  DomainEmpiricalGatePass .biological biologicalContract biologicalEvidence ∧
  DomainEmpiricalGatePass .computationalOrganizational
    computationalOrganizationalContract computationalOrganizationalEvidence

/-- A successful gate exposes the structural well-formedness of its contract. -/
theorem contractWellFormed_of_empiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence)
    (passed : EmpiricalGatePass contract evidence) :
    FrozenEmpiricalContractWellFormed contract :=
  passed.1

/-- A successful gate exposes the structural well-formedness of its receipt. -/
theorem evidenceWellFormed_of_empiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence)
    (passed : EmpiricalGatePass contract evidence) :
    ReceiptBoundGateEvidenceWellFormed evidence :=
  passed.2.1

/-- A malformed frozen contract cannot pass, even if its receipt copies empties. -/
theorem malformedContract_blocks_empiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence)
    (malformed : ¬ FrozenEmpiricalContractWellFormed contract) :
    ¬ EmpiricalGatePass contract evidence := by
  intro passed
  exact malformed passed.1

/-- A malformed receipt cannot pass, even if its fields match the contract. -/
theorem malformedEvidence_blocks_empiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence)
    (malformed : ¬ ReceiptBoundGateEvidenceWellFormed evidence) :
    ¬ EmpiricalGatePass contract evidence := by
  intro passed
  exact malformed passed.2.1

/-- Any preregistered falsifier blocks a domain pass. -/
theorem falsifier_blocks_empiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence)
    (triggered : evidence.falsifierTriggered = true) :
    ¬ EmpiricalGatePass contract evidence := by
  intro passed
  rcases passed.2.2.2 with
    ⟨_, _, _, _, _, _, notTriggered⟩
  rw [triggered] at notTriggered
  contradiction

/-- A declared decision statistic at or below its frozen threshold blocks pass. -/
theorem insufficientGain_blocks_empiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence)
    (insufficient : evidence.observedDecisionStatistic ≤ contract.decisionThreshold) :
    ¬ EmpiricalGatePass contract evidence := by
  intro passed
  exact (not_lt_of_ge insufficient) passed.2.2.2.1

/-- A failed preregistered group-direction requirement blocks the gate. -/
theorem failedGroupDirection_blocks_empiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence)
    (failed : evidence.groupDirectionPassed = false) :
    ¬ EmpiricalGatePass contract evidence := by
  intro passed
  rcases passed.2.2.2 with
    ⟨_, _, _, groupPassed, _, _, _⟩
  rw [failed] at groupPassed
  contradiction

/-- A successful gate exposes the exact contract identifier named by the receipt. -/
theorem receipt_contractId_matches_of_empiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence)
    (passed : EmpiricalGatePass contract evidence) :
    evidence.observedContractId = contract.contractId :=
  passed.2.2.1.2.2.1

/-- A receipt imported for a different contract cannot pass this contract's gate. -/
theorem contractId_mismatch_blocks_empiricalGatePass
    (contract : FrozenEmpiricalContract)
    (evidence : ReceiptBoundGateEvidence)
    (mismatch : evidence.observedContractId ≠ contract.contractId) :
    ¬ EmpiricalGatePass contract evidence := by
  intro passed
  exact mismatch (receipt_contractId_matches_of_empiricalGatePass contract evidence passed)

/-- Cross-domain support projects to each of its three independently typed lanes. -/
theorem crossDomainGatePass_components
    {physicalContract : FrozenEmpiricalContract}
    {physicalEvidence : ReceiptBoundGateEvidence}
    {biologicalContract : FrozenEmpiricalContract}
    {biologicalEvidence : ReceiptBoundGateEvidence}
    {computationalOrganizationalContract : FrozenEmpiricalContract}
    {computationalOrganizationalEvidence : ReceiptBoundGateEvidence}
    (passed : CrossDomainEmpiricalGatePass
      physicalContract physicalEvidence
      biologicalContract biologicalEvidence
      computationalOrganizationalContract computationalOrganizationalEvidence) :
    DomainEmpiricalGatePass .physical physicalContract physicalEvidence ∧
    DomainEmpiricalGatePass .biological biologicalContract biologicalEvidence ∧
    DomainEmpiricalGatePass .computationalOrganizational
      computationalOrganizationalContract computationalOrganizationalEvidence :=
  passed.2

/-- A cross-domain pass exposes pairwise-distinct receipt artifacts. -/
theorem crossDomainEvidenceIndependent_of_crossDomainGatePass
    {physicalContract : FrozenEmpiricalContract}
    {physicalEvidence : ReceiptBoundGateEvidence}
    {biologicalContract : FrozenEmpiricalContract}
    {biologicalEvidence : ReceiptBoundGateEvidence}
    {computationalOrganizationalContract : FrozenEmpiricalContract}
    {computationalOrganizationalEvidence : ReceiptBoundGateEvidence}
    (passed : CrossDomainEmpiricalGatePass
      physicalContract physicalEvidence
      biologicalContract biologicalEvidence
      computationalOrganizationalContract computationalOrganizationalEvidence) :
    CrossDomainEvidenceIndependent
      physicalEvidence biologicalEvidence computationalOrganizationalEvidence :=
  passed.1

/-- Reusing one receipt identifier across the physical and biological lanes blocks pass. -/
theorem sharedPhysicalBiologicalReceiptId_blocks_crossDomainGatePass
    (physicalContract : FrozenEmpiricalContract)
    (physicalEvidence : ReceiptBoundGateEvidence)
    (biologicalContract : FrozenEmpiricalContract)
    (biologicalEvidence : ReceiptBoundGateEvidence)
    (computationalOrganizationalContract : FrozenEmpiricalContract)
    (computationalOrganizationalEvidence : ReceiptBoundGateEvidence)
    (shared : physicalEvidence.receiptId = biologicalEvidence.receiptId) :
    ¬ CrossDomainEmpiricalGatePass
      physicalContract physicalEvidence
      biologicalContract biologicalEvidence
      computationalOrganizationalContract computationalOrganizationalEvidence := by
  intro passed
  exact passed.1.1 shared

/-- Reusing one receipt payload across the physical and biological lanes blocks pass. -/
theorem sharedPhysicalBiologicalReceiptDigest_blocks_crossDomainGatePass
    (physicalContract : FrozenEmpiricalContract)
    (physicalEvidence : ReceiptBoundGateEvidence)
    (biologicalContract : FrozenEmpiricalContract)
    (biologicalEvidence : ReceiptBoundGateEvidence)
    (computationalOrganizationalContract : FrozenEmpiricalContract)
    (computationalOrganizationalEvidence : ReceiptBoundGateEvidence)
    (shared : physicalEvidence.receiptDigest = biologicalEvidence.receiptDigest) :
    ¬ CrossDomainEmpiricalGatePass
      physicalContract physicalEvidence
      biologicalContract biologicalEvidence
      computationalOrganizationalContract computationalOrganizationalEvidence := by
  intro passed
  exact passed.1.2.2.2.1 shared

/--
Run a generic prequential predictor.  At each step the prediction from the
current state is emitted before the state is updated with the current
observation.  This sequencing theorem does not prove that the initial state or
either function was constructed without future-data leakage.
-/
def prequentialPredictions
    {State Observation Prediction : Type*}
    (predict : State → Prediction)
    (update : State → Observation → State)
    (state : State) : List Observation → List Prediction
  | [] => []
  | observation :: observations =>
      predict state ::
        prequentialPredictions predict update (update state observation) observations

/-- A prequential run emits exactly one prediction per observation. -/
@[simp] theorem prequentialPredictions_length
    {State Observation Prediction : Type*}
    (predict : State → Prediction)
    (update : State → Observation → State)
    (state : State)
    (observations : List Observation) :
    (prequentialPredictions predict update state observations).length =
      observations.length := by
  induction observations generalizing state with
  | nil => rfl
  | cons observation observations ih =>
      simp [prequentialPredictions, ih]

/-- The head prediction is emitted before the current observation updates state. -/
theorem prequentialPredictions_head_before_currentObservation
    {State Observation Prediction : Type*}
    (predict : State → Prediction)
    (update : State → Observation → State)
    (state : State)
    (observation : Observation)
    (observations : List Observation) :
    prequentialPredictions predict update state (observation :: observations) =
      predict state :: prequentialPredictions predict update
        (update state observation) observations :=
  rfl

/-- Appending future observations cannot change predictions on the fixed prefix. -/
theorem prequentialPredictions_prefixCausality
    {State Observation Prediction : Type*}
    (predict : State → Prediction)
    (update : State → Observation → State)
    (state : State)
    (past future : List Observation) :
    (prequentialPredictions predict update state (past ++ future)).take past.length =
      prequentialPredictions predict update state past := by
  induction past generalizing state with
  | nil => rfl
  | cons observation past ih =>
      simp [prequentialPredictions, ih]

/--
No rule using only the physical verdict can entail the three-domain verdict.
This finite countermodel is the formal boundary against empirical overclaim.
-/
theorem oneDomainPass_does_not_entail_allDomains :
    ¬ ∀ verdict : DemonstratorDomain → Bool,
      verdict .physical = true →
      ∀ domain, verdict domain = true := by
  intro alleged
  let verdict : DemonstratorDomain → Bool := fun domain =>
    decide (domain = .physical)
  have physicalPass : verdict .physical = true := by
    simp [verdict]
  have biologicalPass := alleged verdict physicalPass .biological
  simp [verdict] at biologicalPass

/-- Even two successful lanes do not entail the missing third lane. -/
theorem twoDomainPasses_do_not_entail_allDomains :
    ¬ ∀ verdict : DemonstratorDomain → Bool,
      verdict .physical = true →
      verdict .biological = true →
      ∀ domain, verdict domain = true := by
  intro alleged
  let verdict : DemonstratorDomain → Bool := fun domain =>
    decide (domain = .physical ∨ domain = .biological)
  have physicalPass : verdict .physical = true := by
    simp [verdict]
  have biologicalPass : verdict .biological = true := by
    simp [verdict]
  have computationalPass := alleged verdict physicalPass biologicalPass
    .computationalOrganizational
  simp [verdict] at computationalPass

end OCKIndividuationMSpaceComposition
