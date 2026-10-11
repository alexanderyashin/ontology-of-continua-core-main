/-!
OC Core 1.4 minimal obligation spine: Q063_Q006 computable-section gate.

This file intentionally does not prove the AIM computable-stability question.
It preserves the frozen target and makes the admissible closure routes explicit:
a positive computable-section construction, a negative no-computable-section
obstruction, or a release-scope irrelevance payload that is not a mathematical
solution of the source question.
-/

namespace OCMinimalObligationSpine

structure Q06306StableElementarySetup : Type where
  stableTheory : Prop
  sourceModelSpecified : Prop
  targetModelSpecified : Prop
  elementarySubmodel : Prop
  computableDataSpecified : Prop
  stableTheoryProof : stableTheory
  sourceModelProof : sourceModelSpecified
  targetModelProof : targetModelSpecified
  elementarySubmodelProof : elementarySubmodel
  computableDataProof : computableDataSpecified

structure Q06306TypeSpaceRepresentation : Type where
  sourceTypeSpaceRepresented : Prop
  targetTypeSpaceRepresented : Prop
  sourceNamesComputable : Prop
  targetNamesComputable : Prop
  restrictionMapRepresented : Prop
  codingArtifactFree : Prop
  sourceRepresentationProof : sourceTypeSpaceRepresented
  targetRepresentationProof : targetTypeSpaceRepresented
  sourceNamesProof : sourceNamesComputable
  targetNamesProof : targetNamesComputable
  restrictionMapProof : restrictionMapRepresented
  codingArtifactFreeProof : codingArtifactFree

structure Q06306ClassicalNonforkingSection : Type where
  setup : Q06306StableElementarySetup
  representation : Q06306TypeSpaceRepresentation
  existsUniqueNonforkingExtension : Prop
  continuousSectionExists : Prop
  uniqueExtensionProof : existsUniqueNonforkingExtension
  continuousSectionProof : continuousSectionExists

structure Q06306ComputableSectionAlgorithm : Type where
  algorithm : Prop
  totalOnRepresentedSourceTypes : Prop
  computesUniqueNonforkingExtension : Prop
  uniformInDeclaredData : Prop
  noHiddenOracle : Prop
  algorithmProof : algorithm
  totalityProof : totalOnRepresentedSourceTypes
  correctnessProof : computesUniqueNonforkingExtension
  uniformityProof : uniformInDeclaredData
  noOracleProof : noHiddenOracle

structure Q06306PositivePayload : Type where
  classicalDenominator : Q06306ClassicalNonforkingSection
  computableSection : Q06306ComputableSectionAlgorithm
  totalityProof : computableSection.totalOnRepresentedSourceTypes
  correctnessProof : computableSection.computesUniqueNonforkingExtension
  uniformityProof : computableSection.uniformInDeclaredData
  noOracleProof : computableSection.noHiddenOracle

structure Q06306NegativePayload : Type where
  setup : Q06306StableElementarySetup
  representation : Q06306TypeSpaceRepresentation
  stableComputableInstance : Prop
  noComputableSection : Prop
  codingRobustness : Prop
  stableComputableInstanceProof : stableComputableInstance
  obstructionProof : noComputableSection
  robustnessProof : codingRobustness

structure Q06306ReleaseIrrelevancePayload : Type where
  exactSourceStatementBound : Prop
  noNecessaryOC14DependencyEdge : Prop
  noSolvedMathClaimMade : Prop
  retainedAsOpenResearchLine : Prop
  exactSourceStatementProof : exactSourceStatementBound
  noNecessaryEdgeProof : noNecessaryOC14DependencyEdge
  noSolvedMathClaimProof : noSolvedMathClaimMade
  retainedOpenProof : retainedAsOpenResearchLine

inductive Q06306MathematicalClosure : Type where
  | positive (payload : Q06306PositivePayload)
  | negative (payload : Q06306NegativePayload)

inductive Q06306ReleaseDisposition : Type where
  | mathematical (closure : Q06306MathematicalClosure)
  | releaseIrrelevant (payload : Q06306ReleaseIrrelevancePayload)

theorem q06306_positive_payload_closes_frozen_computable_section
    (payload : Q06306PositivePayload) :
    payload.computableSection.algorithm ∧
      payload.computableSection.totalOnRepresentedSourceTypes ∧
      payload.computableSection.computesUniqueNonforkingExtension ∧
      payload.computableSection.uniformInDeclaredData ∧
      payload.computableSection.noHiddenOracle := by
  exact ⟨payload.computableSection.algorithmProof,
    payload.totalityProof,
    payload.correctnessProof,
    payload.uniformityProof,
    payload.noOracleProof⟩

theorem q06306_negative_payload_refutes_frozen_computable_section
    (payload : Q06306NegativePayload) :
    payload.noComputableSection ∧ payload.codingRobustness := by
  exact ⟨payload.obstructionProof, payload.robustnessProof⟩

theorem q06306_release_irrelevance_is_not_math_closure
    (payload : Q06306ReleaseIrrelevancePayload) :
    payload.noNecessaryOC14DependencyEdge ∧
      payload.noSolvedMathClaimMade ∧
      payload.retainedAsOpenResearchLine := by
  exact ⟨payload.noNecessaryEdgeProof,
    payload.noSolvedMathClaimProof,
    payload.retainedOpenProof⟩

theorem q06306_release_disposition_decides_only_allowed_routes
    (disposition : Q06306ReleaseDisposition) :
    (∃ payload : Q06306PositivePayload,
      disposition = Q06306ReleaseDisposition.mathematical
        (Q06306MathematicalClosure.positive payload)) ∨
    (∃ payload : Q06306NegativePayload,
      disposition = Q06306ReleaseDisposition.mathematical
        (Q06306MathematicalClosure.negative payload)) ∨
    (∃ payload : Q06306ReleaseIrrelevancePayload,
      disposition = Q06306ReleaseDisposition.releaseIrrelevant payload) := by
  cases disposition with
  | mathematical closure =>
      cases closure with
      | positive payload => exact Or.inl ⟨payload, rfl⟩
      | negative payload => exact Or.inr (Or.inl ⟨payload, rfl⟩)
  | releaseIrrelevant payload =>
      exact Or.inr (Or.inr ⟨payload, rfl⟩)

end OCMinimalObligationSpine
