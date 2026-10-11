import OCKIndividuationMSpaceComposition.TargetBlindConfidenceAllocation
import OCKIndividuationMSpaceComposition.DependentPopulationObservationBounds

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Sample complexity of a registered stochastic forecast envelope

This module inverts the finite-alphabet radius used by the M3 adapter.  It
separates reducible statistical width from the structural validation and
transport terms.  The inversion is exact for the registered Weissman-style
certificate; it is not an information-theoretic lower bound over every
possible estimator.
-/

/-- Independent-equivalent sample count required by the registered raw TV
radius to reach `epsilon`. -/
noncomputable def weissmanRequiredIndependentCount
    (categoryFactor alpha epsilon : ℝ) : ℝ :=
  Real.log (categoryFactor / alpha) / (2 * epsilon ^ 2)

/-- Exact inversion of the registered radius: enough independent-equivalent
observations make the raw radius no larger than `epsilon`. -/
theorem weissman_sample_threshold_guarantees_radius
    (categoryFactor alpha epsilon observations : ℝ)
    (epsilonPositive : 0 < epsilon)
    (observationsPositive : 0 < observations)
    (ratioAtLeastOne : 1 ≤ categoryFactor / alpha)
    (enough :
      weissmanRequiredIndependentCount categoryFactor alpha epsilon ≤
        observations) :
    weissmanTVRadius categoryFactor observations alpha ≤ epsilon := by
  have logNonnegative : 0 ≤ Real.log (categoryFactor / alpha) :=
    Real.log_nonneg ratioAtLeastOne
  have epsilonDenominatorPositive : 0 < 2 * epsilon ^ 2 := by positivity
  have observationDenominatorPositive : 0 < 2 * observations := by positivity
  have scaledEnough :
      Real.log (categoryFactor / alpha) ≤
        observations * (2 * epsilon ^ 2) := by
    exact (div_le_iff₀ epsilonDenominatorPositive).mp
      (by simpa [weissmanRequiredIndependentCount] using enough)
  apply (Real.sqrt_le_iff).2
  refine ⟨epsilonPositive.le, ?_⟩
  apply (div_le_iff₀ observationDenominatorPositive).2
  nlinarith

/-- Required count is strictly positive in the non-vacuous regime
`categoryFactor/alpha > 1`. -/
theorem weissmanRequiredIndependentCount_positive
    (categoryFactor alpha epsilon : ℝ)
    (epsilonPositive : 0 < epsilon)
    (ratioGreaterThanOne : 1 < categoryFactor / alpha) :
    0 < weissmanRequiredIndependentCount categoryFactor alpha epsilon := by
  unfold weissmanRequiredIndependentCount
  exact div_pos (Real.log_pos ratioGreaterThanOne) (by positivity)

/-- A registered design effect converts the independent-equivalent quota
into a raw trace quota. -/
theorem designEffect_raw_threshold_guarantees_weissman_radius
    (categoryFactor alpha epsilon raw designEffect : ℝ)
    (epsilonPositive : 0 < epsilon)
    (designEffectPositive : 0 < designEffect)
    (ratioGreaterThanOne : 1 < categoryFactor / alpha)
    (enoughRaw :
      designEffect *
          weissmanRequiredIndependentCount categoryFactor alpha epsilon ≤ raw) :
    weissmanTVRadius categoryFactor
        (designEffectEffectiveObservations raw designEffect) alpha ≤ epsilon := by
  have requiredPositive := weissmanRequiredIndependentCount_positive
    categoryFactor alpha epsilon epsilonPositive ratioGreaterThanOne
  have rawPositive : 0 < raw := by
    have productPositive :
        0 < designEffect *
          weissmanRequiredIndependentCount categoryFactor alpha epsilon :=
      mul_pos designEffectPositive requiredPositive
    exact lt_of_lt_of_le productPositive enoughRaw
  apply weissman_sample_threshold_guarantees_radius
    categoryFactor alpha epsilon
    (designEffectEffectiveObservations raw designEffect)
    epsilonPositive
  · exact div_pos rawPositive designEffectPositive
  · exact ratioGreaterThanOne.le
  · rw [designEffectEffectiveObservations]
    exact (le_div_iff₀ designEffectPositive).2
      (by simpa [mul_comm] using enoughRaw)

/-- Weighted validation-plus-prospective statistical contribution to one
registered aggregate forecast envelope. -/
noncomputable def weightedTwoSampleRadius
    {Index : Type*} [Fintype Index]
    (weight validationRadius prospectiveRadius : Index → ℝ) : ℝ :=
  ∑ index, weight index *
    (validationRadius index + prospectiveRadius index)

/-- If both row radii are at most half the aggregate statistical budget, a
normalized nonnegative mixture spends no more than that budget. -/
theorem weightedTwoSampleRadius_le_budget
    {Index : Type*} [Fintype Index]
    (weight validationRadius prospectiveRadius : Index → ℝ)
    (budget : ℝ)
    (weightNonnegative : ∀ index, 0 ≤ weight index)
    (weightNormalized : (∑ index, weight index) = 1)
    (validationBound : ∀ index, validationRadius index ≤ budget / 2)
    (prospectiveBound : ∀ index, prospectiveRadius index ≤ budget / 2) :
    weightedTwoSampleRadius weight validationRadius prospectiveRadius ≤
      budget := by
  unfold weightedTwoSampleRadius
  calc
    (∑ index, weight index *
      (validationRadius index + prospectiveRadius index)) ≤
        ∑ index, weight index * budget := by
      apply Finset.sum_le_sum
      intro index _
      apply mul_le_mul_of_nonneg_left _ (weightNonnegative index)
      linarith [validationBound index, prospectiveBound index]
    _ = (∑ index, weight index) * budget := by
      rw [Finset.sum_mul]
    _ = budget := by rw [weightNormalized, one_mul]

/-- End-to-end count rule for the statistical part of a two-sample aggregate
forecast certificate.  Each alpha and sample size may be row-specific. -/
theorem rowwise_sample_thresholds_guarantee_aggregate_statistical_budget
    {Index : Type*} [Fintype Index]
    (weight categoryFactor validationAlpha prospectiveAlpha : Index → ℝ)
    (validationObservations prospectiveObservations : Index → ℝ)
    (budget : ℝ)
    (budgetPositive : 0 < budget)
    (weightNonnegative : ∀ index, 0 ≤ weight index)
    (weightNormalized : (∑ index, weight index) = 1)
    (validationObservationsPositive :
      ∀ index, 0 < validationObservations index)
    (prospectiveObservationsPositive :
      ∀ index, 0 < prospectiveObservations index)
    (validationRatio :
      ∀ index, 1 ≤ categoryFactor index / validationAlpha index)
    (prospectiveRatio :
      ∀ index, 1 ≤ categoryFactor index / prospectiveAlpha index)
    (validationEnough : ∀ index,
      weissmanRequiredIndependentCount
          (categoryFactor index) (validationAlpha index) (budget / 2) ≤
        validationObservations index)
    (prospectiveEnough : ∀ index,
      weissmanRequiredIndependentCount
          (categoryFactor index) (prospectiveAlpha index) (budget / 2) ≤
        prospectiveObservations index) :
    weightedTwoSampleRadius weight
        (fun index => weissmanTVRadius
          (categoryFactor index) (validationObservations index)
          (validationAlpha index))
        (fun index => weissmanTVRadius
          (categoryFactor index) (prospectiveObservations index)
          (prospectiveAlpha index)) ≤ budget := by
  apply weightedTwoSampleRadius_le_budget
    weight
    (fun index => weissmanTVRadius
      (categoryFactor index) (validationObservations index)
      (validationAlpha index))
    (fun index => weissmanTVRadius
      (categoryFactor index) (prospectiveObservations index)
      (prospectiveAlpha index))
    budget weightNonnegative weightNormalized
  · intro index
    exact weissman_sample_threshold_guarantees_radius
      (categoryFactor index) (validationAlpha index) (budget / 2)
      (validationObservations index) (by positivity)
      (validationObservationsPositive index) (validationRatio index)
      (validationEnough index)
  · intro index
    exact weissman_sample_threshold_guarantees_radius
      (categoryFactor index) (prospectiveAlpha index) (budget / 2)
      (prospectiveObservations index) (by positivity)
      (prospectiveObservationsPositive index) (prospectiveRatio index)
      (prospectiveEnough index)

/-- Complete registered envelope = structural validation/transport base plus
reducible statistical radius. -/
noncomputable def registeredForecastEnvelope
    (structuralBase statisticalRadius : ℝ) : ℝ :=
  structuralBase + statisticalRadius

/-- A residual statistical budget closes a desired total target whenever the
structural base plus that budget lies below the target. -/
theorem residual_statistical_budget_guarantees_total_forecast_target
    (structuralBase statisticalRadius statisticalBudget target : ℝ)
    (statisticalBound : statisticalRadius ≤ statisticalBudget)
    (budgetFits : structuralBase + statisticalBudget ≤ target) :
    registeredForecastEnvelope structuralBase statisticalRadius ≤ target := by
  unfold registeredForecastEnvelope
  linarith

/-- Structural floor: nonnegative statistical width can never make the
registered envelope smaller than its validation/transport base. -/
theorem structuralBase_le_registeredForecastEnvelope
    (structuralBase statisticalRadius : ℝ)
    (statisticalNonnegative : 0 ≤ statisticalRadius) :
    structuralBase ≤
      registeredForecastEnvelope structuralBase statisticalRadius := by
  unfold registeredForecastEnvelope
  linarith

/-- No-go: if the desired target is already below the structural base, no
amount of sampling can make this registered certificate meet it.  The model or
state map must change; collecting more identical data is not a repair. -/
theorem target_below_structuralBase_is_unreachable_by_sampling
    (structuralBase statisticalRadius target : ℝ)
    (statisticalNonnegative : 0 ≤ statisticalRadius)
    (targetBelowBase : target < structuralBase) :
    ¬ registeredForecastEnvelope structuralBase statisticalRadius ≤ target := by
  intro claimed
  have floor := structuralBase_le_registeredForecastEnvelope
    structuralBase statisticalRadius statisticalNonnegative
  linarith

/-- No finite raw trace count satisfies the registered positive-radius quota
uniformly over all positive design effects.  A dependence bound or independent
block structure is logically required. -/
theorem no_finite_raw_uniform_weissman_quota_without_designEffect_bound
    (categoryFactor alpha epsilon raw : ℝ)
    (epsilonPositive : 0 < epsilon)
    (ratioGreaterThanOne : 1 < categoryFactor / alpha) :
    ¬ ∀ designEffect : ℝ, 0 < designEffect →
        designEffect *
          weissmanRequiredIndependentCount categoryFactor alpha epsilon ≤ raw := by
  exact no_finite_raw_meets_all_positive_designEffects raw
    (weissmanRequiredIndependentCount categoryFactor alpha epsilon)
    (weissmanRequiredIndependentCount_positive
      categoryFactor alpha epsilon epsilonPositive ratioGreaterThanOne)

end OCKIndividuationMSpaceComposition
