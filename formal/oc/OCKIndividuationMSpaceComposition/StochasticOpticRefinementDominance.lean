import OCKIndividuationMSpaceComposition.StochasticForecastSampleComplexity
import OCKIndividuationMSpaceComposition.StochasticObservationForecastMinimax

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe uWorld uCoarse uFine uOutcome

/-!
# Certified dominance and the optic refinement crossover

The module composes two previously separate facts:

* an aliased pair creates an algorithm-independent minimax floor for every
  forecast using the coarse observation; and
* a registered structural-plus-statistical envelope upper-bounds one chosen
  fine forecast.

If the fine upper certificate lies below the coarse minimax floor, the fine
forecast strictly beats every coarse-observation algorithm on that pair.  The
result is conditional but end-to-end: information class, achieved certificate,
sample budget and strict comparison all appear in one theorem.
-/

/-- Real-valued worst-case TV loss of one forecast on two possible worlds. -/
noncomputable def twoWorldForecastRisk
    {World : Type uWorld}
    {Observation : Type uCoarse}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome)
    (forecast : Observation → FiniteProbabilityMass Outcome)
    (left right : World) : ℝ :=
  max
    (finiteTotalVariation (law left) (forecast (observe left)) : ℝ)
    (finiteTotalVariation (law right) (forecast (observe right)) : ℝ)

/-- Real form of the universal same-observation minimax lower bound. -/
theorem observation_collision_real_risk_ge_half_separation
    {World : Type uWorld}
    {Observation : Type uCoarse}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome)
    (forecast : Observation → FiniteProbabilityMass Outcome)
    (left right : World)
    (collision : observe left = observe right) :
    (finiteTotalVariation (law left) (law right) : ℝ) / 2 ≤
      twoWorldForecastRisk observe law forecast left right := by
  have rationalLower := observation_collision_max_tv_error_ge_half_separation
    observe law forecast left right collision
  unfold twoWorldForecastRisk
  rw [show (finiteTotalVariation (law left) (law right) : ℝ) / 2 =
      ((finiteTotalVariation (law left) (law right) / 2 : ℚ) : ℝ) by
    norm_num]
  rw [← Rat.cast_max]
  exact (Rat.cast_le).2 rationalLower

/-- Exact algebraic crossover: a fine registered envelope is strictly smaller
exactly when its reduction in structural base exceeds its increase in
statistical width.  No monotonic-refinement shortcut is available. -/
theorem fine_envelope_improves_iff_structural_gain_exceeds_statistical_penalty
    (coarseStructural fineStructural coarseStatistical fineStatistical : ℝ) :
    registeredForecastEnvelope fineStructural fineStatistical <
        registeredForecastEnvelope coarseStructural coarseStatistical ↔
      coarseStructural - fineStructural >
        fineStatistical - coarseStatistical := by
  unfold registeredForecastEnvelope
  constructor <;> intro hypothesis <;> linarith

/-- Equality boundary of the optic crossover. -/
theorem fine_envelope_ties_iff_structural_gain_equals_statistical_penalty
    (coarseStructural fineStructural coarseStatistical fineStatistical : ℝ) :
    registeredForecastEnvelope fineStructural fineStatistical =
        registeredForecastEnvelope coarseStructural coarseStatistical ↔
      coarseStructural - fineStructural =
        fineStatistical - coarseStatistical := by
  unfold registeredForecastEnvelope
  constructor <;> intro hypothesis <;> linarith

/-- If the fine forecast's registered envelope lies below the coarse
same-observation minimax floor, it strictly dominates every coarse predictor
on the witnessed pair.  The fine observation is necessarily forced to split
that pair. -/
theorem certified_fine_forecast_strictly_dominates_coarse_observation_class
    {World : Type uWorld}
    {CoarseObservation : Type uCoarse}
    {FineObservation : Type uFine}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (coarseObserve : World → CoarseObservation)
    (fineObserve : World → FineObservation)
    (law : World → FiniteProbabilityMass Outcome)
    (fineForecast : FineObservation → FiniteProbabilityMass Outcome)
    (left right : World)
    (coarseCollision : coarseObserve left = coarseObserve right)
    (fineStructural fineStatistical statisticalBudget target : ℝ)
    (fineRiskBound :
      twoWorldForecastRisk fineObserve law fineForecast left right ≤
        registeredForecastEnvelope fineStructural fineStatistical)
    (statisticalBound : fineStatistical ≤ statisticalBudget)
    (budgetFits : fineStructural + statisticalBudget ≤ target)
    (targetBelowCoarseFloor :
      target < (finiteTotalVariation (law left) (law right) : ℝ) / 2) :
    fineObserve left ≠ fineObserve right ∧
      ∀ coarseForecast : CoarseObservation → FiniteProbabilityMass Outcome,
        twoWorldForecastRisk fineObserve law fineForecast left right <
          twoWorldForecastRisk coarseObserve law coarseForecast left right := by
  have fineEnvelopeBound :
      registeredForecastEnvelope fineStructural fineStatistical ≤ target :=
    residual_statistical_budget_guarantees_total_forecast_target
      fineStructural fineStatistical statisticalBudget target
      statisticalBound budgetFits
  have fineRiskBelowFloor :
      twoWorldForecastRisk fineObserve law fineForecast left right <
        (finiteTotalVariation (law left) (law right) : ℝ) / 2 :=
    lt_of_le_of_lt (fineRiskBound.trans fineEnvelopeBound)
      targetBelowCoarseFloor
  constructor
  · intro fineCollision
    have fineLower := observation_collision_real_risk_ge_half_separation
      fineObserve law fineForecast left right fineCollision
    exact (not_le_of_gt fineRiskBelowFloor) fineLower
  · intro coarseForecast
    have coarseLower := observation_collision_real_risk_ge_half_separation
      coarseObserve law coarseForecast left right coarseCollision
    exact lt_of_lt_of_le fineRiskBelowFloor coarseLower

/-- No-go dual: an optic that still aliases the witnessed pair cannot possess
a valid sub-minimax registered envelope for that pair. -/
theorem unresolved_fine_collision_blocks_subminimax_certificate
    {World : Type uWorld}
    {FineObservation : Type uFine}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (fineObserve : World → FineObservation)
    (law : World → FiniteProbabilityMass Outcome)
    (fineForecast : FineObservation → FiniteProbabilityMass Outcome)
    (left right : World)
    (fineCollision : fineObserve left = fineObserve right)
    (claimedEnvelope : ℝ)
    (claimedBelowFloor :
      claimedEnvelope < (finiteTotalVariation (law left) (law right) : ℝ) / 2) :
    ¬ twoWorldForecastRisk fineObserve law fineForecast left right ≤
        claimedEnvelope := by
  intro claimed
  have lower := observation_collision_real_risk_ge_half_separation
    fineObserve law fineForecast left right fineCollision
  exact (not_le_of_gt claimedBelowFloor) (lower.trans claimed)

/-- A four-number counterexample family shows why structural refinement alone
cannot determine the preferred finite-sample optic: the same positive
structural gain can either help or hurt depending on the statistical penalty. -/
theorem same_structural_gain_supports_opposite_refinement_decisions :
    let coarseStructural : ℝ := 3
    let fineStructural : ℝ := 1
    let coarseStatistical : ℝ := 1
    let helpfulFineStatistical : ℝ := 2
    let harmfulFineStatistical : ℝ := 4
    coarseStructural - fineStructural = 2 ∧
      registeredForecastEnvelope fineStructural helpfulFineStatistical <
        registeredForecastEnvelope coarseStructural coarseStatistical ∧
      registeredForecastEnvelope coarseStructural coarseStatistical <
        registeredForecastEnvelope fineStructural harmfulFineStatistical := by
  norm_num [registeredForecastEnvelope]

end OCKIndividuationMSpaceComposition
