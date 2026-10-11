import OCKIndividuationMSpaceComposition.BudgetedPredictiveSafety

namespace OCKIndividuationMSpaceComposition

/-!
The squared-loss adapter for predictive mixtures.

This is the domain-neutral algebra used when adaptive optics aggregates two
admissible path predictors.  It says that mixture loss is the weighted mean
of component losses minus an explicit diversity credit.  It does not say
that an empirical selector transports or that either predictor is calibrated.
-/

theorem convexMixtureSquaredLoss_decomposition
    (outcome first second weight : ℝ) :
    weight * binarySquaredLoss outcome first
        + (1 - weight) * binarySquaredLoss outcome second
      = binarySquaredLoss outcome (weight * first + (1 - weight) * second)
        + weight * (1 - weight) * (first - second) ^ 2 := by
  dsimp [binarySquaredLoss]
  ring

theorem convexMixtureSquaredLoss_le_weightedComponents
    (outcome first second weight : ℝ)
    (hweightLower : 0 ≤ weight)
    (hweightUpper : weight ≤ 1) :
    binarySquaredLoss outcome (weight * first + (1 - weight) * second)
      ≤ weight * binarySquaredLoss outcome first
        + (1 - weight) * binarySquaredLoss outcome second := by
  rw [convexMixtureSquaredLoss_decomposition]
  have hcomplement : 0 ≤ 1 - weight := sub_nonneg.mpr hweightUpper
  apply le_add_of_nonneg_right
  positivity

theorem convexMixtureSquaredLoss_strict_diversity_credit
    (outcome first second weight : ℝ)
    (hweightLower : 0 < weight)
    (hweightUpper : weight < 1)
    (hdifferent : first ≠ second) :
    binarySquaredLoss outcome (weight * first + (1 - weight) * second)
      < weight * binarySquaredLoss outcome first
        + (1 - weight) * binarySquaredLoss outcome second := by
  rw [convexMixtureSquaredLoss_decomposition]
  have hcomplement : 0 < 1 - weight := sub_pos.mpr hweightUpper
  have hdifference : 0 < (first - second) ^ 2 := sq_pos_of_ne_zero (sub_ne_zero.mpr hdifferent)
  apply lt_add_of_pos_right
  positivity

end OCKIndividuationMSpaceComposition
