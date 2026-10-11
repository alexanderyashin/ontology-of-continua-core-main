import OCKIndividuationMSpaceComposition.BridgeOntologyHypergraph
import Mathlib.Data.Fintype.EquivFin
import Mathlib.Data.Fintype.OfMap

namespace OCKIndividuationMSpaceComposition

/-!
Finite, typed representation of the complete Logion bridge-rule denominator.

This module does not prove that an arbitrary empirical candidate satisfies a
rule.  It proves that the frozen conversion vocabulary itself is finite,
exhaustive, non-duplicated, typed, loss-accounted and equipped with an explicit
reverse policy.  Candidate admission remains evidence- and cut-relative.
-/

inductive BridgeOntologyId where
  | bo01 | bo02 | bo03 | bo04 | bo05 | bo06 | bo07
  | bo08 | bo09 | bo10 | bo11 | bo12 | bo13
deriving DecidableEq, Repr

inductive BridgeRuleId where
  | bor01 | bor02 | bor03 | bor04 | bor05
  | bor06 | bor07 | bor08 | bor09 | bor10
  | bor11 | bor12 | bor13 | bor14 | bor15
  | bor16 | bor17 | bor18 | bor19 | bor20
  | bor21 | bor22 | bor23 | bor24 | bor25
deriving DecidableEq, Repr

inductive MappingFamily where
  | logicalObjectToContract
  | logicalObjectToTechnicalPassport
  | logicalObjectToSemanticPassport
  | logicalObjectToPhysicalRealization
  | contractToPhysicalRealization
  | contractToTestSuite
  | testSuiteToTestOccurrence
  | physicalGenerationToHotCopy
  | physicalGenerationToRemoteBackup
  | physicalGenerationToHddArchive
  | copyToRestoreCanary
  | functionalAssetToProcessStep
  | functionalAssetToDataAssetInteraction
  | processStepToInterfacePort
  | variableToObservationSource
  | scientificResultToReaderClaim
  | readerClaimToPublicationAtom
  | physicalGenerationToRuntimeOccurrence
  | processDefinitionToProcessOccurrence
  | interfacePortToSignalTransfer
  | governanceDecisionToSubjectScope
  | changeOccurrenceToAffectedGeneration
  | ontologySubjectToRootAssetSubject
  | evidenceOccurrenceToAssertion
  | contractToProcessDefinition
deriving DecidableEq, Repr

inductive OntologyRole where
  | logicalObject | contract | technicalPassport | semanticPassport
  | physicalArtifact | testSuite | testOccurrence | persistenceHotCopy
  | persistenceRemoteCopy | persistenceArchiveCopy | persistenceCopy
  | restoreOccurrence
  | functionalAsset | processStep | dataAsset | interfacePort | variable
  | observationSource | scientificResult | readerClaim | publicationAtom
  | runtimeOccurrence | processDefinition | processOccurrence
  | signalTransfer | governanceDecision | changeOccurrence
  | ontologyLocalSubject | rootAssetSubject | logicalOrPhysicalGeneration
  | evidenceOccurrence | assertion
deriving DecidableEq, Repr

inductive BridgeClass where
  | partialCorrespondence | observation | realization
  | faithfulEmbedding | abstractionQuotient
deriving DecidableEq, Repr

inductive BridgeDirection where
  | forwardOnly | bidirectionalScoped
deriving DecidableEq, Repr

inductive RoundTripClass where
  | none | setValued | taskEquivalent | exactOnVerifiedImage
deriving DecidableEq, Repr

inductive ReverseMode where
  | noReverse | evidenceReferencesOnly | typedCandidateSet
  | taskRelative | exactOnVerifiedImage
deriving DecidableEq, Repr

structure BridgeRuleSpec where
  bridgeOntology : BridgeOntologyId
  family : MappingFamily
  source : OntologyRole
  target : OntologyRole
  bridgeClass : BridgeClass
  direction : BridgeDirection
  roundTrip : RoundTripClass
  reverseMode : ReverseMode
deriving DecidableEq, Repr

def allBridgeOntologyIds : List BridgeOntologyId :=
  [.bo01, .bo02, .bo03, .bo04, .bo05, .bo06, .bo07,
   .bo08, .bo09, .bo10, .bo11, .bo12, .bo13]

instance : Fintype BridgeOntologyId :=
  Fintype.ofList allBridgeOntologyIds (by
    intro value
    cases value <;> simp [allBridgeOntologyIds])

def allBridgeRuleIds : List BridgeRuleId :=
  [.bor01, .bor02, .bor03, .bor04, .bor05,
   .bor06, .bor07, .bor08, .bor09, .bor10,
   .bor11, .bor12, .bor13, .bor14, .bor15,
   .bor16, .bor17, .bor18, .bor19, .bor20,
   .bor21, .bor22, .bor23, .bor24, .bor25]

instance : Fintype BridgeRuleId :=
  Fintype.ofList allBridgeRuleIds (by
    intro value
    cases value <;> simp [allBridgeRuleIds])

def allMappingFamilies : List MappingFamily :=
  [.logicalObjectToContract,
   .logicalObjectToTechnicalPassport,
   .logicalObjectToSemanticPassport,
   .logicalObjectToPhysicalRealization,
   .contractToPhysicalRealization,
   .contractToTestSuite,
   .testSuiteToTestOccurrence,
   .physicalGenerationToHotCopy,
   .physicalGenerationToRemoteBackup,
   .physicalGenerationToHddArchive,
   .copyToRestoreCanary,
   .functionalAssetToProcessStep,
   .functionalAssetToDataAssetInteraction,
   .processStepToInterfacePort,
   .variableToObservationSource,
   .scientificResultToReaderClaim,
   .readerClaimToPublicationAtom,
   .physicalGenerationToRuntimeOccurrence,
   .processDefinitionToProcessOccurrence,
   .interfacePortToSignalTransfer,
   .governanceDecisionToSubjectScope,
   .changeOccurrenceToAffectedGeneration,
   .ontologySubjectToRootAssetSubject,
   .evidenceOccurrenceToAssertion,
   .contractToProcessDefinition]

instance : Fintype MappingFamily :=
  Fintype.ofList allMappingFamilies (by
    intro value
    cases value <;> simp [allMappingFamilies])

def bridgeRuleSpec : BridgeRuleId → BridgeRuleSpec
  | .bor01 => ⟨.bo02, .logicalObjectToContract, .logicalObject, .contract,
      .partialCorrespondence, .bidirectionalScoped, .setValued, .typedCandidateSet⟩
  | .bor02 => ⟨.bo03, .logicalObjectToTechnicalPassport, .logicalObject,
      .technicalPassport, .partialCorrespondence, .bidirectionalScoped,
      .setValued, .typedCandidateSet⟩
  | .bor03 => ⟨.bo03, .logicalObjectToSemanticPassport, .logicalObject,
      .semanticPassport, .observation, .bidirectionalScoped, .taskEquivalent,
      .taskRelative⟩
  | .bor04 => ⟨.bo01, .logicalObjectToPhysicalRealization, .logicalObject,
      .physicalArtifact, .realization, .bidirectionalScoped,
      .exactOnVerifiedImage, .exactOnVerifiedImage⟩
  | .bor05 => ⟨.bo01, .contractToPhysicalRealization, .contract,
      .physicalArtifact, .partialCorrespondence, .bidirectionalScoped,
      .taskEquivalent, .taskRelative⟩
  | .bor06 => ⟨.bo04, .contractToTestSuite, .contract, .testSuite,
      .partialCorrespondence, .bidirectionalScoped, .setValued, .typedCandidateSet⟩
  | .bor07 => ⟨.bo04, .testSuiteToTestOccurrence, .testSuite, .testOccurrence,
      .faithfulEmbedding, .forwardOnly, .exactOnVerifiedImage, .exactOnVerifiedImage⟩
  | .bor08 => ⟨.bo05, .physicalGenerationToHotCopy, .physicalArtifact,
      .persistenceHotCopy, .realization, .bidirectionalScoped, .taskEquivalent,
      .taskRelative⟩
  | .bor09 => ⟨.bo05, .physicalGenerationToRemoteBackup, .physicalArtifact,
      .persistenceRemoteCopy, .realization, .bidirectionalScoped, .taskEquivalent,
      .taskRelative⟩
  | .bor10 => ⟨.bo05, .physicalGenerationToHddArchive, .physicalArtifact,
      .persistenceArchiveCopy, .realization, .bidirectionalScoped, .taskEquivalent,
      .taskRelative⟩
  | .bor11 => ⟨.bo05, .copyToRestoreCanary, .persistenceCopy,
      .restoreOccurrence, .faithfulEmbedding, .forwardOnly, .exactOnVerifiedImage,
      .exactOnVerifiedImage⟩
  | .bor12 => ⟨.bo06, .functionalAssetToProcessStep, .functionalAsset,
      .processStep, .partialCorrespondence, .bidirectionalScoped, .setValued,
      .typedCandidateSet⟩
  | .bor13 => ⟨.bo07, .functionalAssetToDataAssetInteraction, .functionalAsset,
      .dataAsset, .observation, .bidirectionalScoped, .setValued, .typedCandidateSet⟩
  | .bor14 => ⟨.bo08, .processStepToInterfacePort, .processStep, .interfacePort,
      .faithfulEmbedding, .bidirectionalScoped, .exactOnVerifiedImage,
      .exactOnVerifiedImage⟩
  | .bor15 => ⟨.bo09, .variableToObservationSource, .variable,
      .observationSource, .observation, .forwardOnly, .setValued,
      .evidenceReferencesOnly⟩
  | .bor16 => ⟨.bo10, .scientificResultToReaderClaim, .scientificResult,
      .readerClaim, .abstractionQuotient, .forwardOnly, .none, .noReverse⟩
  | .bor17 => ⟨.bo10, .readerClaimToPublicationAtom, .readerClaim,
      .publicationAtom, .realization, .bidirectionalScoped, .taskEquivalent,
      .taskRelative⟩
  | .bor18 => ⟨.bo11, .physicalGenerationToRuntimeOccurrence, .physicalArtifact,
      .runtimeOccurrence, .observation, .forwardOnly, .exactOnVerifiedImage,
      .exactOnVerifiedImage⟩
  | .bor19 => ⟨.bo11, .processDefinitionToProcessOccurrence, .processDefinition,
      .processOccurrence, .faithfulEmbedding, .forwardOnly, .exactOnVerifiedImage,
      .exactOnVerifiedImage⟩
  | .bor20 => ⟨.bo11, .interfacePortToSignalTransfer, .interfacePort,
      .signalTransfer, .observation, .forwardOnly, .exactOnVerifiedImage,
      .exactOnVerifiedImage⟩
  | .bor21 => ⟨.bo12, .governanceDecisionToSubjectScope, .governanceDecision,
      .rootAssetSubject, .partialCorrespondence, .bidirectionalScoped, .setValued,
      .typedCandidateSet⟩
  | .bor22 => ⟨.bo12, .changeOccurrenceToAffectedGeneration, .changeOccurrence,
      .logicalOrPhysicalGeneration, .partialCorrespondence, .bidirectionalScoped, .setValued,
      .typedCandidateSet⟩
  | .bor23 => ⟨.bo13, .ontologySubjectToRootAssetSubject, .ontologyLocalSubject,
      .rootAssetSubject, .partialCorrespondence, .bidirectionalScoped,
      .exactOnVerifiedImage, .exactOnVerifiedImage⟩
  | .bor24 => ⟨.bo04, .evidenceOccurrenceToAssertion, .evidenceOccurrence, .assertion,
      .observation, .forwardOnly, .none, .evidenceReferencesOnly⟩
  | .bor25 => ⟨.bo02, .contractToProcessDefinition, .contract,
      .processDefinition, .partialCorrespondence, .bidirectionalScoped,
      .setValued, .typedCandidateSet⟩

def ruleFamily (rule : BridgeRuleId) : MappingFamily :=
  (bridgeRuleSpec rule).family

def ruleGeneration (_rule : BridgeRuleId) : Nat := 1

def ruleRequiresTypedWitness (_rule : BridgeRuleId) : Bool := true

def ruleRequiresLossAccount (_rule : BridgeRuleId) : Bool := true

def bridgeOntologyCovered (ontology : BridgeOntologyId) : Prop :=
  ∃ rule : BridgeRuleId, (bridgeRuleSpec rule).bridgeOntology = ontology

/-- The frozen bridge denominator contains exactly twenty-five rules. -/
theorem bridgeRuleId_card : Fintype.card BridgeRuleId = 25 := by
  decide

/-- The twenty-five mapping families also form an exact finite denominator. -/
theorem mappingFamily_card : Fintype.card MappingFamily = 25 := by
  decide

/-- No two rule IDs silently name the same mapping family. -/
theorem ruleFamily_injective : Function.Injective ruleFamily := by
  decide

/-- Every declared mapping family is represented by a rule. -/
theorem ruleFamily_surjective : Function.Surjective ruleFamily := by
  decide

theorem ruleFamily_bijective : Function.Bijective ruleFamily :=
  ⟨ruleFamily_injective, ruleFamily_surjective⟩

/-- The complete typed rule row, not merely its family tag, identifies a rule. -/
theorem bridgeRuleSpec_injective : Function.Injective bridgeRuleSpec := by
  intro left right equalSpec
  apply ruleFamily_injective
  change (bridgeRuleSpec left).family = (bridgeRuleSpec right).family
  exact congrArg BridgeRuleSpec.family equalSpec

/-- Every bridge ontology BO-01 through BO-13 is operationally covered. -/
theorem every_bridge_ontology_is_covered : ∀ ontology, bridgeOntologyCovered ontology := by
  intro ontology
  cases ontology
  · exact ⟨.bor04, rfl⟩
  · exact ⟨.bor01, rfl⟩
  · exact ⟨.bor02, rfl⟩
  · exact ⟨.bor06, rfl⟩
  · exact ⟨.bor08, rfl⟩
  · exact ⟨.bor12, rfl⟩
  · exact ⟨.bor13, rfl⟩
  · exact ⟨.bor14, rfl⟩
  · exact ⟨.bor15, rfl⟩
  · exact ⟨.bor16, rfl⟩
  · exact ⟨.bor18, rfl⟩
  · exact ⟨.bor21, rfl⟩
  · exact ⟨.bor23, rfl⟩

/-- No rule generation is implicit or unversioned. -/
theorem every_rule_has_generation_one :
    ∀ rule, ruleGeneration rule = 1 := by
  intro rule
  cases rule <;> rfl

/-- Witness and loss-account obligations are total over the denominator. -/
theorem every_rule_requires_witness_and_loss_account :
    ∀ rule,
      ruleRequiresTypedWitness rule = true ∧
      ruleRequiresLossAccount rule = true := by
  intro rule
  cases rule <;> exact ⟨rfl, rfl⟩

/-- A rule advertised as exact has a reverse only on its verified image. -/
theorem exact_round_trip_has_verified_image_reverse
    (rule : BridgeRuleId)
    (exact : (bridgeRuleSpec rule).roundTrip = .exactOnVerifiedImage) :
    (bridgeRuleSpec rule).reverseMode = .exactOnVerifiedImage := by
  cases rule <;> simp_all [bridgeRuleSpec]

/-- A genuinely set-valued rule never masquerades as a deterministic inverse. -/
theorem set_valued_rule_has_candidate_set_reverse
    (rule : BridgeRuleId)
    (setValued : (bridgeRuleSpec rule).roundTrip = .setValued) :
    (bridgeRuleSpec rule).reverseMode = .typedCandidateSet ∨
      (bridgeRuleSpec rule).reverseMode = .evidenceReferencesOnly := by
  cases rule <;> simp_all [bridgeRuleSpec]

/-- Task-equivalent transport has exactly the declared task-relative reverse. -/
theorem task_equivalent_rule_has_task_relative_reverse
    (rule : BridgeRuleId)
    (taskEquivalent : (bridgeRuleSpec rule).roundTrip = .taskEquivalent) :
    (bridgeRuleSpec rule).reverseMode = .taskRelative := by
  cases rule <;> simp_all [bridgeRuleSpec]

/-- A forward-only abstraction never acquires an undeclared inverse. -/
theorem no_round_trip_rule_has_no_exact_reverse
    (rule : BridgeRuleId)
    (none : (bridgeRuleSpec rule).roundTrip = .none) :
    (bridgeRuleSpec rule).reverseMode = .noReverse ∨
      (bridgeRuleSpec rule).reverseMode = .evidenceReferencesOnly := by
  cases rule <;> simp_all [bridgeRuleSpec]

/-- Bidirectional-scoped rules never claim that no reverse query exists. -/
theorem bidirectional_rule_has_declared_reverse
    (rule : BridgeRuleId)
    (bidirectional : (bridgeRuleSpec rule).direction = .bidirectionalScoped) :
    (bridgeRuleSpec rule).reverseMode ≠ .noReverse := by
  cases rule <;> simp_all [bridgeRuleSpec]

/-- Finite indexing exists without replacing the semantic rule identity. -/
noncomputable def bridgeRuleEquivFin25 : BridgeRuleId ≃ Fin 25 :=
  Fintype.equivFin BridgeRuleId

theorem bridgeRuleIndex_round_trip (rule : BridgeRuleId) :
    bridgeRuleEquivFin25.symm (bridgeRuleEquivFin25 rule) = rule :=
  bridgeRuleEquivFin25.left_inv rule

theorem bridgeRuleFromIndex_round_trip (index : Fin 25) :
    bridgeRuleEquivFin25 (bridgeRuleEquivFin25.symm index) = index :=
  bridgeRuleEquivFin25.right_inv index

end OCKIndividuationMSpaceComposition
