import OCKIndividuationMSpaceComposition.StochasticQuotientMinimax

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe uWorld uObservation uOutcome

/-!
# Exact information boundary for observation-only stochastic forecasts

This module turns the sharp two-law TV radius into an observation contract.
It quantifies over every predictor that factors through the same observation;
the lower bound is therefore algorithm-independent inside that information
class.  It does not claim a lower bound for a predictor given a richer optic.
-/

/-- The target law is constant on every fibre of the declared observation. -/
def ObservationLawSufficient
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome) : Prop :=
  ∀ ⦃left right : World⦄, observe left = observe right → law left = law right

/-- An exact forecast is constrained to use only the declared observation. -/
def ExactObservationLawForecast
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome) : Prop :=
  ∃ forecast : Observation → FiniteProbabilityMass Outcome,
    ∀ world, forecast (observe world) = law world

/-- Positive theorem: fibre constancy is sufficient to construct a globally
exact observation-only forecast. -/
theorem observationLawSufficient_has_exact_forecast
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Nonempty World]
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome)
    (sufficient : ObservationLawSufficient observe law) :
    ExactObservationLawForecast observe law := by
  classical
  let defaultWorld : World := Classical.choice inferInstance
  let forecast : Observation → FiniteProbabilityMass Outcome := fun observed =>
    if represented : ∃ world, observe world = observed then
      law (Classical.choose represented)
    else
      law defaultWorld
  refine ⟨forecast, ?_⟩
  intro world
  have represented : ∃ candidate, observe candidate = observe world :=
    ⟨world, rfl⟩
  simp only [forecast, dif_pos represented]
  exact sufficient (Classical.choose_spec represented)

/-- Converse theorem: an exact observation-only forecast forces the law to be
constant on each observation fibre. -/
theorem exact_forecast_implies_observationLawSufficient
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome)
    (exact : ExactObservationLawForecast observe law) :
    ObservationLawSufficient observe law := by
  rcases exact with ⟨forecast, correct⟩
  intro left right collision
  rw [← correct left, ← correct right, collision]

/-- Exact characterization of the information condition for zero-error law
forecasting. -/
theorem exact_observation_forecast_iff_fibre_constant
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Nonempty World]
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome) :
    ExactObservationLawForecast observe law ↔
      ObservationLawSufficient observe law := by
  constructor
  · exact exact_forecast_implies_observationLawSufficient observe law
  · exact observationLawSufficient_has_exact_forecast observe law

/-- Universal quantitative lower bound: if two possible worlds produce the
same observation, every predictor using only that observation has worst-case
TV error at least half the separation of their target laws. -/
theorem observation_collision_max_tv_error_ge_half_separation
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome)
    (forecast : Observation → FiniteProbabilityMass Outcome)
    (left right : World)
    (collision : observe left = observe right) :
    finiteTotalVariation (law left) (law right) / 2 ≤
      max
        (finiteTotalVariation (law left) (forecast (observe left)))
        (finiteTotalVariation (law right) (forecast (observe right))) := by
  let radius := max
    (finiteTotalVariation (law left) (forecast (observe left)))
    (finiteTotalVariation (law right) (forecast (observe right)))
  have leftBound :
      finiteTotalVariation (law left) (forecast (observe left)) ≤ radius :=
    le_max_left _ _
  have rightBound :
      finiteTotalVariation (law right) (forecast (observe left)) ≤ radius := by
    rw [collision]
    exact le_max_right _ _
  exact any_common_tv_radius_ge_half_pairwise
    (law left) (law right) (forecast (observe left)) radius
    leftBound rightBound

/-- No-go form for a declared radius below the collision floor. -/
theorem observation_collision_no_uniform_subhalf_forecast
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome)
    (left right : World)
    (collision : observe left = observe right)
    (epsilon : ℚ)
    (tooSmall : epsilon < finiteTotalVariation (law left) (law right) / 2) :
    ¬ ∃ forecast : Observation → FiniteProbabilityMass Outcome,
        finiteTotalVariation (law left) (forecast (observe left)) ≤ epsilon ∧
        finiteTotalVariation (law right) (forecast (observe right)) ≤ epsilon := by
  rintro ⟨forecast, leftBound, rightBound⟩
  have lower := observation_collision_max_tv_error_ge_half_separation
    observe law forecast left right collision
  have upper :
      max
        (finiteTotalVariation (law left) (forecast (observe left)))
        (finiteTotalVariation (law right) (forecast (observe right))) ≤
        epsilon := by
    exact max_le leftBound rightBound
  exact (not_le_of_gt tooSmall) (lower.trans upper)

/-- The constant midpoint forecast attains the collision lower bound on both
worlds.  Thus the factor `1/2` is sharp, not a proof artifact. -/
theorem constant_midpoint_forecast_attains_collision_radius
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome)
    (left right : World) :
    let forecast : Observation → FiniteProbabilityMass Outcome :=
      fun _ => finiteProbabilityMidpoint (law left) (law right)
    finiteTotalVariation (law left) (forecast (observe left)) =
        finiteTotalVariation (law left) (law right) / 2 ∧
      finiteTotalVariation (law right) (forecast (observe right)) =
        finiteTotalVariation (law left) (law right) / 2 := by
  dsimp
  exact ⟨finiteTotalVariation_left_midpoint (law left) (law right),
    finiteTotalVariation_right_midpoint (law left) (law right)⟩

/-- Exact two-world minimax characterization within one observation class:
the midpoint achieves the lower bound and no observation-only forecast can
improve its worst-case radius. -/
theorem two_world_observation_forecast_minimax_characterization
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observe : World → Observation)
    (law : World → FiniteProbabilityMass Outcome)
    (left right : World)
    (collision : observe left = observe right) :
    (∃ forecast : Observation → FiniteProbabilityMass Outcome,
      finiteTotalVariation (law left) (forecast (observe left)) =
          finiteTotalVariation (law left) (law right) / 2 ∧
        finiteTotalVariation (law right) (forecast (observe right)) =
          finiteTotalVariation (law left) (law right) / 2) ∧
    (∀ forecast : Observation → FiniteProbabilityMass Outcome,
      finiteTotalVariation (law left) (law right) / 2 ≤
        max
          (finiteTotalVariation (law left) (forecast (observe left)))
          (finiteTotalVariation (law right) (forecast (observe right)))) := by
  constructor
  · refine ⟨fun _ => finiteProbabilityMidpoint (law left) (law right), ?_⟩
    exact constant_midpoint_forecast_attains_collision_radius
      observe law left right
  · intro forecast
    exact observation_collision_max_tv_error_ge_half_separation
      observe law forecast left right collision

/-- More samples do not help if every admitted transcript continues to alias
the same two laws.  The theorem quantifies over an arbitrary predictor at
every sample count. -/
theorem persistent_observation_collision_preserves_minimax_floor
    {World : Type uWorld}
    {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (observeAt : ℕ → World → Observation)
    (law : World → FiniteProbabilityMass Outcome)
    (forecastAt : ℕ → Observation → FiniteProbabilityMass Outcome)
    (left right : World)
    (persistentCollision : ∀ observations,
      observeAt observations left = observeAt observations right) :
    ∀ observations,
      finiteTotalVariation (law left) (law right) / 2 ≤
        max
          (finiteTotalVariation (law left)
            (forecastAt observations (observeAt observations left)))
          (finiteTotalVariation (law right)
            (forecastAt observations (observeAt observations right))) := by
  intro observations
  exact observation_collision_max_tv_error_ge_half_separation
    (observeAt observations) law (forecastAt observations) left right
    (persistentCollision observations)

end OCKIndividuationMSpaceComposition
