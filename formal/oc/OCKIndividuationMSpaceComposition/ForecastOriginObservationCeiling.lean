import OCKIndividuationMSpaceComposition.PredictiveAdapterStack

namespace OCKIndividuationMSpaceComposition

/-!
Minimum OC adapter from a forecast-origin observation contract to the mature
observation-collision ceiling already proved in `PredictiveAdapterStack`.
-/

structure ForecastOriginExperiment (World Observation : Type*) where
  observeAtOrigin : World → Observation
  outcomeAfterOrigin : World → ℝ

structure ForecastOriginOutcomeCollision
    {World Observation : Type*}
    (experiment : ForecastOriginExperiment World Observation) where
  first : World
  second : World
  sameOriginObservation :
    experiment.observeAtOrigin first = experiment.observeAtOrigin second
  differentOutcome :
    experiment.outcomeAfterOrigin first ≠ experiment.outcomeAfterOrigin second

theorem forecastOrigin_predictor_equal_on_collision
    {World Observation : Type*}
    {experiment : ForecastOriginExperiment World Observation}
    (collision : ForecastOriginOutcomeCollision experiment)
    (predictor : Observation → ℝ) :
    predictor (experiment.observeAtOrigin collision.first) =
      predictor (experiment.observeAtOrigin collision.second) := by
  rw [collision.sameOriginObservation]

theorem forecastOrigin_collision_MSE_lower_bound
    {World Observation : Type*}
    {experiment : ForecastOriginExperiment World Observation}
    (collision : ForecastOriginOutcomeCollision experiment)
    (predictor : Observation → ℝ) :
    (experiment.outcomeAfterOrigin collision.first
          - experiment.outcomeAfterOrigin collision.second) ^ 2 / 4
      ≤ CollisionPairMSE
        (experiment.outcomeAfterOrigin collision.first)
        (experiment.outcomeAfterOrigin collision.second)
        (predictor (experiment.observeAtOrigin collision.first)) :=
  collisionPairMSE_lower_bound _ _ _

theorem forecastOrigin_midpoint_attains_collision_bound
    {World Observation : Type*}
    {experiment : ForecastOriginExperiment World Observation}
    (collision : ForecastOriginOutcomeCollision experiment) :
    CollisionPairMSE
        (experiment.outcomeAfterOrigin collision.first)
        (experiment.outcomeAfterOrigin collision.second)
        ((experiment.outcomeAfterOrigin collision.first
          + experiment.outcomeAfterOrigin collision.second) / 2)
      = (experiment.outcomeAfterOrigin collision.first
          - experiment.outcomeAfterOrigin collision.second) ^ 2 / 4 :=
  collisionPairMSE_midpoint_attains_bound _ _

end OCKIndividuationMSpaceComposition
