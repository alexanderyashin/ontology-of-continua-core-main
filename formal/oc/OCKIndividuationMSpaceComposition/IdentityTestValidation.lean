import OCKIndividuationMSpaceComposition.EmpiricalTheoryGate
import OCKIndividuationMSpaceComposition.QualifiedObjectHierarchy

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe uOccurrence uExperiment uOutcome

/-!
# Receipt-bound validation of constitutive identity tests

Formal convergence of `ForcedIdentity` and `AllowedIdentity` is a theorem
about supplied evidence and a supplied test law.  It does not establish that
the tests are empirically valid.  This module adds a separate frozen contract
and receipt surface for held-out invariance, separation, calibration,
continuity audit, controls and multiplicity.

Reference lineage labels remain operational reference evidence.  They are not
declared ontic ground truth.  A passing Boolean receipt proves only the
declared validation rule.  Equality with the formal identity relation follows
only through an explicit interpretation adapter whose two semantic
implications are additional evidence-bearing premises.
-/

/-! ## Frozen contract and evaluator receipt -/

structure FrozenIdentityTestValidationContract where
  contractId : String
  preregistrationDigest : String
  sourceBindingDigest : String
  testFamilyDigest : String
  referenceLineageSemanticsId : String
  splitDigest : String
  calibrationRuleId : String
  minimumIndependentUnits : Nat
  deriving Repr

def FrozenIdentityTestValidationContractWellFormed
    (contract : FrozenIdentityTestValidationContract) : Prop :=
  contract.contractId ≠ "" ∧
  contract.preregistrationDigest ≠ "" ∧
  contract.sourceBindingDigest ≠ "" ∧
  contract.testFamilyDigest ≠ "" ∧
  contract.referenceLineageSemanticsId ≠ "" ∧
  contract.splitDigest ≠ "" ∧
  contract.calibrationRuleId ≠ "" ∧
  0 < contract.minimumIndependentUnits

/-- Values imported from one sealed evaluator receipt.  Boolean fields are
deliberately structural; the adapter and external audit must establish that
they truthfully summarize the frozen run. -/
structure IdentityTestValidationReceipt where
  receiptId : String
  receiptDigest : String
  observedContractId : String
  observedPreregistrationDigest : String
  observedSourceBindingDigest : String
  observedTestFamilyDigest : String
  observedReferenceLineageSemanticsId : String
  observedSplitDigest : String
  observedCalibrationRuleId : String
  observedIndependentUnits : Nat
  heldOutSplitDisjoint : Bool
  outcomeFirewallIntact : Bool
  continuityAuditPassed : Bool
  invariancePassed : Bool
  separationPassed : Bool
  calibrationPassed : Bool
  negativeControlsPassed : Bool
  multiplicityControlPassed : Bool
  falsifierTriggered : Bool
  deriving Repr

def IdentityTestValidationReceiptWellFormed
    (receipt : IdentityTestValidationReceipt) : Prop :=
  receipt.receiptId ≠ "" ∧
  receipt.receiptDigest ≠ "" ∧
  receipt.observedContractId ≠ "" ∧
  receipt.observedPreregistrationDigest ≠ "" ∧
  receipt.observedSourceBindingDigest ≠ "" ∧
  receipt.observedTestFamilyDigest ≠ "" ∧
  receipt.observedReferenceLineageSemanticsId ≠ "" ∧
  receipt.observedSplitDigest ≠ "" ∧
  receipt.observedCalibrationRuleId ≠ ""

/-- Exact binding of every semantic and artifact identifier used by the
validation decision. -/
structure IdentityTestReceiptMatchesContract
    (contract : FrozenIdentityTestValidationContract)
    (receipt : IdentityTestValidationReceipt) : Prop where
  contractId : receipt.observedContractId = contract.contractId
  preregistration :
    receipt.observedPreregistrationDigest = contract.preregistrationDigest
  source : receipt.observedSourceBindingDigest = contract.sourceBindingDigest
  testFamily : receipt.observedTestFamilyDigest = contract.testFamilyDigest
  referenceSemantics :
    receipt.observedReferenceLineageSemanticsId =
      contract.referenceLineageSemanticsId
  split : receipt.observedSplitDigest = contract.splitDigest
  calibration : receipt.observedCalibrationRuleId = contract.calibrationRuleId

/-- The complete declared decision rule.  Equality at a strict threshold is
not silently promoted to a pass: enough units uses `≤`, while all qualitative
requirements must equal their exact passing Boolean. -/
structure IdentityTestValidationDecisionPass
    (contract : FrozenIdentityTestValidationContract)
    (receipt : IdentityTestValidationReceipt) : Prop where
  enoughIndependentUnits :
    contract.minimumIndependentUnits ≤ receipt.observedIndependentUnits
  heldOutSplitDisjoint : receipt.heldOutSplitDisjoint = true
  outcomeFirewallIntact : receipt.outcomeFirewallIntact = true
  continuityAuditPassed : receipt.continuityAuditPassed = true
  invariancePassed : receipt.invariancePassed = true
  separationPassed : receipt.separationPassed = true
  calibrationPassed : receipt.calibrationPassed = true
  negativeControlsPassed : receipt.negativeControlsPassed = true
  multiplicityControlPassed : receipt.multiplicityControlPassed = true
  noFalsifier : receipt.falsifierTriggered = false

/-- Lean-checkable validation certificate.  It does not read raw observations
or certify that the receipt adapter is scientifically adequate. -/
structure IdentityTestValidationPass
    (contract : FrozenIdentityTestValidationContract)
    (receipt : IdentityTestValidationReceipt) : Prop where
  contractWellFormed : FrozenIdentityTestValidationContractWellFormed contract
  receiptWellFormed : IdentityTestValidationReceiptWellFormed receipt
  receiptMatches : IdentityTestReceiptMatchesContract contract receipt
  decision : IdentityTestValidationDecisionPass contract receipt

theorem falsifier_blocks_identityTestValidation
    (contract : FrozenIdentityTestValidationContract)
    (receipt : IdentityTestValidationReceipt)
    (triggered : receipt.falsifierTriggered = true) :
  ¬ IdentityTestValidationPass contract receipt := by
  intro passed
  have noFalsifier := passed.decision.noFalsifier
  rw [triggered] at noFalsifier
  contradiction

theorem failedInvariance_blocks_identityTestValidation
    (contract : FrozenIdentityTestValidationContract)
    (receipt : IdentityTestValidationReceipt)
    (failed : receipt.invariancePassed = false) :
  ¬ IdentityTestValidationPass contract receipt := by
  intro passed
  have invariancePassed := passed.decision.invariancePassed
  rw [failed] at invariancePassed
  contradiction

theorem failedSeparation_blocks_identityTestValidation
    (contract : FrozenIdentityTestValidationContract)
    (receipt : IdentityTestValidationReceipt)
    (failed : receipt.separationPassed = false) :
  ¬ IdentityTestValidationPass contract receipt := by
  intro passed
  have separationPassed := passed.decision.separationPassed
  rw [failed] at separationPassed
  contradiction

/-! ## Reference labels and the semantic interpretation adapter -/

/-- Operational reference lineage evidence, with exact external semantics and
source bindings.  The structure name intentionally avoids `GroundTruth`. -/
structure ReferenceLineageEvidence (Occurrence : Type uOccurrence) where
  relation : BinaryRelation Occurrence
  semanticsId : String
  sourceDigest : String

/-- External interpretation of the two Boolean validation results.  These
implications cannot be generated from receipt strings by Lean: they must be
justified by the domain adapter, sampling design and scientific audit. -/
structure IdentityTestReferenceInterpretation
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {Outcome : Type uOutcome}
    (contract : FrozenIdentityTestValidationContract)
    (receipt : IdentityTestValidationReceipt)
    (law : Occurrence → Experiment → Outcome)
    (reference : ReferenceLineageEvidence Occurrence) : Prop where
  semanticsBound : reference.semanticsId = contract.referenceLineageSemanticsId
  sourceBound : reference.sourceDigest = contract.sourceBindingDigest
  invarianceSound : receipt.invariancePassed = true →
    RelationRefines reference.relation (AllowedIdentity law)
  separationSound : receipt.separationPassed = true →
    RelationRefines (AllowedIdentity law) reference.relation

/-- Conditional soundness: a passing receipt plus an explicit interpretation
adapter makes the declared test equivalence coincide with the operational
reference lineage relation. -/
theorem validated_allowedIdentity_eq_referenceLineage
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {Outcome : Type uOutcome}
    {law : Occurrence → Experiment → Outcome}
    {contract : FrozenIdentityTestValidationContract}
    {receipt : IdentityTestValidationReceipt}
    {reference : ReferenceLineageEvidence Occurrence}
    (passed : IdentityTestValidationPass contract receipt)
    (interpretation : IdentityTestReferenceInterpretation
      contract receipt law reference) :
    AllowedIdentity law = reference.relation := by
  have referenceToAllowed :=
    interpretation.invarianceSound passed.decision.invariancePassed
  have allowedToReference :=
    interpretation.separationSound passed.decision.separationPassed
  funext first second
  apply propext
  constructor
  · intro allowed
    exact allowedToReference allowed
  · intro referenced
    exact referenceToAllowed referenced

/-- If the formal forced/allowed bounds also converge, the mathematical token
relation agrees with the operational reference relation.  The conclusion is
still relative to that reference semantics; it is not an ontic-truth theorem. -/
theorem validated_forcedIdentity_eq_referenceLineage
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {Outcome : Type uOutcome}
    {evidence : BinaryRelation Occurrence}
    {law : Occurrence → Experiment → Outcome}
    {contract : FrozenIdentityTestValidationContract}
    {receipt : IdentityTestValidationReceipt}
    {reference : ReferenceLineageEvidence Occurrence}
    (convergence : ForcedIdentity evidence = AllowedIdentity law)
    (passed : IdentityTestValidationPass contract receipt)
    (interpretation : IdentityTestReferenceInterpretation
      contract receipt law reference) :
    ForcedIdentity evidence = reference.relation :=
  convergence.trans
    (validated_allowedIdentity_eq_referenceLineage passed interpretation)

/-- Receipt success alone cannot select between distinct ontic identity
hypotheses.  Any such selection requires a further premise relating the
operational reference to the intended ontology. -/
theorem validationPass_does_not_choose_onticGroundTruth
    {contract : FrozenIdentityTestValidationContract}
    {receipt : IdentityTestValidationReceipt}
    (passed : IdentityTestValidationPass contract receipt)
    {Occurrence : Type uOccurrence}
    {firstHypothesis secondHypothesis : BinaryRelation Occurrence}
    (different : firstHypothesis ≠ secondHypothesis) :
    IdentityTestValidationPass contract receipt ∧
      firstHypothesis ≠ secondHypothesis :=
  ⟨passed, different⟩

/-! ## Authoritative typed specification binding -/

/-- One typed identity-test specification owns the evidence relation, complete
test law, operational reference and every semantic binding used by a frozen
validation run.  Contract, receipt and interpretation below are all indexed by
this same value, so those objects cannot silently substitute a different law
or evidence relation. -/
structure BoundIdentityTestSpecification
    (Occurrence : Type uOccurrence)
    (Experiment : Type uExperiment)
    (Outcome : Type uOutcome) where
  specificationId : String
  validationContractId : String
  preregistrationDigest : String
  sourceBindingDigest : String
  testFamilyDigest : String
  referenceLineageSemanticsId : String
  splitDigest : String
  calibrationRuleId : String
  minimumIndependentUnits : Nat
  evidence : BinaryRelation Occurrence
  law : Occurrence → Experiment → Outcome
  reference : ReferenceLineageEvidence Occurrence
  referenceSemantics_bound :
    reference.semanticsId = referenceLineageSemanticsId
  referenceSource_bound : reference.sourceDigest = sourceBindingDigest

/-- Frozen string-level contract, propositionally tied to one typed
specification. -/
structure BoundFrozenIdentityTestValidationContract
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {Outcome : Type uOutcome}
    (specification :
      BoundIdentityTestSpecification Occurrence Experiment Outcome) where
  base : FrozenIdentityTestValidationContract
  contractId_bound : base.contractId = specification.validationContractId
  preregistration_bound :
    base.preregistrationDigest = specification.preregistrationDigest
  source_bound : base.sourceBindingDigest = specification.sourceBindingDigest
  testFamily_bound : base.testFamilyDigest = specification.testFamilyDigest
  referenceSemantics_bound :
    base.referenceLineageSemanticsId =
      specification.referenceLineageSemanticsId
  split_bound : base.splitDigest = specification.splitDigest
  calibration_bound : base.calibrationRuleId = specification.calibrationRuleId
  minimumUnits_bound :
    base.minimumIndependentUnits = specification.minimumIndependentUnits

/-- Sealed evaluator receipt, propositionally tied to the same typed
specification as the contract. -/
structure BoundIdentityTestValidationReceipt
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {Outcome : Type uOutcome}
    (specification :
      BoundIdentityTestSpecification Occurrence Experiment Outcome) where
  base : IdentityTestValidationReceipt
  observedSpecificationId : String
  specificationId_bound :
    observedSpecificationId = specification.specificationId
  contractId_bound :
    base.observedContractId = specification.validationContractId
  preregistration_bound :
    base.observedPreregistrationDigest = specification.preregistrationDigest
  source_bound :
    base.observedSourceBindingDigest = specification.sourceBindingDigest
  testFamily_bound :
    base.observedTestFamilyDigest = specification.testFamilyDigest
  referenceSemantics_bound :
    base.observedReferenceLineageSemanticsId =
      specification.referenceLineageSemanticsId
  split_bound : base.observedSplitDigest = specification.splitDigest
  calibration_bound :
    base.observedCalibrationRuleId = specification.calibrationRuleId

/-- The Lean checker still checks only the declared receipt predicate.  The
dependent indices guarantee identity of the typed specification; they do not
attest the raw observations or the scientific validity of the adapter. -/
structure BoundIdentityTestValidationPass
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {Outcome : Type uOutcome}
    {specification :
      BoundIdentityTestSpecification Occurrence Experiment Outcome}
    (contract : BoundFrozenIdentityTestValidationContract specification)
    (receipt : BoundIdentityTestValidationReceipt specification) : Prop where
  basePass : IdentityTestValidationPass contract.base receipt.base

/-- Semantic interpretation over the exact law and reference owned by the
shared typed specification. -/
structure BoundIdentityTestReferenceInterpretation
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {Outcome : Type uOutcome}
    (specification :
      BoundIdentityTestSpecification Occurrence Experiment Outcome)
    (contract : BoundFrozenIdentityTestValidationContract specification)
    (receipt : BoundIdentityTestValidationReceipt specification) : Prop where
  invarianceSound : receipt.base.invariancePassed = true →
    RelationRefines specification.reference.relation
      (AllowedIdentity specification.law)
  separationSound : receipt.base.separationPassed = true →
    RelationRefines (AllowedIdentity specification.law)
      specification.reference.relation

/-- Conditional semantic soundness for the law/reference pair that is actually
bound into contract and receipt. -/
theorem bound_validated_allowedIdentity_eq_referenceLineage
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {Outcome : Type uOutcome}
    {specification :
      BoundIdentityTestSpecification Occurrence Experiment Outcome}
    {contract : BoundFrozenIdentityTestValidationContract specification}
    {receipt : BoundIdentityTestValidationReceipt specification}
    (passed : BoundIdentityTestValidationPass contract receipt)
    (interpretation : BoundIdentityTestReferenceInterpretation
      specification contract receipt) :
    AllowedIdentity specification.law =
      specification.reference.relation := by
  have referenceToAllowed := interpretation.invarianceSound
    passed.basePass.decision.invariancePassed
  have allowedToReference := interpretation.separationSound
    passed.basePass.decision.separationPassed
  funext first second
  apply propext
  constructor
  · intro allowed
    exact allowedToReference allowed
  · intro referenced
    exact referenceToAllowed referenced

/-- Forced/allowed convergence uses the evidence and law from the same typed
specification; neither may float as an independent theorem parameter. -/
theorem bound_validated_forcedIdentity_eq_referenceLineage
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {Outcome : Type uOutcome}
    {specification :
      BoundIdentityTestSpecification Occurrence Experiment Outcome}
    {contract : BoundFrozenIdentityTestValidationContract specification}
    {receipt : BoundIdentityTestValidationReceipt specification}
    (convergence :
      ForcedIdentity specification.evidence =
        AllowedIdentity specification.law)
    (passed : BoundIdentityTestValidationPass contract receipt)
    (interpretation : BoundIdentityTestReferenceInterpretation
      specification contract receipt) :
    ForcedIdentity specification.evidence =
      specification.reference.relation :=
  convergence.trans
    (bound_validated_allowedIdentity_eq_referenceLineage
      passed interpretation)

/-! ## Explicit Boolean/string-only countermodel -/

def booleanOnlyReferenceLineage : ReferenceLineageEvidence Bool where
  relation := fun first second => first = second
  semanticsId := "operational-bool-equality"
  sourceDigest := "synthetic-source"

def booleanOnlyIdentityTestSpecification :
    BoundIdentityTestSpecification Bool Unit Unit where
  specificationId := "boolean-only-specification"
  validationContractId := "boolean-only-contract"
  preregistrationDigest := "synthetic-preregistration"
  sourceBindingDigest := "synthetic-source"
  testFamilyDigest := "constant-unit-law"
  referenceLineageSemanticsId := "operational-bool-equality"
  splitDigest := "synthetic-split"
  calibrationRuleId := "synthetic-calibration"
  minimumIndependentUnits := 1
  evidence := fun first second => first = second
  law := fun _ _ => ()
  reference := booleanOnlyReferenceLineage
  referenceSemantics_bound := rfl
  referenceSource_bound := rfl

def booleanOnlyBoundContract :
    BoundFrozenIdentityTestValidationContract
      booleanOnlyIdentityTestSpecification where
  base := {
    contractId := "boolean-only-contract"
    preregistrationDigest := "synthetic-preregistration"
    sourceBindingDigest := "synthetic-source"
    testFamilyDigest := "constant-unit-law"
    referenceLineageSemanticsId := "operational-bool-equality"
    splitDigest := "synthetic-split"
    calibrationRuleId := "synthetic-calibration"
    minimumIndependentUnits := 1
  }
  contractId_bound := rfl
  preregistration_bound := rfl
  source_bound := rfl
  testFamily_bound := rfl
  referenceSemantics_bound := rfl
  split_bound := rfl
  calibration_bound := rfl
  minimumUnits_bound := rfl

def booleanOnlyBoundReceipt :
    BoundIdentityTestValidationReceipt
      booleanOnlyIdentityTestSpecification where
  base := {
    receiptId := "boolean-only-receipt"
    receiptDigest := "synthetic-receipt-digest"
    observedContractId := "boolean-only-contract"
    observedPreregistrationDigest := "synthetic-preregistration"
    observedSourceBindingDigest := "synthetic-source"
    observedTestFamilyDigest := "constant-unit-law"
    observedReferenceLineageSemanticsId := "operational-bool-equality"
    observedSplitDigest := "synthetic-split"
    observedCalibrationRuleId := "synthetic-calibration"
    observedIndependentUnits := 1
    heldOutSplitDisjoint := true
    outcomeFirewallIntact := true
    continuityAuditPassed := true
    invariancePassed := true
    separationPassed := true
    calibrationPassed := true
    negativeControlsPassed := true
    multiplicityControlPassed := true
    falsifierTriggered := false
  }
  observedSpecificationId := "boolean-only-specification"
  specificationId_bound := rfl
  contractId_bound := rfl
  preregistration_bound := rfl
  source_bound := rfl
  testFamily_bound := rfl
  referenceSemantics_bound := rfl
  split_bound := rfl
  calibration_bound := rfl

def booleanOnlyBoundPass :
    BoundIdentityTestValidationPass booleanOnlyBoundContract
      booleanOnlyBoundReceipt where
  basePass := {
    contractWellFormed := by
      simp [FrozenIdentityTestValidationContractWellFormed,
        booleanOnlyBoundContract]
    receiptWellFormed := by
      simp [IdentityTestValidationReceiptWellFormed,
        booleanOnlyBoundReceipt]
    receiptMatches := {
      contractId := rfl
      preregistration := rfl
      source := rfl
      testFamily := rfl
      referenceSemantics := rfl
      split := rfl
      calibration := rfl
    }
    decision := {
      enoughIndependentUnits := by decide
      heldOutSplitDisjoint := rfl
      outcomeFirewallIntact := rfl
      continuityAuditPassed := rfl
      invariancePassed := rfl
      separationPassed := rfl
      calibrationPassed := rfl
      negativeControlsPassed := rfl
      multiplicityControlPassed := rfl
      noFalsifier := rfl
    }
  }

/-- Concrete separation of syntactic receipt success from semantic validity:
all strings and Booleans pass, yet the constant test law cannot separate the
two Boolean occurrences and therefore cannot validate equality lineage. -/
theorem strings_and_booleans_alone_do_not_validate_identity_semantics :
    BoundIdentityTestValidationPass booleanOnlyBoundContract
        booleanOnlyBoundReceipt ∧
      ¬ BoundIdentityTestReferenceInterpretation
        booleanOnlyIdentityTestSpecification booleanOnlyBoundContract
        booleanOnlyBoundReceipt := by
  constructor
  · exact booleanOnlyBoundPass
  · intro interpretation
    have allowedToReference :=
      interpretation.separationSound (by rfl)
    have allowed :
        AllowedIdentity booleanOnlyIdentityTestSpecification.law false true := by
      intro experiment
      cases experiment
      rfl
    have referenceEdge := allowedToReference allowed
    change false = true at referenceEdge
    exact Bool.false_ne_true referenceEdge

end OCKIndividuationMSpaceComposition
