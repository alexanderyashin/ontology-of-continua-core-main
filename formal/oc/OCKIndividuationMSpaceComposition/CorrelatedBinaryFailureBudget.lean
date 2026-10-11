import OCKIndividuationMSpaceComposition.ProductMeasureKL
import Mathlib.Probability.Moments.Variance

namespace OCKIndividuationMSpaceComposition

open MeasureTheory ProbabilityTheory

/-!
## Correlated binary failures

For an exchangeable Bernoulli block with marginal failure probability `p`,
raw size `n`, and common pairwise correlation `rho`, the empirical failure
rate has mean-square error

`p * (1 - p) * (1 + (n - 1) * rho) / n`.

The algebra below makes the engineering consequence explicit: increasing one
persistent block cannot remove the `p * (1-p) * rho` error floor, whereas
independent replicated blocks divide the whole block error by their count.
This is an exact second-moment model, not a claim that arbitrary incident
records are exchangeable Bernoulli trials.
-/

/-- Mean-square error of the empirical failure rate in one exchangeable
binary block. -/
noncomputable def exchangeableBinaryMeanMSE
    (raw failureProbability correlation : ℝ) : ℝ :=
  failureProbability * (1 - failureProbability) *
    (1 + (raw - 1) * correlation) / raw

/-- The exchangeable binary MSE is a persistent-correlation floor plus a
finite-sample term. -/
theorem exchangeableBinaryMeanMSE_decomposition
    (raw failureProbability correlation : ℝ)
    (rawNonzero : raw ≠ 0) :
    exchangeableBinaryMeanMSE raw failureProbability correlation =
      failureProbability * (1 - failureProbability) *
        (correlation + (1 - correlation) / raw) := by
  rw [exchangeableBinaryMeanMSE]
  field_simp
  ring

/-- Persistent nonnegative within-block correlation imposes an exact lower
bound on the MSE of the empirical failure rate, no matter how large the one
block becomes. -/
theorem exchangeableBinaryMeanMSE_correlation_floor
    (raw failureProbability correlation : ℝ)
    (rawPositive : 0 < raw)
    (probabilityNonnegative : 0 ≤ failureProbability)
    (probabilityAtMostOne : failureProbability ≤ 1)
    (_correlationNonnegative : 0 ≤ correlation)
    (correlationAtMostOne : correlation ≤ 1) :
    failureProbability * (1 - failureProbability) * correlation ≤
      exchangeableBinaryMeanMSE raw failureProbability correlation := by
  rw [exchangeableBinaryMeanMSE_decomposition raw failureProbability correlation
    rawPositive.ne']
  have hVarianceNonnegative :
      0 ≤ failureProbability * (1 - failureProbability) :=
    mul_nonneg probabilityNonnegative (sub_nonneg.mpr probabilityAtMostOne)
  have hFiniteTermNonnegative : 0 ≤ (1 - correlation) / raw :=
    div_nonneg (sub_nonneg.mpr correlationAtMostOne) rawPositive.le
  exact mul_le_mul_of_nonneg_left
    (le_add_of_nonneg_right hFiniteTermNonnegative) hVarianceNonnegative

/-- No amount of additional sampling inside one persistent correlated block
can meet an MSE target below the correlation floor. -/
theorem exchangeableBinary_singleBlock_target_impossible
    (raw failureProbability correlation target : ℝ)
    (rawPositive : 0 < raw)
    (probabilityNonnegative : 0 ≤ failureProbability)
    (probabilityAtMostOne : failureProbability ≤ 1)
    (correlationNonnegative : 0 ≤ correlation)
    (correlationAtMostOne : correlation ≤ 1)
    (targetBelowFloor :
      target < failureProbability * (1 - failureProbability) * correlation) :
    ¬ exchangeableBinaryMeanMSE raw failureProbability correlation ≤ target := by
  intro hTarget
  have hFloor := exchangeableBinaryMeanMSE_correlation_floor
    raw failureProbability correlation rawPositive probabilityNonnegative
    probabilityAtMostOne correlationNonnegative correlationAtMostOne
  exact (not_lt_of_ge (hFloor.trans hTarget)) targetBelowFloor

/-- MSE after averaging `blocks` independent exchangeable blocks of the same
design.  Independence here is the product-channel contract formalized in
`ProductMeasureKL`; it is not inferred from metadata. -/
noncomputable def independentExchangeableBinaryMeanMSE
    (blocks raw failureProbability correlation : ℝ) : ℝ :=
  exchangeableBinaryMeanMSE raw failureProbability correlation / blocks

/-- Independent block replication divides the full correlated-block MSE by
the number of blocks. -/
theorem independentExchangeableBinaryMeanMSE_formula
    (blocks raw failureProbability correlation : ℝ) :
    independentExchangeableBinaryMeanMSE
      blocks raw failureProbability correlation =
      exchangeableBinaryMeanMSE raw failureProbability correlation / blocks := rfl

/-- A concrete sufficient block-count rule for any positive MSE target. -/
theorem independentExchangeableBinary_blocks_sufficient
    (blocks raw failureProbability correlation target : ℝ)
    (blocksPositive : 0 < blocks)
    (requiredBudget :
      exchangeableBinaryMeanMSE raw failureProbability correlation ≤
        blocks * target) :
    independentExchangeableBinaryMeanMSE
      blocks raw failureProbability correlation ≤ target := by
  exact (div_le_iff₀ blocksPositive).2 (by simpa [mul_comm] using requiredBudget)

/-- Provided a block MSE is nonnegative, independent replication can achieve
every positive MSE target.  This positive theorem complements the one-block
no-go theorem. -/
theorem exists_independentExchangeableBinary_blocks_for_target
    (raw failureProbability correlation target : ℝ)
    (blockMSENonnegative :
      0 ≤ exchangeableBinaryMeanMSE raw failureProbability correlation)
    (targetPositive : 0 < target) :
    ∃ blocks : ℝ, 0 < blocks ∧
      independentExchangeableBinaryMeanMSE
        blocks raw failureProbability correlation ≤ target := by
  let blocks :=
    exchangeableBinaryMeanMSE raw failureProbability correlation / target + 1
  have blocksPositive : 0 < blocks := by
    dsimp [blocks]
    positivity
  refine ⟨blocks, blocksPositive, ?_⟩
  apply independentExchangeableBinary_blocks_sufficient
    blocks raw failureProbability correlation target blocksPositive
  dsimp [blocks]
  have targetNonnegative : 0 ≤ target := targetPositive.le
  rw [add_mul, div_mul_cancel₀ _ targetPositive.ne', one_mul]
  exact le_add_of_nonneg_right targetNonnegative

/-- Exact inversion of the exchangeable second-moment law: for a block size
strictly greater than one and nonzero Bernoulli variance, the observed MSE
determines the implied intraclass correlation. -/
theorem exchangeableBinary_impliedCorrelation_exact
    (raw failureProbability correlation observedMSE : ℝ)
    (rawGreaterThanOne : 1 < raw)
    (bernoulliVarianceNonzero :
      failureProbability * (1 - failureProbability) ≠ 0)
    (observedLaw :
      observedMSE = exchangeableBinaryMeanMSE
        raw failureProbability correlation) :
    correlation =
      (raw * observedMSE /
          (failureProbability * (1 - failureProbability)) - 1) /
        (raw - 1) := by
  have rawNonzero : raw ≠ 0 := ne_of_gt (lt_trans zero_lt_one rawGreaterThanOne)
  have rawMinusOneNonzero : raw - 1 ≠ 0 := sub_ne_zero.mpr rawGreaterThanOne.ne'
  have scaledLaw :
      raw * observedMSE /
          (failureProbability * (1 - failureProbability)) =
        1 + (raw - 1) * correlation := by
    rw [observedLaw, exchangeableBinaryMeanMSE]
    field_simp [rawNonzero]
    exact mul_div_cancel_left₀ _ bernoulliVarianceNonzero
  rw [scaledLaw]
  field_simp [rawMinusOneNonzero]
  ring

/-- Operational concentration bridge.  Any concrete failure-rate estimator
whose variance is certified by the independent-block MSE law inherits this
Chebyshev deviation bound. -/
theorem independentExchangeableBinary_chebyshev_bound
    {Omega : Type*} [MeasurableSpace Omega]
    (mu : Measure Omega) [IsFiniteMeasure mu]
    (failureRateEstimator : Omega → ℝ)
    (estimatorMemLp : MemLp failureRateEstimator 2 mu)
    (blocks raw failureProbability correlation epsilon : ℝ)
    (epsilonPositive : 0 < epsilon)
    (varianceLaw :
      variance failureRateEstimator mu =
        independentExchangeableBinaryMeanMSE
          blocks raw failureProbability correlation) :
    mu {ω | epsilon ≤
        |failureRateEstimator ω - mu[failureRateEstimator]|} ≤
      ENNReal.ofReal
        (independentExchangeableBinaryMeanMSE
          blocks raw failureProbability correlation / epsilon ^ 2) := by
  simpa [varianceLaw] using
    meas_ge_le_variance_div_sq estimatorMemLp epsilonPositive

/-- A fully numerical acceptance rule: if certified estimator MSE is at most
`delta * epsilon²`, its probability of an absolute error at least `epsilon`
is at most `ofReal delta`. -/
theorem independentExchangeableBinary_probability_target
    {Omega : Type*} [MeasurableSpace Omega]
    (mu : Measure Omega) [IsFiniteMeasure mu]
    (failureRateEstimator : Omega → ℝ)
    (estimatorMemLp : MemLp failureRateEstimator 2 mu)
    (blocks raw failureProbability correlation epsilon delta : ℝ)
    (epsilonPositive : 0 < epsilon)
    (varianceLaw :
      variance failureRateEstimator mu =
        independentExchangeableBinaryMeanMSE
          blocks raw failureProbability correlation)
    (mseBudget :
      independentExchangeableBinaryMeanMSE
          blocks raw failureProbability correlation ≤
        delta * epsilon ^ 2) :
    mu {ω | epsilon ≤
        |failureRateEstimator ω - mu[failureRateEstimator]|} ≤
      ENNReal.ofReal delta := by
  calc
    mu {ω | epsilon ≤
        |failureRateEstimator ω - mu[failureRateEstimator]|} ≤
        ENNReal.ofReal
          (independentExchangeableBinaryMeanMSE
            blocks raw failureProbability correlation / epsilon ^ 2) :=
      independentExchangeableBinary_chebyshev_bound
        mu failureRateEstimator estimatorMemLp blocks raw failureProbability
          correlation epsilon epsilonPositive varianceLaw
    _ ≤ ENNReal.ofReal delta := by
      apply ENNReal.ofReal_le_ofReal
      exact (div_le_iff₀ (sq_pos_of_pos epsilonPositive)).2 mseBudget

end OCKIndividuationMSpaceComposition
