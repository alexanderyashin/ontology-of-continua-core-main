/-!
OC Core 1.4 minimal obligation spine: Q063_Q013 finite-spectrum
computable-stability gate.

The frozen question asks what computability-theoretic conclusion follows when
`T` has finitely many models in `ℵ₁`, with a possible `ℵₙ` extension.  This
file preserves that target and prevents replacement by a narrower categorical
case, a classical spectrum fact, or a release-scope irrelevance record.
-/

namespace OCMinimalObligationSpine

structure Q06313FiniteSpectrumHypotheses : Type where
  theorySpecified : Prop
  languageSizeSpecified : Prop
  completenessSpecified : Prop
  computabilityAssumptionsSpecified : Prop
  finiteModelsInAlephOne : Prop
  optionalFiniteModelsInAlephN : Prop
  theoryProof : theorySpecified
  languageSizeProof : languageSizeSpecified
  completenessProof : completenessSpecified
  computabilityAssumptionsProof : computabilityAssumptionsSpecified
  alephOneFiniteProof : finiteModelsInAlephOne

structure Q06313EffectiveConclusion : Type where
  conclusionSpecified : Prop
  uniformitySpecified : Prop
  degreeOrPresentationBoundsSpecified : Prop
  algorithmicContentSpecified : Prop
  conclusionProof : conclusionSpecified
  uniformityProof : uniformitySpecified
  degreeOrPresentationBoundsProof : degreeOrPresentationBoundsSpecified
  algorithmicContentProof : algorithmicContentSpecified

structure Q06313PositiveAnswerPayload : Type where
  hypotheses : Q06313FiniteSpectrumHypotheses
  effectiveConclusion : Q06313EffectiveConclusion
  derivesConclusionFromFiniteSpectrum : Prop
  notOnlyAlephOneCategoricalCase : Prop
  noncategoricalFiniteSpectrumRedTeamPass : Prop
  derivationProof : derivesConclusionFromFiniteSpectrum
  broaderThanCategoricalProof : notOnlyAlephOneCategoricalCase
  redTeamProof : noncategoricalFiniteSpectrumRedTeamPass

structure Q06313CounterexamplePayload : Type where
  hypotheses : Q06313FiniteSpectrumHypotheses
  proposedConclusion : Q06313EffectiveConclusion
  satisfiesFiniteSpectrumHypothesis : Prop
  failsProposedEffectiveConclusion : Prop
  codingRobustness : Prop
  hypothesisProof : satisfiesFiniteSpectrumHypothesis
  failureProof : failsProposedEffectiveConclusion
  robustnessProof : codingRobustness

structure Q06313IllPosedPayload : Type where
  exactFrozenQuestionBound : Prop
  missingAssumptionsSpecified : Prop
  noUniqueEffectiveConclusionWithoutAddedAssumptions : Prop
  minimalAddedAssumptionsProvided : Prop
  sourceQuestionProof : exactFrozenQuestionBound
  missingAssumptionsProof : missingAssumptionsSpecified
  noUniqueConclusionProof : noUniqueEffectiveConclusionWithoutAddedAssumptions
  minimalAssumptionsProof : minimalAddedAssumptionsProvided

structure Q06313EffectiveFewSpectrumSuccessor : Type where
  successorResult : Prop
  successorWithinFiniteSpectrumContext : Prop
  notTerminalByItself : Prop
  successorProof : successorResult
  contextProof : successorWithinFiniteSpectrumContext
  nonterminalProof : notTerminalByItself

structure Q06313SuccessorPromotionPayload : Type where
  successor : Q06313EffectiveFewSpectrumSuccessor
  exactFrozenHypothesesCovered : Prop
  effectiveConclusionMatchesSourceQuestion : Prop
  categoricalSpecialCaseNotOnlyRoute : Prop
  promotionProof : exactFrozenHypothesesCovered
  conclusionMatchProof : effectiveConclusionMatchesSourceQuestion
  notOnlyCategoricalProof : categoricalSpecialCaseNotOnlyRoute

structure Q06313ReleaseIrrelevancePayload : Type where
  exactSourceStatementBound : Prop
  noNecessaryOC14DependencyEdge : Prop
  noSolvedMathClaimMade : Prop
  retainedAsOpenResearchLine : Prop
  exactSourceStatementProof : exactSourceStatementBound
  noNecessaryEdgeProof : noNecessaryOC14DependencyEdge
  noSolvedMathClaimProof : noSolvedMathClaimMade
  retainedOpenProof : retainedAsOpenResearchLine

inductive Q06313MathematicalClosure : Type where
  | positive (payload : Q06313PositiveAnswerPayload)
  | promotedSuccessor (payload : Q06313SuccessorPromotionPayload)
  | counterexample (payload : Q06313CounterexamplePayload)
  | illPosed (payload : Q06313IllPosedPayload)

inductive Q06313ReleaseDisposition : Type where
  | mathematical (closure : Q06313MathematicalClosure)
  | releaseIrrelevant (payload : Q06313ReleaseIrrelevancePayload)

theorem q06313_positive_answer_closes_only_with_effective_derivation
    (payload : Q06313PositiveAnswerPayload) :
    payload.derivesConclusionFromFiniteSpectrum ∧
      payload.notOnlyAlephOneCategoricalCase ∧
      payload.noncategoricalFiniteSpectrumRedTeamPass := by
  exact ⟨payload.derivationProof,
    payload.broaderThanCategoricalProof,
    payload.redTeamProof⟩

theorem q06313_successor_needs_promotion_to_close_frozen_target
    (payload : Q06313SuccessorPromotionPayload) :
    payload.exactFrozenHypothesesCovered ∧
      payload.effectiveConclusionMatchesSourceQuestion ∧
      payload.categoricalSpecialCaseNotOnlyRoute := by
  exact ⟨payload.promotionProof,
    payload.conclusionMatchProof,
    payload.notOnlyCategoricalProof⟩

theorem q06313_counterexample_refutes_proposed_effective_conclusion
    (payload : Q06313CounterexamplePayload) :
    payload.satisfiesFiniteSpectrumHypothesis ∧
      payload.failsProposedEffectiveConclusion ∧
      payload.codingRobustness := by
  exact ⟨payload.hypothesisProof,
    payload.failureProof,
    payload.robustnessProof⟩

theorem q06313_ill_posed_payload_requires_minimal_added_assumptions
    (payload : Q06313IllPosedPayload) :
    payload.exactFrozenQuestionBound ∧
      payload.missingAssumptionsSpecified ∧
      payload.noUniqueEffectiveConclusionWithoutAddedAssumptions ∧
      payload.minimalAddedAssumptionsProvided := by
  exact ⟨payload.sourceQuestionProof,
    payload.missingAssumptionsProof,
    payload.noUniqueConclusionProof,
    payload.minimalAssumptionsProof⟩

theorem q06313_release_irrelevance_is_not_math_closure
    (payload : Q06313ReleaseIrrelevancePayload) :
    payload.noNecessaryOC14DependencyEdge ∧
      payload.noSolvedMathClaimMade ∧
      payload.retainedAsOpenResearchLine := by
  exact ⟨payload.noNecessaryEdgeProof,
    payload.noSolvedMathClaimProof,
    payload.retainedOpenProof⟩

theorem q06313_release_disposition_decides_only_allowed_routes
    (disposition : Q06313ReleaseDisposition) :
    (∃ payload : Q06313PositiveAnswerPayload,
      disposition = Q06313ReleaseDisposition.mathematical
        (Q06313MathematicalClosure.positive payload)) ∨
    (∃ payload : Q06313SuccessorPromotionPayload,
      disposition = Q06313ReleaseDisposition.mathematical
        (Q06313MathematicalClosure.promotedSuccessor payload)) ∨
    (∃ payload : Q06313CounterexamplePayload,
      disposition = Q06313ReleaseDisposition.mathematical
        (Q06313MathematicalClosure.counterexample payload)) ∨
    (∃ payload : Q06313IllPosedPayload,
      disposition = Q06313ReleaseDisposition.mathematical
        (Q06313MathematicalClosure.illPosed payload)) ∨
    (∃ payload : Q06313ReleaseIrrelevancePayload,
      disposition = Q06313ReleaseDisposition.releaseIrrelevant payload) := by
  cases disposition with
  | mathematical closure =>
      cases closure with
      | positive payload => exact Or.inl ⟨payload, rfl⟩
      | promotedSuccessor payload => exact Or.inr (Or.inl ⟨payload, rfl⟩)
      | counterexample payload => exact Or.inr (Or.inr (Or.inl ⟨payload, rfl⟩))
      | illPosed payload => exact Or.inr (Or.inr (Or.inr (Or.inl ⟨payload, rfl⟩)))
  | releaseIrrelevant payload =>
      exact Or.inr (Or.inr (Or.inr (Or.inr ⟨payload, rfl⟩)))

end OCMinimalObligationSpine
