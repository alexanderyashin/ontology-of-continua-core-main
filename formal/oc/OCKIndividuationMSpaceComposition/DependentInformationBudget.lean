import OCKIndividuationMSpaceComposition.GaussianKLMagnitude

namespace OCKIndividuationMSpaceComposition

/-!
## Exchangeable dependence and effective information

For `raw` equally informative observations with common pairwise correlation
`correlation`, the variance inflation factor of their mean is
`1 + (raw - 1) * correlation`.  Dividing the raw count by this factor gives
the exact independent-equivalent observation count for the exchangeable
covariance model.  These results expose both the usable positive design law
and the finite-information ceiling caused by persistent dependence.
-/

/-- Independent-equivalent observations in the exchangeable-correlation
model. -/
noncomputable def exchangeableEffectiveObservations
    (raw correlation : ℝ) : ℝ :=
  raw / (1 + (raw - 1) * correlation)

/-- Increasing an admissible nonnegative correlation can only reduce the
effective observation count. -/
theorem exchangeableEffectiveObservations_antitone_correlation
    (raw firstCorrelation secondCorrelation : ℝ)
    (rawAtLeastOne : 1 ≤ raw)
    (firstNonnegative : 0 ≤ firstCorrelation)
    (correlationsOrdered : firstCorrelation ≤ secondCorrelation) :
    exchangeableEffectiveObservations raw secondCorrelation ≤
      exchangeableEffectiveObservations raw firstCorrelation := by
  have rawNonnegative : 0 ≤ raw := zero_le_one.trans rawAtLeastOne
  have offsetNonnegative : 0 ≤ raw - 1 := sub_nonneg.mpr rawAtLeastOne
  have firstDenominatorPositive :
      0 < 1 + (raw - 1) * firstCorrelation := by positivity
  have secondDenominatorPositive :
      0 < 1 + (raw - 1) * secondCorrelation := by
    have secondNonnegative : 0 ≤ secondCorrelation :=
      firstNonnegative.trans correlationsOrdered
    positivity
  apply (div_le_div_iff₀ secondDenominatorPositive firstDenominatorPositive).mpr
  nlinarith [mul_nonneg rawNonnegative
    (mul_nonneg offsetNonnegative (sub_nonneg.mpr correlationsOrdered))]

/-- Under nonnegative dependence, nominal sample count is optimistic: the
effective count never exceeds the raw count. -/
theorem exchangeableEffectiveObservations_le_raw
    (raw correlation : ℝ)
    (rawAtLeastOne : 1 ≤ raw) (correlationNonnegative : 0 ≤ correlation) :
    exchangeableEffectiveObservations raw correlation ≤ raw := by
  have rawNonnegative : 0 ≤ raw := zero_le_one.trans rawAtLeastOne
  have denominatorPositive : 0 < 1 + (raw - 1) * correlation := by
    have : 0 ≤ raw - 1 := sub_nonneg.mpr rawAtLeastOne
    positivity
  rw [exchangeableEffectiveObservations]
  apply (div_le_iff₀ denominatorPositive).mpr
  nlinarith [mul_nonneg (sub_nonneg.mpr rawAtLeastOne) correlationNonnegative]

/-- Exact finite-information ceiling: with positive persistent correlation
below one, no finite raw sample has as much information as `1 / correlation`
independent observations. -/
theorem exchangeableEffectiveObservations_lt_inverseCorrelation
    (raw correlation : ℝ)
    (rawPositive : 0 < raw)
    (correlationPositive : 0 < correlation)
    (correlationBelowOne : correlation < 1) :
    exchangeableEffectiveObservations raw correlation < 1 / correlation := by
  have denominatorPositive : 0 < 1 + (raw - 1) * correlation := by
    nlinarith [mul_pos rawPositive correlationPositive]
  rw [exchangeableEffectiveObservations]
  apply (div_lt_div_iff₀ denominatorPositive correlationPositive).mpr
  nlinarith

/-- No-go design law: if the requested independent-equivalent count reaches
the dependence ceiling, increasing a finite raw sample can never meet it. -/
theorem exchangeable_target_unreachable_at_dependence_ceiling
    (raw correlation target : ℝ)
    (rawPositive : 0 < raw)
    (correlationPositive : 0 < correlation)
    (correlationBelowOne : correlation < 1)
    (ceilingBelowTarget : 1 / correlation ≤ target) :
    exchangeableEffectiveObservations raw correlation < target :=
  (exchangeableEffectiveObservations_lt_inverseCorrelation raw correlation
    rawPositive correlationPositive correlationBelowOne).trans_le ceilingBelowTarget

/-- Exact inversion of the effective-count constraint.  Below the correlation
ceiling, this raw-sample formula is sufficient for the requested effective
sample size. -/
theorem exchangeable_raw_threshold_sufficient
    (raw correlation target : ℝ)
    (targetPositive : 0 < target)
    (correlationNonnegative : 0 ≤ correlation)
    (correlationBelowOne : correlation < 1)
    (belowCeiling : target * correlation < 1)
    (enoughRaw :
      target * (1 - correlation) / (1 - target * correlation) ≤ raw) :
    target ≤ exchangeableEffectiveObservations raw correlation := by
  have oneMinusCorrelationPositive : 0 < 1 - correlation := by linarith
  have budgetDenominatorPositive : 0 < 1 - target * correlation := by linarith
  have thresholdPositive :
      0 < target * (1 - correlation) / (1 - target * correlation) := by positivity
  have rawPositive : 0 < raw := thresholdPositive.trans_le enoughRaw
  have denominatorPositive : 0 < 1 + (raw - 1) * correlation := by
    nlinarith [mul_nonneg (le_of_lt rawPositive) correlationNonnegative]
  rw [exchangeableEffectiveObservations]
  apply (le_div_iff₀ denominatorPositive).mpr
  apply (div_le_iff₀ budgetDenominatorPositive).mp at enoughRaw
  nlinarith

/-- A correlation interval gives a rigorous effective-information interval.
The upper correlation endpoint is the conservative design value. -/
theorem exchangeable_uncertainty_sandwich
    (raw lowerCorrelation actualCorrelation upperCorrelation : ℝ)
    (rawAtLeastOne : 1 ≤ raw)
    (lowerNonnegative : 0 ≤ lowerCorrelation)
    (lowerBound : lowerCorrelation ≤ actualCorrelation)
    (upperBound : actualCorrelation ≤ upperCorrelation) :
    exchangeableEffectiveObservations raw upperCorrelation ≤
        exchangeableEffectiveObservations raw actualCorrelation ∧
      exchangeableEffectiveObservations raw actualCorrelation ≤
        exchangeableEffectiveObservations raw lowerCorrelation := by
  constructor
  · exact exchangeableEffectiveObservations_antitone_correlation
      raw actualCorrelation upperCorrelation rawAtLeastOne
      (lowerNonnegative.trans lowerBound) upperBound
  · exact exchangeableEffectiveObservations_antitone_correlation
      raw lowerCorrelation actualCorrelation rawAtLeastOne
      lowerNonnegative lowerBound

/-- Independent exchangeable blocks add their registered effective counts.
This is a block-design surface, not a claim that rows from different blocks
are independent without an explicit domain contract. -/
noncomputable def independentBlockEffectiveObservations
    (blocks blockSize correlation : ℝ) : ℝ :=
  blocks * exchangeableEffectiveObservations blockSize correlation

/-- Exact linear growth in the number of independent blocks.  Thus the
single-block `1/rho` ceiling is not a global ceiling when genuinely
independent new blocks can be acquired. -/
theorem independentBlockEffectiveObservations_linear_blocks
    (firstBlocks secondBlocks blockSize correlation : ℝ) :
    independentBlockEffectiveObservations (firstBlocks + secondBlocks)
        blockSize correlation =
      independentBlockEffectiveObservations firstBlocks blockSize correlation +
        independentBlockEffectiveObservations secondBlocks blockSize correlation := by
  simp [independentBlockEffectiveObservations]
  ring

/-- Any target can be exceeded by acquiring sufficiently many independent
blocks whenever one block carries positive effective information. -/
theorem independent_blocks_break_single_block_ceiling
    (blocks blockSize correlation target : ℝ)
    (oneBlockPositive :
      0 < exchangeableEffectiveObservations blockSize correlation)
    (enoughBlocks :
      target / exchangeableEffectiveObservations blockSize correlation < blocks) :
    target < independentBlockEffectiveObservations blocks blockSize correlation := by
  rw [independentBlockEffectiveObservations]
  exact (div_lt_iff₀ oneBlockPositive).mp enoughBlocks

/-- Correlation uncertainty propagates blockwise when the number of admitted
independent blocks is nonnegative. -/
theorem independentBlock_uncertainty_sandwich
    (blocks blockSize lowerCorrelation actualCorrelation upperCorrelation : ℝ)
    (blocksNonnegative : 0 ≤ blocks)
    (blockSizeAtLeastOne : 1 ≤ blockSize)
    (lowerNonnegative : 0 ≤ lowerCorrelation)
    (lowerBound : lowerCorrelation ≤ actualCorrelation)
    (upperBound : actualCorrelation ≤ upperCorrelation) :
    independentBlockEffectiveObservations blocks blockSize upperCorrelation ≤
        independentBlockEffectiveObservations blocks blockSize actualCorrelation ∧
      independentBlockEffectiveObservations blocks blockSize actualCorrelation ≤
        independentBlockEffectiveObservations blocks blockSize lowerCorrelation := by
  rcases exchangeable_uncertainty_sandwich blockSize lowerCorrelation
    actualCorrelation upperCorrelation blockSizeAtLeastOne lowerNonnegative
    lowerBound upperBound with ⟨lower, upper⟩
  constructor <;>
    exact mul_le_mul_of_nonneg_left (by assumption) blocksNonnegative

/-- Error envelope after replacing nominal observations by their exact
exchangeable effective count. -/
noncomputable def dependentExponentialUnionBudget
    (competitors raw correlation exponent : ℝ) : ℝ :=
  exponentialUnionBudget competitors
    (exchangeableEffectiveObservations raw correlation) exponent

/-- End-to-end conservative experimental design: the closed raw-sample
threshold compensates for correlation and then discharges the same exponential
error guarantee as the independent channel. -/
theorem exchangeable_raw_threshold_guarantees_budget
    (competitors targetError exponent raw correlation : ℝ)
    (competitorsPositive : 0 < competitors)
    (targetErrorPositive : 0 < targetError)
    (targetBelowCompetitors : targetError < competitors)
    (exponentPositive : 0 < exponent)
    (correlationNonnegative : 0 ≤ correlation)
    (correlationBelowOne : correlation < 1)
    (belowCeiling :
      requiredRealObservations competitors targetError exponent * correlation < 1)
    (enoughRaw :
      requiredRealObservations competitors targetError exponent * (1 - correlation) /
          (1 - requiredRealObservations competitors targetError exponent * correlation) ≤ raw) :
    dependentExponentialUnionBudget competitors raw correlation exponent ≤
      targetError := by
  have targetPositive :
      0 < requiredRealObservations competitors targetError exponent := by
    rw [requiredRealObservations]
    have ratioGreaterThanOne : 1 < competitors / targetError := by
      exact (one_lt_div targetErrorPositive).mpr targetBelowCompetitors
    exact div_pos (Real.log_pos ratioGreaterThanOne) exponentPositive
  apply requiredRealObservations_guarantees_budget
    competitors targetError exponent
    (exchangeableEffectiveObservations raw correlation)
    competitorsPositive targetErrorPositive exponentPositive
  exact exchangeable_raw_threshold_sufficient raw correlation
    (requiredRealObservations competitors targetError exponent)
    targetPositive correlationNonnegative correlationBelowOne belowCeiling enoughRaw

end OCKIndividuationMSpaceComposition
