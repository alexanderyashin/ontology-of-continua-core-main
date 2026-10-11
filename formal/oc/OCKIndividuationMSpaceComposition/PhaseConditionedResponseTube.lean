import OCKIndividuationMSpaceComposition.SetResidualHullComposition

namespace OCKIndividuationMSpaceComposition

/-!
# Phase-conditioned within-successor response tubes

The previous scalar composition separates a successor-mechanism hull from a
residual radius.  A transition trajectory additionally varies by an
origin-observable phase and forecast horizon, and its lower and upper errors
need not be symmetric.  This module types that extra structure without assuming
that phase is identifiable.

The interval arithmetic is reused mathematics.  The OC-specific contribution
is the explicit dependency boundary between origin information, path phase,
successor mechanism, horizon and residual law.
-/

namespace ScalarForecastHull

/-- Inflate a mechanism hull by separate lower and upper residual radii. -/
def inflateAsymmetric
    (hull : ScalarForecastHull) (lowerRadius upperRadius : ℝ) :
    ScalarForecastHull where
  lower := hull.lower - lowerRadius
  upper := hull.upper + upperRadius

/-- Pointwise positive bridge for an asymmetric residual law. -/
theorem contained_center_and_asymmetric_residual_bounds_yield_target
    (mechanism : ScalarForecastHull)
    (center target lowerRadius upperRadius : ℝ)
    (centerContained : Contains mechanism center)
    (lowerBound : -lowerRadius ≤ target - center)
    (upperBound : target - center ≤ upperRadius) :
    Contains (inflateAsymmetric mechanism lowerRadius upperRadius) target := by
  constructor
  · dsimp [Contains, inflateAsymmetric] at centerContained ⊢
    linarith [centerContained.1, lowerBound]
  · dsimp [Contains, inflateAsymmetric] at centerContained ⊢
    linarith [centerContained.2, upperBound]

/-- Exact proper-score width charge for asymmetric composition. -/
theorem inflateAsymmetric_width
    (mechanism : ScalarForecastHull) (lowerRadius upperRadius : ℝ) :
    (inflateAsymmetric mechanism lowerRadius upperRadius).upper -
        (inflateAsymmetric mechanism lowerRadius upperRadius).lower =
      (mechanism.upper - mechanism.lower) + lowerRadius + upperRadius := by
  simp [inflateAsymmetric]
  ring

/-- Worst-case minimality: any scalar hull covering both asymmetric extreme
worlds contains the explicit asymmetric inflation. -/
theorem inflateAsymmetric_is_minimal_for_extreme_worlds
    (mechanism candidate : ScalarForecastHull)
    (lowerRadius upperRadius : ℝ)
    (coversLower : Contains candidate (mechanism.lower - lowerRadius))
    (coversUpper : Contains candidate (mechanism.upper + upperRadius)) :
    Refines (inflateAsymmetric mechanism lowerRadius upperRadius) candidate := by
  exact ⟨coversLower.1, coversUpper.2⟩

end ScalarForecastHull

/-- A response envelope indexed separately by path phase and forecast horizon. -/
structure PhaseConditionedResponseTube (Phase Horizon : Type*) where
  hullAt : Phase → Horizon → ScalarForecastHull

namespace PhaseConditionedResponseTube

/-- A realized trajectory is covered pointwise at the selected phase. -/
def CoversTrajectory
    {Phase Horizon : Type*}
    (tube : PhaseConditionedResponseTube Phase Horizon)
    (phase : Phase) (trajectory : Horizon → ℝ) : Prop :=
  ∀ horizon, ScalarForecastHull.Contains (tube.hullAt phase horizon) (trajectory horizon)

/-- Compose a successor-mechanism tube with phase/horizon-specific asymmetric
residual radii. -/
def compose
    {Phase Horizon : Type*}
    (mechanism : PhaseConditionedResponseTube Phase Horizon)
    (lowerRadius upperRadius : Phase → Horizon → ℝ) :
    PhaseConditionedResponseTube Phase Horizon where
  hullAt phase horizon := ScalarForecastHull.inflateAsymmetric
    (mechanism.hullAt phase horizon)
    (lowerRadius phase horizon) (upperRadius phase horizon)

/-- Positive trajectory theorem: pointwise successor-centre containment and
phase/horizon residual bounds construct coverage of the complete requested
trajectory. -/
theorem compose_covers_trajectory
    {Phase Horizon : Type*}
    (mechanism : PhaseConditionedResponseTube Phase Horizon)
    (lowerRadius upperRadius : Phase → Horizon → ℝ)
    (phase : Phase)
    (center target : Horizon → ℝ)
    (centerContained : ∀ horizon,
      ScalarForecastHull.Contains (mechanism.hullAt phase horizon) (center horizon))
    (lowerBound : ∀ horizon,
      -lowerRadius phase horizon ≤ target horizon - center horizon)
    (upperBound : ∀ horizon,
      target horizon - center horizon ≤ upperRadius phase horizon) :
    CoversTrajectory (compose mechanism lowerRadius upperRadius) phase target := by
  intro horizon
  exact ScalarForecastHull.contained_center_and_asymmetric_residual_bounds_yield_target
    (mechanism.hullAt phase horizon) (center horizon) (target horizon)
    (lowerRadius phase horizon) (upperRadius phase horizon)
    (centerContained horizon) (lowerBound horizon) (upperBound horizon)

/-- An explicitly refined phase-specific hull never costs more width than its
unconditioned parent at the same horizon. -/
theorem phase_refinement_cannot_increase_width
    {Phase Horizon : Type*}
    (conditioned unconditioned : PhaseConditionedResponseTube Phase Horizon)
    (phase : Phase) (horizon : Horizon)
    (refines : ScalarForecastHull.Refines
      (conditioned.hullAt phase horizon) (unconditioned.hullAt phase horizon)) :
    (conditioned.hullAt phase horizon).upper -
        (conditioned.hullAt phase horizon).lower ≤
      (unconditioned.hullAt phase horizon).upper -
        (unconditioned.hullAt phase horizon).lower :=
  ScalarForecastHull.width_le_of_refines _ _ refines

end PhaseConditionedResponseTube

/-- Quantitative phase-aliasing lower bound.  If two worlds are observationally
aliased at origin, any single hull which is sound for both must pay at least the
absolute gap between their trajectory values at that horizon. -/
theorem aliased_phase_sound_hull_width_at_least_target_gap
    {World Information : Type*}
    (observeAtOrigin : World → Information)
    (targetAtHorizon : World → ℝ)
    (forecast : Information → ScalarForecastHull)
    (first second : World)
    (sameInformation : observeAtOrigin first = observeAtOrigin second)
    (coversFirst : ScalarForecastHull.Contains
      (forecast (observeAtOrigin first)) (targetAtHorizon first))
    (coversSecond : ScalarForecastHull.Contains
      (forecast (observeAtOrigin second)) (targetAtHorizon second)) :
    |targetAtHorizon first - targetAtHorizon second| ≤
      (forecast (observeAtOrigin first)).upper -
        (forecast (observeAtOrigin first)).lower := by
  rw [← sameInformation] at coversSecond
  rw [abs_le]
  constructor <;> linarith [coversFirst.1, coversFirst.2, coversSecond.1, coversSecond.2]

/-- No deterministic point forecast can be exact in two phase worlds which are
aliased at origin but have different horizon targets. -/
theorem aliased_phase_point_forecast_cannot_be_exact
    {World Information Outcome : Type*}
    (observeAtOrigin : World → Information)
    (targetAtHorizon : World → Outcome)
    (forecast : Information → Outcome)
    (first second : World)
    (sameInformation : observeAtOrigin first = observeAtOrigin second)
    (differentTargets : targetAtHorizon first ≠ targetAtHorizon second) :
    ¬ (forecast (observeAtOrigin first) = targetAtHorizon first ∧
      forecast (observeAtOrigin second) = targetAtHorizon second) :=
  aliased_information_cannot_predict_distinct_targets_exactly
    observeAtOrigin targetAtHorizon forecast first second sameInformation differentTargets

end OCKIndividuationMSpaceComposition
