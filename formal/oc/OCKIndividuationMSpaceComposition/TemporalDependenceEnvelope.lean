import OCKIndividuationMSpaceComposition.DependentPopulationObservationBounds

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
## Finite temporal-dependence envelopes with an explicit tail budget

For a finite registered family of lags, a design effect has the generic form

`1 + 2 * sum_l weight_l * correlation_l`.

The ordinary stationary-mean weights `1 - lag / n` are one instance.  Keeping
the weights abstract makes the bridge applicable to irregular cadence,
blocked capture and domain-specific covariance estimators.  The theorem
surface requires the weights and tail envelope to be registered explicitly.
-/

/-- Finite integrated-dependence factor for a registered lag family. -/
noncomputable def temporalDesignEffect
    {Lag : Type*} [Fintype Lag]
    (weight correlation : Lag → ℝ) : ℝ :=
  1 + 2 * ∑ lag, weight lag * correlation lag

/-- Nonnegative weights and correlations make the temporal design effect at
least the independent value one. -/
theorem temporalDesignEffect_at_least_one
    {Lag : Type*} [Fintype Lag]
    (weight correlation : Lag → ℝ)
    (weightNonnegative : ∀ lag, 0 ≤ weight lag)
    (correlationNonnegative : ∀ lag, 0 ≤ correlation lag) :
    1 ≤ temporalDesignEffect weight correlation := by
  have termsNonnegative :
      0 ≤ ∑ lag, weight lag * correlation lag := by
    exact Finset.sum_nonneg fun lag _ =>
      mul_nonneg (weightNonnegative lag) (correlationNonnegative lag)
  unfold temporalDesignEffect
  linarith

/-- Pointwise larger nonnegative-weight correlation envelopes produce larger
design effects. -/
theorem temporalDesignEffect_mono_correlation
    {Lag : Type*} [Fintype Lag]
    (weight first second : Lag → ℝ)
    (weightNonnegative : ∀ lag, 0 ≤ weight lag)
    (correlationOrder : ∀ lag, first lag ≤ second lag) :
    temporalDesignEffect weight first ≤ temporalDesignEffect weight second := by
  have sumOrder :
      (∑ lag, weight lag * first lag) ≤
        ∑ lag, weight lag * second lag := by
    apply Finset.sum_le_sum
    intro lag _
    exact mul_le_mul_of_nonneg_left
      (correlationOrder lag) (weightNonnegative lag)
  unfold temporalDesignEffect
  linarith

/-- Exact decomposition into a captured lag profile and an omitted residual
profile. -/
theorem temporalDesignEffect_additive_tail
    {Lag : Type*} [Fintype Lag]
    (weight captured tail : Lag → ℝ) :
    temporalDesignEffect weight (fun lag => captured lag + tail lag) =
      temporalDesignEffect weight captured +
        2 * ∑ lag, weight lag * tail lag := by
  simp only [temporalDesignEffect, mul_add, Finset.sum_add_distrib]
  ring

/-- A pointwise residual envelope plus a scalar weighted-tail budget gives a
valid upper design effect for the complete temporal process. -/
theorem temporalDesignEffect_le_captured_add_tailBudget
    {Lag : Type*} [Fintype Lag]
    (weight actual captured residualUpper : Lag → ℝ)
    (tailBudget : ℝ)
    (weightNonnegative : ∀ lag, 0 ≤ weight lag)
    (pointwiseEnvelope :
      ∀ lag, actual lag ≤ captured lag + residualUpper lag)
    (weightedTailBound :
      (∑ lag, weight lag * residualUpper lag) ≤ tailBudget) :
    temporalDesignEffect weight actual ≤
      temporalDesignEffect weight captured + 2 * tailBudget := by
  calc
    temporalDesignEffect weight actual ≤
        temporalDesignEffect weight
          (fun lag => captured lag + residualUpper lag) :=
      temporalDesignEffect_mono_correlation
        weight actual (fun lag => captured lag + residualUpper lag)
        weightNonnegative pointwiseEnvelope
    _ = temporalDesignEffect weight captured +
        2 * ∑ lag, weight lag * residualUpper lag :=
      temporalDesignEffect_additive_tail weight captured residualUpper
    _ ≤ temporalDesignEffect weight captured + 2 * tailBudget := by
      linarith

/-- Omitting a strictly positive weighted residual tail strictly
underestimates temporal dependence. -/
theorem positive_omitted_tail_strictly_increases_designEffect
    {Lag : Type*} [Fintype Lag]
    (weight captured tail : Lag → ℝ)
    (positiveTail : 0 < ∑ lag, weight lag * tail lag) :
    temporalDesignEffect weight captured <
      temporalDesignEffect weight (fun lag => captured lag + tail lag) := by
  rw [temporalDesignEffect_additive_tail]
  linarith

/-- End-to-end positive theorem: a captured finite-lag profile plus a valid
tail budget supplies a conservative population-learning quota. -/
theorem temporal_tail_corrected_raw_threshold_guarantees_population_budget
    {Lag : Type*} [Fintype Lag]
    (weight actual captured residualUpper : Lag → ℝ)
    (hypothesisCount : ℕ)
    (epsilon delta raw tailBudget : ℝ)
    (weightNonnegative : ∀ lag, 0 ≤ weight lag)
    (pointwiseEnvelope :
      ∀ lag, actual lag ≤ captured lag + residualUpper lag)
    (weightedTailBound :
      (∑ lag, weight lag * residualUpper lag) ≤ tailBudget)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (deltaBelowFamily : delta < 2 * (hypothesisCount : ℝ))
    (actualDesignEffectPositive :
      0 < temporalDesignEffect weight actual)
    (enoughRaw :
      (temporalDesignEffect weight captured + 2 * tailBudget) *
          populationRequiredEffectiveObservations
            hypothesisCount epsilon delta ≤ raw) :
    designEffectPopulationBudget hypothesisCount raw
        (temporalDesignEffect weight actual) epsilon ≤ delta := by
  have upperBound := temporalDesignEffect_le_captured_add_tailBudget
    weight actual captured residualUpper tailBudget weightNonnegative
    pointwiseEnvelope weightedTailBound
  exact upper_designEffect_threshold_is_robust
    hypothesisCount epsilon delta raw
    (temporalDesignEffect weight actual)
    (temporalDesignEffect weight captured + 2 * tailBudget)
    hypothesisCountPositive epsilonPositive deltaPositive deltaBelowFamily
    actualDesignEffectPositive upperBound enoughRaw

/-- Operational no-go: a truncated dependence estimate can satisfy its own
raw quota while the true design effect strictly violates the requested error
target.  A tail bound is therefore logically necessary, not merely a
conservative reporting preference. -/
theorem underestimated_temporalDesignEffect_can_false_accept
    (hypothesisCount : ℕ)
    (epsilon delta raw truncatedEffect actualEffect : ℝ)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (actualEffectPositive : 0 < actualEffect)
    (truncatedRuleAccepts :
      truncatedEffect * populationRequiredEffectiveObservations
        hypothesisCount epsilon delta ≤ raw)
    (actualRuleFails :
      raw < actualEffect * populationRequiredEffectiveObservations
        hypothesisCount epsilon delta) :
    truncatedEffect * populationRequiredEffectiveObservations
        hypothesisCount epsilon delta ≤ raw ∧
      delta < designEffectPopulationBudget
        hypothesisCount raw actualEffect epsilon := by
  refine ⟨truncatedRuleAccepts, ?_⟩
  have effectiveInsufficient :
      designEffectEffectiveObservations raw actualEffect <
        populationRequiredEffectiveObservations
          hypothesisCount epsilon delta := by
    rw [designEffectEffectiveObservations]
    exact (div_lt_iff₀ actualEffectPositive).2 (by
      simpa [mul_comm] using actualRuleFails)
  have countPositive : 0 < (hypothesisCount : ℝ) := by
    exact_mod_cast hypothesisCountPositive
  have failed := observations_below_required_fail_exponential_budget
    (2 * (hypothesisCount : ℝ)) delta (2 * epsilon ^ 2)
    (designEffectEffectiveObservations raw actualEffect)
    (by positivity) deltaPositive (by positivity)
    (by simpa [populationRequiredEffectiveObservations] using
      effectiveInsufficient)
  simpa [designEffectPopulationBudget] using failed

/-- Exact false-accept bridge for a positive omitted lag tail.  It exposes the
interval of raw counts where a truncated rule passes but the complete rule
must fail. -/
theorem positive_omitted_tail_creates_false_acceptance_interval
    {Lag : Type*} [Fintype Lag]
    (weight captured tail : Lag → ℝ)
    (hypothesisCount : ℕ)
    (epsilon delta raw : ℝ)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (completeEffectPositive :
      0 < temporalDesignEffect weight (fun lag => captured lag + tail lag))
    (positiveTail : 0 < ∑ lag, weight lag * tail lag)
    (truncatedRuleAccepts :
      temporalDesignEffect weight captured *
          populationRequiredEffectiveObservations
            hypothesisCount epsilon delta ≤ raw)
    (completeRuleFails :
      raw < temporalDesignEffect weight (fun lag => captured lag + tail lag) *
        populationRequiredEffectiveObservations
          hypothesisCount epsilon delta) :
    temporalDesignEffect weight captured <
        temporalDesignEffect weight (fun lag => captured lag + tail lag) ∧
      delta < designEffectPopulationBudget hypothesisCount raw
        (temporalDesignEffect weight (fun lag => captured lag + tail lag))
        epsilon := by
  refine ⟨positive_omitted_tail_strictly_increases_designEffect
      weight captured tail positiveTail, ?_⟩
  exact (underestimated_temporalDesignEffect_can_false_accept
    hypothesisCount epsilon delta raw
    (temporalDesignEffect weight captured)
    (temporalDesignEffect weight (fun lag => captured lag + tail lag))
    hypothesisCountPositive epsilonPositive deltaPositive
    completeEffectPositive truncatedRuleAccepts completeRuleFails).2

end OCKIndividuationMSpaceComposition
