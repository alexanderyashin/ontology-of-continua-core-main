import OCKIndividuationMSpaceComposition.CrossDomainEffectTransport

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uContext

/-!
# Family-level suffix-event predictive risk transport

The empirical adapters use domain-specific target events.  This module does
not identify those events with one another.  It reuses the mature OC transport
algebra by treating the reference-minus-adapted Brier risk as the transported
effect.  Thus the positive result is a quantitative bound under an explicit
drift/weight contract, while the overlap countermodel remains a formal no-go.
-/

/-- Improvement in suffix-event Brier risk relative to a registered reference. -/
def suffixRiskImprovement (referenceRisk adaptedRisk : ℚ) : ℚ :=
  referenceRisk - adaptedRisk

/-- Domain/context-indexed suffix-risk improvement profile. -/
def suffixRiskProfile {Context : Type uContext} (risk : Context → ℚ) :
    Context → ℚ := fun context => risk context

/--
A family-level transport certificate for domain-specific suffix-event tasks.
The target and source outcomes may differ; only the risk functional and the
declared context contract are shared.
-/
structure FamilySuffixRiskTransportContract
    {Context : Type uContext} [Fintype Context] where
  sourceWeight : Context → ℚ
  targetWeight : Context → ℚ
  sourceImprovement : Context → ℚ
  targetImprovement : Context → ℚ
  mechanismDriftRadius : ℚ
  improvementMagnitudeBound : ℚ
  targetWeightNonnegative : ∀ context, 0 ≤ targetWeight context
  targetWeightNormalized : ∑ context, targetWeight context = 1
  mechanismDriftBound : ∀ context,
    |targetImprovement context - sourceImprovement context| ≤
      mechanismDriftRadius
  sourceImprovementBounded : ∀ context,
    |sourceImprovement context| ≤ improvementMagnitudeBound

/--
Positive family-level theorem: the transported suffix-risk improvement differs
from its source-weighted reference by at most mechanism drift plus population
composition shift.  This is an OC adapter theorem; the algebra is reused from
`combined_cross_domain_transport_bound`.
-/
theorem family_suffix_risk_transport_bound
    {Context : Type uContext} [Fintype Context]
    (contract : FamilySuffixRiskTransportContract (Context := Context)) :
    |domainAverageEffect contract.targetWeight contract.targetImprovement -
        domainAverageEffect contract.sourceWeight contract.sourceImprovement| ≤
      contract.mechanismDriftRadius +
        contract.improvementMagnitudeBound *
          ∑ context,
            |contract.targetWeight context - contract.sourceWeight context| := by
  exact combined_cross_domain_transport_bound
    contract.sourceWeight contract.targetWeight
    contract.sourceImprovement contract.targetImprovement
    contract.mechanismDriftRadius contract.improvementMagnitudeBound
    contract.targetWeightNonnegative contract.targetWeightNormalized
    contract.mechanismDriftBound contract.sourceImprovementBounded

/--
The bound is stable under the explicit reference-minus-adapted Brier-risk
encoding used by the empirical packet.
-/
theorem family_suffix_risk_transport_bound_expanded
    {Context : Type uContext} [Fintype Context]
    (contract : FamilySuffixRiskTransportContract (Context := Context))
    (referenceSource adaptedSource referenceTarget adaptedTarget : Context → ℚ)
    (sourceEncoding : ∀ context,
      contract.sourceImprovement context =
        suffixRiskImprovement (referenceSource context) (adaptedSource context))
    (targetEncoding : ∀ context,
      contract.targetImprovement context =
        suffixRiskImprovement (referenceTarget context) (adaptedTarget context)) :
    |domainAverageEffect contract.targetWeight
          (fun context => referenceTarget context - adaptedTarget context) -
        domainAverageEffect contract.sourceWeight
          (fun context => referenceSource context - adaptedSource context)| ≤
      contract.mechanismDriftRadius +
        contract.improvementMagnitudeBound *
          ∑ context,
            |contract.targetWeight context - contract.sourceWeight context| := by
  have bound := family_suffix_risk_transport_bound contract
  have sourceEquality := funext sourceEncoding
  have targetEquality := funext targetEncoding
  rw [sourceEquality, targetEquality] at bound
  simpa [suffixRiskImprovement] using bound

/--
Formal no-go specialization: without source overlap, equal source evidence can
support different target suffix-risk effects.  Therefore family-level
transport requires an overlap/transport contract; it cannot be inferred from
source observations alone.
-/
theorem family_suffix_risk_no_overlap_no_go :
    (∀ context, sourcePointWeight context ≠ 0 →
      zeroContextEffect context = hiddenTargetEffect context) ∧
    domainAverageEffect sourcePointWeight zeroContextEffect =
      domainAverageEffect sourcePointWeight hiddenTargetEffect ∧
    domainAverageEffect targetPointWeight zeroContextEffect = 0 ∧
    domainAverageEffect targetPointWeight hiddenTargetEffect = 1 := by
  exact missing_overlap_blocks_cross_domain_effect_identification

end OCKIndividuationMSpaceComposition
