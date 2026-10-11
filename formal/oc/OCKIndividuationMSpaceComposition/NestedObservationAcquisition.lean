import OCKIndividuationMSpaceComposition.ContextTypingRefinement
import OCKIndividuationMSpaceComposition.ForecastOriginObservationCeiling
import OCKIndividuationMSpaceComposition.SemanticPredictionContract

namespace OCKIndividuationMSpaceComposition

/-!
# Nested observation acquisition and forecast-origin delay

An observation origin is an operational choice, not merely a column subset.
This module records a nested stream of observations, reuses the mature
refinement/risk result, and adds the OC decision boundary: information gained by
waiting must pay for its declared latency cost.  It also preserves a sharp
no-go: a target distinction unsplit at a later origin was necessarily unsplit at
every earlier origin.
-/

universe uState uObservation uPrediction

/-- A time-indexed observation schedule.  A later observation must explicitly
collapse to every earlier observation; adding a timestamp or a feature name is
not sufficient evidence of refinement. -/
structure NestedObservationSchedule
    (State : Type uState) (Observation : Nat → Type uObservation) where
  observe : (origin : Nat) → State → Observation origin
  collapse : ∀ {early late : Nat}, early ≤ late →
    Observation late → Observation early
  factor : ∀ {early late : Nat} (ordered : early ≤ late) (state : State),
    observe early state = collapse ordered (observe late state)

namespace NestedObservationSchedule

/-- The declared late observation refines the declared early observation. -/
def refinement
    {State : Type uState} {Observation : Nat → Type uObservation}
    (schedule : NestedObservationSchedule State Observation)
    {early late : Nat} (ordered : early ≤ late) :
    ContextObservationRefinement
      (schedule.observe early) (schedule.observe late) where
  collapse := schedule.collapse ordered
  factor := schedule.factor ordered

/-- Predictors admissible at an origin factor through precisely that origin's
observation, rather than through an eventually available trace. -/
def FactorsAt
    {State : Type uState} {Observation : Nat → Type uObservation}
    {Prediction : Type uPrediction}
    (schedule : NestedObservationSchedule State Observation)
    (origin : Nat) (predictor : State → Prediction) : Prop :=
  FactorsThrough (schedule.observe origin) predictor

/-- Any predictor available earlier remains available later by explicit
collapse.  This is the positive expressivity theorem behind an acquisition
curve. -/
theorem factorsAt_mono
    {State : Type uState} {Observation : Nat → Type uObservation}
    {Prediction : Type uPrediction}
    (schedule : NestedObservationSchedule State Observation)
    {early late : Nat} (ordered : early ≤ late) :
    {predictor : State → Prediction | schedule.FactorsAt early predictor} ⊆
      {predictor : State → Prediction | schedule.FactorsAt late predictor} :=
  schedule.refinement ordered |>.factorsThrough_mono

/-- The best attainable risk over the declared information class cannot rise
when the forecast origin is delayed and the observation nesting is genuine. -/
theorem optimal_risk_antitone
    {State : Type uState} {Observation : Nat → Type uObservation}
    {Prediction : Type uPrediction}
    (schedule : NestedObservationSchedule State Observation)
    {early late : Nat} (ordered : early ≤ late)
    (risk : (State → Prediction) → ℝ)
    (earlyOptimal : OptimalRiskWitness risk
      {predictor | schedule.FactorsAt early predictor})
    (lateOptimal : OptimalRiskWitness risk
      {predictor | schedule.FactorsAt late predictor}) :
    lateOptimal.value ≤ earlyOptimal.value := by
  exact optimal_risk_antitone_under_model_refinement
    risk _ _ (schedule.factorsAt_mono ordered) earlyOptimal lateOptimal

/-- A collision surviving to a later observation also survives every earlier
origin.  This turns a measured late fiber into an auditable impossibility
boundary for all earlier decision times. -/
theorem early_collision_of_late_collision
    {State : Type uState} {Observation : Nat → Type uObservation}
    (schedule : NestedObservationSchedule State Observation)
    {early late : Nat} (ordered : early ≤ late)
    {first second : State}
    (lateCollision : schedule.observe late first = schedule.observe late second) :
    schedule.observe early first = schedule.observe early second :=
  (schedule.refinement ordered).coarse_collision_of_fine_collision lateCollision

/-- No deterministic point forecast at an earlier origin can be exact in two
worlds whose outcome differs and whose collision survives to a later origin. -/
theorem late_unsplit_outcomes_block_early_exact_point_forecast
    {State : Type uState} {Observation : Nat → Type uObservation}
    {Outcome : Type uPrediction}
    (schedule : NestedObservationSchedule State Observation)
    (target : State → Outcome)
    {early late : Nat} (ordered : early ≤ late)
    (forecast : Observation early → Outcome)
    (first second : State)
    (lateCollision : schedule.observe late first = schedule.observe late second)
    (differentTargets : target first ≠ target second) :
    ¬ (forecast (schedule.observe early first) = target first ∧
      forecast (schedule.observe early second) = target second) :=
  aliased_information_cannot_predict_distinct_targets_exactly
    (schedule.observe early) target forecast first second
    (schedule.early_collision_of_late_collision ordered lateCollision)
    differentTargets

/-- The latency-aware decision objective: risk plus the declared price of
waiting.  The price may encode physical delay, governance opportunity cost or
the cost of acquiring an external schedule. -/
def delayAdjustedRisk (risk delayCost origin : ℝ) : ℝ :=
  risk + delayCost * origin

/-- Exact operational criterion for waiting: a later forecast origin is
decision-preferred precisely when its risk reduction pays the additional delay
cost.  No claim that waiting helps is possible without this premise. -/
theorem delayed_origin_is_decision_preferred
    (earlyRisk lateRisk delayCost earlyOrigin lateOrigin : ℝ)
    (paysForDelay :
      lateRisk + delayCost * (lateOrigin - earlyOrigin) ≤ earlyRisk) :
    delayAdjustedRisk lateRisk delayCost lateOrigin ≤
      delayAdjustedRisk earlyRisk delayCost earlyOrigin := by
  dsimp [delayAdjustedRisk]
  linarith

/-- Complementary no-go: risk monotonicity alone does not license delaying an
action, because an arbitrarily high delay cost can reverse the operational
ordering even when the later predictor has lower risk. -/
theorem lower_risk_alone_does_not_imply_delayed_decision_preferred :
    ∃ earlyRisk lateRisk delayCost earlyOrigin lateOrigin : ℝ,
      lateRisk < earlyRisk ∧
      ¬ (delayAdjustedRisk lateRisk delayCost lateOrigin ≤
        delayAdjustedRisk earlyRisk delayCost earlyOrigin) := by
  refine ⟨1, 0, 2, 0, 1, by norm_num, ?_⟩
  norm_num [delayAdjustedRisk]

end NestedObservationSchedule

end OCKIndividuationMSpaceComposition
