import OCKIndividuationMSpaceComposition.PopulationObservationBounds
import OCKIndividuationMSpaceComposition.DependentInformationBudget

namespace OCKIndividuationMSpaceComposition

/-!
## Population learning under an explicit dependence budget

`PopulationObservationBounds` identifies the independent-equivalent sample
budget needed for uniform learning.  `DependentInformationBudget` identifies
the exact effective count of an exchangeable correlated block.  This module
closes the bridge between them.

The bridge deliberately distinguishes raw event count from effective
information.  A finite raw count is sufficient only after an upper dependence
budget has been registered.  If that budget is unbounded, no finite raw count
can guarantee a positive effective-information target.  For persistent
exchangeable correlation the stronger one-block ceiling is exact.
-/

/-- Independent-equivalent observations after applying a positive design
effect (variance/information inflation factor). -/
noncomputable def designEffectEffectiveObservations
    (raw designEffect : ℝ) : ℝ :=
  raw / designEffect

/-- Effective observations required by the two-sided finite-hypothesis
population concentration surface. -/
noncomputable def populationRequiredEffectiveObservations
    (hypothesisCount : ℕ) (epsilon delta : ℝ) : ℝ :=
  requiredRealObservations
    (2 * (hypothesisCount : ℝ)) delta (2 * epsilon ^ 2)

/-- Population error surface after replacing raw events by their registered
independent-equivalent count. -/
noncomputable def designEffectPopulationBudget
    (hypothesisCount : ℕ) (raw designEffect epsilon : ℝ) : ℝ :=
  exponentialUnionBudget
    (2 * (hypothesisCount : ℝ))
    (designEffectEffectiveObservations raw designEffect)
    (2 * epsilon ^ 2)

/-- The required effective count is strictly positive under the ordinary
non-vacuous confidence regime `delta < 2H`. -/
theorem populationRequiredEffectiveObservations_positive
    (hypothesisCount : ℕ) (epsilon delta : ℝ)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (deltaBelowFamily : delta < 2 * (hypothesisCount : ℝ)) :
    0 < populationRequiredEffectiveObservations
      hypothesisCount epsilon delta := by
  have familyPositive : 0 < 2 * (hypothesisCount : ℝ) := by
    have countPositive : 0 < (hypothesisCount : ℝ) := by
      exact_mod_cast hypothesisCountPositive
    positivity
  have ratioGreaterThanOne :
      1 < (2 * (hypothesisCount : ℝ)) / delta :=
    (one_lt_div deltaPositive).mpr deltaBelowFamily
  have exponentPositive : 0 < 2 * epsilon ^ 2 := by positivity
  rw [populationRequiredEffectiveObservations, requiredRealObservations]
  exact div_pos (Real.log_pos ratioGreaterThanOne) exponentPositive

/-- A raw count equal to `designEffect` times the required effective count is
sufficient for the declared population error budget. -/
theorem designEffect_raw_threshold_guarantees_population_budget
    (hypothesisCount : ℕ) (epsilon delta raw designEffect : ℝ)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (designEffectPositive : 0 < designEffect)
    (enoughRaw :
      designEffect *
          populationRequiredEffectiveObservations
            hypothesisCount epsilon delta ≤ raw) :
    designEffectPopulationBudget
        hypothesisCount raw designEffect epsilon ≤ delta := by
  have countPositive : 0 < (hypothesisCount : ℝ) := by
    exact_mod_cast hypothesisCountPositive
  have familyPositive : 0 < 2 * (hypothesisCount : ℝ) := by positivity
  have exponentPositive : 0 < 2 * epsilon ^ 2 := by positivity
  apply requiredRealObservations_guarantees_budget
    (2 * (hypothesisCount : ℝ)) delta (2 * epsilon ^ 2)
    (designEffectEffectiveObservations raw designEffect)
    familyPositive deltaPositive exponentPositive
  rw [populationRequiredEffectiveObservations] at enoughRaw
  rw [designEffectEffectiveObservations]
  apply (le_div_iff₀ designEffectPositive).2
  simpa [mul_comm] using enoughRaw

/-- The design-effect surface reduces exactly to the independent population
surface at design effect one. -/
theorem designEffect_one_recovers_independent_population_budget
    (hypothesisCount : ℕ) (raw epsilon : ℝ) :
    designEffectPopulationBudget hypothesisCount raw 1 epsilon =
      exponentialUnionBudget
        (2 * (hypothesisCount : ℝ)) raw (2 * epsilon ^ 2) := by
  simp [designEffectPopulationBudget, designEffectEffectiveObservations]

/-- Designing at an upper confidence bound for the design effect remains
sufficient for every smaller actual design effect. -/
theorem upper_designEffect_threshold_is_robust
    (hypothesisCount : ℕ) (epsilon delta raw actual upper : ℝ)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (deltaBelowFamily : delta < 2 * (hypothesisCount : ℝ))
    (actualPositive : 0 < actual)
    (actualLeUpper : actual ≤ upper)
    (enoughAtUpper :
      upper * populationRequiredEffectiveObservations
        hypothesisCount epsilon delta ≤ raw) :
    designEffectPopulationBudget
        hypothesisCount raw actual epsilon ≤ delta := by
  have requiredPositive :=
    populationRequiredEffectiveObservations_positive
      hypothesisCount epsilon delta hypothesisCountPositive epsilonPositive
      deltaPositive deltaBelowFamily
  apply designEffect_raw_threshold_guarantees_population_budget
    hypothesisCount epsilon delta raw actual hypothesisCountPositive
    epsilonPositive deltaPositive actualPositive
  exact (mul_le_mul_of_nonneg_right actualLeUpper requiredPositive.le).trans
    enoughAtUpper

/-- Below the exact logarithmic effective-count threshold, the exponential
population budget is strictly worse than the requested target.  This is the
necessity counterpart to `requiredRealObservations_guarantees_budget`. -/
theorem observations_below_required_fail_exponential_budget
    (competitors targetError exponent observations : ℝ)
    (competitorsPositive : 0 < competitors)
    (targetPositive : 0 < targetError)
    (exponentPositive : 0 < exponent)
    (insufficient :
      observations <
        requiredRealObservations competitors targetError exponent) :
    targetError < exponentialUnionBudget competitors observations exponent := by
  have ratioPositive : 0 < competitors / targetError :=
    div_pos competitorsPositive targetPositive
  have scaledInsufficient :
      observations * exponent < Real.log (competitors / targetError) := by
    rw [requiredRealObservations] at insufficient
    exact (lt_div_iff₀ exponentPositive).mp insufficient
  have exponentialStrict :
      Real.exp (-Real.log (competitors / targetError)) <
        Real.exp (-observations * exponent) := by
    apply Real.exp_lt_exp.mpr
    linarith
  have inverseRatio :
      Real.exp (-Real.log (competitors / targetError)) =
        targetError / competitors := by
    rw [Real.exp_neg, Real.exp_log ratioPositive]
    field_simp
  rw [exponentialUnionBudget]
  rw [inverseRatio] at exponentialStrict
  have scaled := mul_lt_mul_of_pos_left exponentialStrict competitorsPositive
  field_simp at scaled
  simpa [neg_mul] using scaled

/-- Pure no-go theorem: if a positive effective-information target is fixed
but the design effect has no finite upper bound, no finite raw count can meet
the target uniformly over all positive design effects. -/
theorem no_finite_raw_meets_all_positive_designEffects
    (raw requiredEffective : ℝ)
    (requiredPositive : 0 < requiredEffective) :
    ¬ ∀ designEffect : ℝ, 0 < designEffect →
        designEffect * requiredEffective ≤ raw := by
  intro universalGuarantee
  let adversarialDesignEffect := (|raw| + 1) / requiredEffective
  have numeratorPositive : 0 < |raw| + 1 := by positivity
  have adversarialPositive : 0 < adversarialDesignEffect := by
    exact div_pos numeratorPositive requiredPositive
  have productIdentity :
      adversarialDesignEffect * requiredEffective = |raw| + 1 := by
    dsimp [adversarialDesignEffect]
    exact div_mul_cancel₀ (|raw| + 1) requiredPositive.ne'
  have rawStrictlyBelow : raw < |raw| + 1 := by
    linarith [le_abs_self raw]
  have claimed := universalGuarantee adversarialDesignEffect adversarialPositive
  rw [productIdentity] at claimed
  exact (not_lt_of_ge claimed) rawStrictlyBelow

/-- Specialized population version of the unbounded-dependence no-go. -/
theorem no_finite_raw_uniform_population_guarantee_without_dependence_bound
    (hypothesisCount : ℕ) (epsilon delta raw : ℝ)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (deltaBelowFamily : delta < 2 * (hypothesisCount : ℝ)) :
    ¬ ∀ designEffect : ℝ, 0 < designEffect →
        designEffect * populationRequiredEffectiveObservations
          hypothesisCount epsilon delta ≤ raw := by
  exact no_finite_raw_meets_all_positive_designEffects raw
    (populationRequiredEffectiveObservations hypothesisCount epsilon delta)
    (populationRequiredEffectiveObservations_positive
      hypothesisCount epsilon delta hypothesisCountPositive epsilonPositive
      deltaPositive deltaBelowFamily)

/-- The generic design-effect count is exactly the exchangeable effective
count when the design effect is `1 + (raw - 1) rho`. -/
theorem exchangeable_is_designEffect_model
    (raw correlation : ℝ) :
    designEffectEffectiveObservations raw
        (1 + (raw - 1) * correlation) =
      exchangeableEffectiveObservations raw correlation := rfl

/-- Exact population no-go for one persistently correlated exchangeable
block.  If the required effective count reaches the `1/rho` ceiling, every
finite positive raw block misses the requested population error target. -/
theorem exchangeable_singleBlock_population_target_impossible_at_ceiling
    (hypothesisCount : ℕ)
    (epsilon delta raw correlation : ℝ)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (rawPositive : 0 < raw)
    (correlationPositive : 0 < correlation)
    (correlationBelowOne : correlation < 1)
    (ceilingBelowRequired :
      1 / correlation ≤
        populationRequiredEffectiveObservations
          hypothesisCount epsilon delta) :
    delta < designEffectPopulationBudget hypothesisCount raw
      (1 + (raw - 1) * correlation) epsilon := by
  have insufficient :
      exchangeableEffectiveObservations raw correlation <
        populationRequiredEffectiveObservations
          hypothesisCount epsilon delta :=
    exchangeable_target_unreachable_at_dependence_ceiling
      raw correlation
      (populationRequiredEffectiveObservations
        hypothesisCount epsilon delta)
      rawPositive correlationPositive correlationBelowOne ceilingBelowRequired
  have countPositive : 0 < (hypothesisCount : ℝ) := by
    exact_mod_cast hypothesisCountPositive
  have familyPositive : 0 < 2 * (hypothesisCount : ℝ) := by positivity
  have exponentPositive : 0 < 2 * epsilon ^ 2 := by positivity
  have failed := observations_below_required_fail_exponential_budget
    (2 * (hypothesisCount : ℝ)) delta (2 * epsilon ^ 2)
    (exchangeableEffectiveObservations raw correlation)
    familyPositive deltaPositive exponentPositive
    (by simpa [populationRequiredEffectiveObservations] using insufficient)
  simpa [designEffectPopulationBudget, exchangeable_is_designEffect_model]
    using failed

/-- Independent blocks remove the one-block ceiling whenever their summed
effective count reaches the population requirement. -/
theorem independent_blocks_guarantee_population_budget
    (hypothesisCount : ℕ)
    (epsilon delta blocks blockSize correlation : ℝ)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (enoughEffective :
      populationRequiredEffectiveObservations
          hypothesisCount epsilon delta ≤
        independentBlockEffectiveObservations
          blocks blockSize correlation) :
    exponentialUnionBudget
        (2 * (hypothesisCount : ℝ))
        (independentBlockEffectiveObservations blocks blockSize correlation)
        (2 * epsilon ^ 2) ≤ delta := by
  have countPositive : 0 < (hypothesisCount : ℝ) := by
    exact_mod_cast hypothesisCountPositive
  apply requiredRealObservations_guarantees_budget
    (2 * (hypothesisCount : ℝ)) delta (2 * epsilon ^ 2)
    (independentBlockEffectiveObservations blocks blockSize correlation)
    (by positivity) deltaPositive (by positivity)
  simpa [populationRequiredEffectiveObservations] using enoughEffective

end OCKIndividuationMSpaceComposition
