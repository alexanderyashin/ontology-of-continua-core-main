import OCKIndividuationMSpaceComposition.FiniteAdapterAutotuning

namespace OCKIndividuationMSpaceComposition

/-!
# Experimental epistemology and scientific-instrument identity

This module formalizes the stable mathematical core of relational exposure.
It deliberately excludes registry storage, timestamps and workflow policy.
-/

/-- Content-addressed scientific instrument components are represented here by
their immutable identities. -/
structure ScientificInstrumentInstance where
  adapterDefinitionId : String
  adapterConfigurationId : String
  calibrationStateId : String
  coreRevisionId : String
  domainAdapterId : String
  observationAdapterId : String
  taskLossId : String
  protocolId : String
  runnerId : String
  deriving DecidableEq

/-- Canonical scientific observation cell.  A shared physical source is only
one coordinate of its identity. -/
structure ScientificExperimentCell where
  sourceId : String
  segmentId : String
  instrument : ScientificInstrumentInstance
  targetId : String
  horizonId : String
  projectionId : String
  carrierBindingId : String
  splitBlockId : String
  comparatorSetId : String
  lossUtilityId : String
  deriving DecidableEq

namespace ScientificInstrumentInstance

/-- Changing fitted state changes the instrument even when the adapter
definition and configuration are unchanged. -/
theorem ne_of_calibrationStateId_ne
    {first second : ScientificInstrumentInstance}
    (different : first.calibrationStateId ≠ second.calibrationStateId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

end ScientificInstrumentInstance

namespace ScientificExperimentCell

/-- T2: different registered settings force different experiment-cell
identities. -/
theorem ne_of_adapterConfigurationId_ne
    {first second : ScientificExperimentCell}
    (different : first.instrument.adapterConfigurationId ≠
      second.instrument.adapterConfigurationId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

end ScientificExperimentCell

def toyInstrumentAt (configuration : String) : ScientificInstrumentInstance where
  adapterDefinitionId := "A"
  adapterConfigurationId := configuration
  calibrationStateId := "fit"
  coreRevisionId := "core"
  domainAdapterId := "domain"
  observationAdapterId := "observe"
  taskLossId := "task"
  protocolId := "protocol"
  runnerId := "runner"

def toyCellAt (configuration : String) : ScientificExperimentCell where
  sourceId := "same-source"
  segmentId := "same-segment"
  instrument := toyInstrumentAt configuration
  targetId := "target"
  horizonId := "horizon"
  projectionId := "projection"
  carrierBindingId := "carrier"
  splitBlockId := "split"
  comparatorSetId := "comparators"
  lossUtilityId := "loss"

/-- T1 with witness: the same dataset/source can contain distinct experiments. -/
theorem same_source_does_not_imply_same_experiment :
    (toyCellAt "theta-1").sourceId = (toyCellAt "theta-2").sourceId ∧
      toyCellAt "theta-1" ≠ toyCellAt "theta-2" := by
  constructor
  · rfl
  · exact ScientificExperimentCell.ne_of_adapterConfigurationId_ne (by decide)

/-! ## Relational exposure and claim-relative evidence -/

/-- Exposure is attached to a claim, artifact/instrument, source and segment;
the Boolean scientific facts are deliberately separate coordinates. -/
structure ScientificExposureRelation where
  claimId : String
  artifactId : String
  instrumentId : String
  sourceId : String
  segmentId : String
  sourceSeen : Bool
  schemaSeen : Bool
  inputSeen : Bool
  outcomeSeen : Bool
  usedForDevelopment : Bool
  exactCellNovel : Bool
  outcomesInfluencedInstrument : Bool
  frozenBeforeSegmentOutcome : Bool
  prospectiveAtFreeze : Bool
  newTargetSource : Bool
  unchangedInstrument : Bool
  targetRecalibrated : Bool
  independentSourceLineage : Bool
  independentDomainLineage : Bool
  temporalDependenceDeclared : Bool
  deriving DecidableEq

def ScientificExposureRelation.independentConfirmation
    (exposure : ScientificExposureRelation) : Prop :=
  exposure.independentSourceLineage = true ∧
    exposure.independentDomainLineage = true ∧
    exposure.outcomesInfluencedInstrument = false

def ScientificExposureRelation.developmentEvidence
    (exposure : ScientificExposureRelation) : Prop :=
  exposure.sourceSeen = true ∧ exposure.usedForDevelopment = true

def ScientificExposureRelation.prospectiveTemporalEvidence
    (exposure : ScientificExposureRelation) : Prop :=
  exposure.frozenBeforeSegmentOutcome = true ∧
    exposure.prospectiveAtFreeze = true ∧
    exposure.temporalDependenceDeclared = true

def ScientificExposureRelation.zeroShotTransferEvidence
    (exposure : ScientificExposureRelation) : Prop :=
  exposure.newTargetSource = true ∧
    exposure.unchangedInstrument = true ∧
    exposure.targetRecalibrated = false

/-- T3: exact-cell novelty cannot rescue independent confirmation when the
target outcomes influenced the instrument lineage. -/
theorem influenced_novel_cell_is_not_independent
    (exposure : ScientificExposureRelation)
    (influenced : exposure.outcomesInfluencedInstrument = true) :
    ¬ exposure.independentConfirmation := by
  intro independent
  have notInfluenced : exposure.outcomesInfluencedInstrument = false := independent.2.2
  simp_all

def schemaOnlyExposure : ScientificExposureRelation where
  claimId := "claim"
  artifactId := "artifact"
  instrumentId := "instrument"
  sourceId := "source"
  segmentId := "segment"
  sourceSeen := true
  schemaSeen := true
  inputSeen := false
  outcomeSeen := false
  usedForDevelopment := false
  exactCellNovel := true
  outcomesInfluencedInstrument := false
  frozenBeforeSegmentOutcome := false
  prospectiveAtFreeze := false
  newTargetSource := false
  unchangedInstrument := false
  targetRecalibrated := false
  independentSourceLineage := false
  independentDomainLineage := false
  temporalDependenceDeclared := false

/-- T4 with witness: source and schema exposure do not imply outcome exposure. -/
theorem source_schema_exposure_does_not_imply_outcome :
    schemaOnlyExposure.sourceSeen = true ∧
      schemaOnlyExposure.schemaSeen = true ∧
      schemaOnlyExposure.outcomeSeen = false := by
  decide

/-- T5: an exposed source remains valid for declared development use.  This is
not an independent-confirmation claim. -/
theorem exposed_source_can_remain_development_evidence
    (exposure : ScientificExposureRelation)
    (seen : exposure.sourceSeen = true)
    (development : exposure.usedForDevelopment = true) :
    exposure.developmentEvidence :=
  ⟨seen, development⟩

/-- T6: an untouched future segment can support prospective temporal evidence
when freeze and temporal-dependence qualification are explicit. -/
theorem future_segment_can_be_prospective
    (exposure : ScientificExposureRelation)
    (frozen : exposure.frozenBeforeSegmentOutcome = true)
    (future : exposure.prospectiveAtFreeze = true)
    (dependenceDeclared : exposure.temporalDependenceDeclared = true) :
    exposure.prospectiveTemporalEvidence :=
  ⟨frozen, future, dependenceDeclared⟩

/-! ## Controlled contrasts and transfer strength -/

/-- A pair of cells identifies a registered factor only after nuisance
equivalence is supplied; equality of all other relevant coordinates is not
manufactured from the result difference. -/
structure RegisteredFactorContrast
    (first second : ScientificExperimentCell) where
  registeredFactorDifferent :
    first.instrument.adapterConfigurationId ≠
      second.instrument.adapterConfigurationId
  nuisanceEquivalent :
    first.sourceId = second.sourceId ∧
    first.segmentId = second.segmentId ∧
    first.targetId = second.targetId ∧
    first.horizonId = second.horizonId ∧
    first.projectionId = second.projectionId ∧
    first.carrierBindingId = second.carrierBindingId ∧
    first.splitBlockId = second.splitBlockId ∧
    first.comparatorSetId = second.comparatorSetId ∧
    first.lossUtilityId = second.lossUtilityId

/-- T7: a qualified one-factor contrast really does contain a distinct
configuration and the declared nuisance equivalences. -/
theorem registered_factor_contrast_identifies_declared_difference
    {first second : ScientificExperimentCell}
    (contrast : RegisteredFactorContrast first second) :
    first ≠ second ∧
      first.sourceId = second.sourceId ∧
      first.segmentId = second.segmentId := by
  exact ⟨ScientificExperimentCell.ne_of_adapterConfigurationId_ne
    contrast.registeredFactorDifferent,
    contrast.nuisanceEquivalent.1,
    contrast.nuisanceEquivalent.2.1⟩

/-- T10: unchanged cross-source application is zero-shot evidence, whereas a
locally recalibrated target is not the same evidence claim. -/
theorem unchanged_settings_are_zeroShot_not_local_recalibration
    (exposure : ScientificExposureRelation)
    (newSource : exposure.newTargetSource = true)
    (unchanged : exposure.unchangedInstrument = true)
    (notRetuned : exposure.targetRecalibrated = false) :
    exposure.zeroShotTransferEvidence :=
  ⟨newSource, unchanged, notRetuned⟩

end OCKIndividuationMSpaceComposition
