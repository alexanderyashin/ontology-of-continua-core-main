import OCKIndividuationMSpaceComposition.TaskConditionedOptics

namespace OCKIndividuationMSpaceComposition

/-!
# Finite-sample refinement crossover

Oracle refinement is monotone, but a learned refinement pays estimation error.
Combining the existing uniform-deviation ERM theorem with the oracle
certificate gives the operational crossover rule: if the fine optic's oracle
gain exceeds twice its declared uniform deviation, the empirically selected
fine rule is guaranteed to beat every coarse rule.  The condition is
directional and intentionally does not pretend that a coarse estimation error
is irrelevant when one wants a symmetric comparison or model selection.
-/

theorem refinement_empirical_choice_strictly_beats_every_coarse_rule
    {FineObservation CoarseObservation Action : Type*}
    (fineRisk : (FineObservation → Action) → ℝ)
    (coarseRisk : (CoarseObservation → Action) → ℝ)
    (fineEmpiricalRisk : (FineObservation → Action) → ℝ)
    (fineOracle : OracleDecisionCertificate fineRisk)
    (coarseOracle : OracleDecisionCertificate coarseRisk)
    (fineChosen : FineObservation → Action)
    (coarseChosen : CoarseObservation → Action)
    (epsilon : ℝ)
    (uniformDeviation : ∀ decision,
      |fineEmpiricalRisk decision - fineRisk decision| ≤ epsilon)
    (fineEmpiricalOptimal :
      fineEmpiricalRisk fineChosen ≤ fineEmpiricalRisk fineOracle.rule)
    (oracleGainClearsDeviation :
      fineOracle.value + 2 * epsilon < coarseOracle.value) :
    fineRisk fineChosen < coarseRisk coarseChosen := by
  have fineExcess := uniform_deviation_erm_excess_risk
    fineRisk fineEmpiricalRisk fineChosen fineOracle.rule epsilon
      uniformDeviation fineEmpiricalOptimal
  have fineBelowCoarseOracle : fineRisk fineChosen < coarseOracle.value := by
    calc
      fineRisk fineChosen ≤ fineRisk fineOracle.rule + 2 * epsilon := fineExcess
      _ = fineOracle.value + 2 * epsilon := by rw [fineOracle.value_eq]
      _ < coarseOracle.value := oracleGainClearsDeviation
  exact lt_of_lt_of_le fineBelowCoarseOracle
    (coarseOracle.optimal coarseChosen)

/-- The theorem's margin is an explicit measurable sufficient condition; it
does not claim that the condition is necessary for a particular data set. -/
theorem refinement_crossover_margin_is_the_declared_budget
    {FineObservation CoarseObservation Action : Type*}
    (fineRisk : (FineObservation → Action) → ℝ)
    (coarseRisk : (CoarseObservation → Action) → ℝ)
    (fineOracle : OracleDecisionCertificate fineRisk)
    (coarseOracle : OracleDecisionCertificate coarseRisk)
    (epsilon : ℝ)
    (oracleGain : ℝ)
    (gain_identity : coarseOracle.value - fineOracle.value = oracleGain) :
    oracleGain > 2 * epsilon ↔
      fineOracle.value + 2 * epsilon < coarseOracle.value := by
  constructor <;> intro hypothesis <;> linarith [gain_identity]

end OCKIndividuationMSpaceComposition
