import OCKIndividuationMSpaceComposition.CorrelatedBinaryFailureBudget

namespace OCKIndividuationMSpaceComposition

/-!
## Latent regimes as a source of dependence and avoidable forecast loss

This two-regime algebra is the smallest positive mechanism that explains the
Logion diagnostic: clustered binary errors and a drifting mean can be two
views of an omitted regime variable.  Observing the regime removes the
between-regime component; pooling cannot.
-/

/-- Pooled failure probability for a two-regime population. -/
noncomputable def twoRegimePooledProbability
    (weight firstProbability secondProbability : ℝ) : ℝ :=
  weight * firstProbability + (1 - weight) * secondProbability

/-- Variance of the latent regime-specific failure propensity. -/
noncomputable def twoRegimeBetweenVariance
    (weight firstProbability secondProbability : ℝ) : ℝ :=
  weight * (1 - weight) * (firstProbability - secondProbability) ^ 2

/-- Exact total-variance decomposition of a pooled Bernoulli observation. -/
theorem twoRegime_bernoulli_variance_decomposition
    (weight firstProbability secondProbability : ℝ) :
    twoRegimePooledProbability weight firstProbability secondProbability *
        (1 - twoRegimePooledProbability weight firstProbability secondProbability) =
      weight * firstProbability * (1 - firstProbability) +
        (1 - weight) * secondProbability * (1 - secondProbability) +
        twoRegimeBetweenVariance weight firstProbability secondProbability := by
  rw [twoRegimePooledProbability, twoRegimeBetweenVariance]
  ring

/-- The squared probability error paid by a pooled predictor, relative to a
regime-conditioned predictor, is exactly the between-regime variance. -/
theorem twoRegime_pooled_excess_brier_exact
    (weight firstProbability secondProbability : ℝ) :
    weight *
          (firstProbability -
            twoRegimePooledProbability weight firstProbability secondProbability) ^ 2 +
        (1 - weight) *
          (secondProbability -
            twoRegimePooledProbability weight firstProbability secondProbability) ^ 2 =
      twoRegimeBetweenVariance weight firstProbability secondProbability := by
  rw [twoRegimePooledProbability, twoRegimeBetweenVariance]
  ring

/-- With a nondegenerate regime mixture and genuinely different regime
failure probabilities, omitted-regime forecast loss is strictly positive. -/
theorem twoRegime_pooled_excess_brier_pos
    (weight firstProbability secondProbability : ℝ)
    (weightPositive : 0 < weight) (weightBelowOne : weight < 1)
    (regimesDiffer : firstProbability ≠ secondProbability) :
    0 < twoRegimeBetweenVariance weight firstProbability secondProbability := by
  rw [twoRegimeBetweenVariance]
  have hComplementPositive : 0 < 1 - weight := sub_pos.mpr weightBelowOne
  have hDifferenceSquaredPositive :
      0 < (firstProbability - secondProbability) ^ 2 :=
    sq_pos_of_ne_zero (sub_ne_zero.mpr regimesDiffer)
  exact mul_pos (mul_pos weightPositive hComplementPositive)
    hDifferenceSquaredPositive

/-- Under a nondegenerate mixture, the regime label has zero squared-error
predictive value exactly when the two conditional failure probabilities are
equal.  This is an operational sufficiency test, not a naming convention. -/
theorem twoRegime_betweenVariance_eq_zero_iff
    (weight firstProbability secondProbability : ℝ)
    (weightPositive : 0 < weight) (weightBelowOne : weight < 1) :
    twoRegimeBetweenVariance weight firstProbability secondProbability = 0 ↔
      firstProbability = secondProbability := by
  rw [twoRegimeBetweenVariance]
  have hWeightProductPositive : 0 < weight * (1 - weight) :=
    mul_pos weightPositive (sub_pos.mpr weightBelowOne)
  constructor
  · intro h
    have hSquare : (firstProbability - secondProbability) ^ 2 = 0 := by
      exact (mul_eq_zero.mp h).resolve_left hWeightProductPositive.ne'
    exact sub_eq_zero.mp (sq_eq_zero_iff.mp hSquare)
  · intro h
    rw [h]
    ring

/-- Net predictive value of recording a regime state after charging a
per-prediction acquisition and maintenance cost in the same Brier units. -/
noncomputable def twoRegimeNetCaptureValue
    (weight firstProbability secondProbability captureCost : ℝ) : ℝ :=
  twoRegimeBetweenVariance weight firstProbability secondProbability -
    captureCost

/-- Exact admission rule for a regime field: it improves net squared-error
value precisely when its acquisition cost is below the between-regime term. -/
theorem twoRegime_capture_value_positive_iff
    (weight firstProbability secondProbability captureCost : ℝ) :
    0 < twoRegimeNetCaptureValue weight firstProbability secondProbability
        captureCost ↔
      captureCost <
        twoRegimeBetweenVariance weight firstProbability secondProbability := by
  rw [twoRegimeNetCaptureValue]
  exact sub_pos

/-- Conversely, a state field whose cost reaches or exceeds its exact Brier
gain cannot improve the registered net objective. -/
theorem twoRegime_capture_value_nonpositive_iff
    (weight firstProbability secondProbability captureCost : ℝ) :
    twoRegimeNetCaptureValue weight firstProbability secondProbability
        captureCost ≤ 0 ↔
      twoRegimeBetweenVariance weight firstProbability secondProbability ≤
        captureCost := by
  rw [twoRegimeNetCaptureValue]
  exact sub_nonpos

/-- Two conditionally independent failures sharing the same latent regime
have covariance equal to the between-regime propensity variance. -/
theorem twoRegime_sharedLatent_covariance_exact
    (weight firstProbability secondProbability : ℝ) :
    (weight * firstProbability ^ 2 +
        (1 - weight) * secondProbability ^ 2) -
      twoRegimePooledProbability weight firstProbability secondProbability ^ 2 =
        twoRegimeBetweenVariance weight firstProbability secondProbability := by
  rw [twoRegimePooledProbability, twoRegimeBetweenVariance]
  ring

/-- Symmetric regime separation is invisible in the pooled one-event failure
probability. -/
theorem symmetricRegime_same_pooled_probability
    (pooled separation : ℝ) :
    twoRegimePooledProbability (1 / 2 : ℝ)
      (pooled + separation) (pooled - separation) = pooled := by
  rw [twoRegimePooledProbability]
  ring

/-- The same symmetric separation that is invisible in the marginal creates
strictly positive shared-regime covariance equal to `separation²`. -/
theorem symmetricRegime_hidden_covariance
    (pooled separation : ℝ) :
    twoRegimeBetweenVariance (1 / 2 : ℝ)
      (pooled + separation) (pooled - separation) = separation ^ 2 := by
  rw [twoRegimeBetweenVariance]
  ring

/-- No-go: a pooled one-event failure probability does not identify latent
regime dependence.  Any nonzero admissible symmetric separation gives the
same pooled probability but a different covariance. -/
theorem pooled_probability_does_not_identify_regime_covariance
    (pooled separation : ℝ) (separationNonzero : separation ≠ 0) :
    twoRegimePooledProbability (1 / 2 : ℝ)
        (pooled + separation) (pooled - separation) =
      twoRegimePooledProbability (1 / 2 : ℝ) pooled pooled ∧
    twoRegimeBetweenVariance (1 / 2 : ℝ)
        (pooled + separation) (pooled - separation) ≠
      twoRegimeBetweenVariance (1 / 2 : ℝ) pooled pooled := by
  constructor
  · rw [twoRegimePooledProbability, twoRegimePooledProbability]
    ring
  · rw [twoRegimeBetweenVariance, twoRegimeBetweenVariance]
    norm_num
    exact separationNonzero

end OCKIndividuationMSpaceComposition
