import OCMinimalObligationSpine.MinimalTransition
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uLiftCarrier uLiftCandidate uRepairCandidate

/-!
This module joins the already proved pressure, M-space and selection surfaces
and adds the smallest quantitative flow/threshold mechanics needed to state
testable transition-time predictions.  It deliberately does not identify a
representational threshold with a thermodynamic phase transition.
-/

/-- A selected lift together with the strict resolution fact that justified it. -/
structure SelectedPressureResolution
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (rank : TransitionRank liftSearch) where
  selection : NatRankedMSpaceArgmin liftSearch d rank
  oldFrameFails : Not (Expresses K d)
  selectedLiftResolves :
    LiftResolves (liftSearch.lift selection.minimizer.1) d

/--
Positive bridge: scoped irreducible pressure plus an available resolving
M-fiber yields a globally rank-minimal admissible lift which strictly resolves
the demanded distinction.  The theorem is conditional on the declared search
classes and does not manufacture a physical dimension.
-/
theorem pressure_selects_minimal_resolving_lift
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (rank : TransitionRank liftSearch)
    (available : AvailableLiftWithin liftSearch d) :
    Nonempty (SelectedPressureResolution pressure liftSearch rank) := by
  obtain ⟨selection⟩ := natRanked_mSpace_argmin_exists liftSearch d rank available
  exact ⟨{
    selection := selection
    oldFrameFails := pressure.2.1
    selectedLiftResolves := selection.minimizer.2.2
  }⟩

/-- A constant-net-flow model for a declared observable and time unit. -/
structure ConstantNetFlow where
  initial : ℚ
  netRate : ℚ
  threshold : ℚ

/-- Observable level after elapsed time `t`. -/
def ConstantNetFlow.levelAt (model : ConstantNetFlow) (t : ℚ) : ℚ :=
  model.initial + t * model.netRate

/-- The exact continuous crossing time when the declared net rate is nonzero. -/
def ConstantNetFlow.crossingTime (model : ConstantNetFlow) : ℚ :=
  (model.threshold - model.initial) / model.netRate

/-- Constant flow satisfies the affine update law exactly. -/
theorem ConstantNetFlow.levelAt_add
    (model : ConstantNetFlow) (t dt : ℚ) :
    model.levelAt (t + dt) = model.levelAt t + dt * model.netRate := by
  simp [ConstantNetFlow.levelAt]
  ring

/-- Positive rate gives an exact threshold value at the predicted crossing time. -/
theorem ConstantNetFlow.levelAt_crossingTime
    (model : ConstantNetFlow)
    (positiveRate : 0 < model.netRate) :
    model.levelAt model.crossingTime = model.threshold := by
  have nonzeroRate : model.netRate ≠ 0 := ne_of_gt positiveRate
  simp only [ConstantNetFlow.levelAt, ConstantNetFlow.crossingTime, div_eq_mul_inv]
  calc
    model.initial + (model.threshold - model.initial) * model.netRate⁻¹ * model.netRate =
        model.initial + (model.threshold - model.initial) * (model.netRate⁻¹ * model.netRate) := by ring
    _ = model.initial + (model.threshold - model.initial) := by
      rw [inv_mul_cancel₀ nonzeroRate]
      ring
    _ = model.threshold := by ring

/-- Before the predicted crossing time a positive-flow observable is sub-threshold. -/
theorem ConstantNetFlow.before_crossing_is_below
    (model : ConstantNetFlow)
    (positiveRate : 0 < model.netRate)
    {t : ℚ}
    (before : t < model.crossingTime) :
    model.levelAt t < model.threshold := by
  rw [← model.levelAt_crossingTime positiveRate]
  simp only [ConstantNetFlow.levelAt]
  simpa [add_comm] using
    (add_lt_add_left (mul_lt_mul_of_pos_right before positiveRate) model.initial)

/-- After the predicted crossing time a positive-flow observable is above threshold. -/
theorem ConstantNetFlow.after_crossing_is_above
    (model : ConstantNetFlow)
    (positiveRate : 0 < model.netRate)
    {t : ℚ}
    (after : model.crossingTime < t) :
    model.threshold < model.levelAt t := by
  rw [← model.levelAt_crossingTime positiveRate]
  simp only [ConstantNetFlow.levelAt]
  simpa [add_comm] using
    (add_lt_add_left (mul_lt_mul_of_pos_right after positiveRate) model.initial)

/--
No-go boundary: from a sub-threshold initial state, a nonpositive net flow can
never reach the threshold at nonnegative time.
-/
theorem ConstantNetFlow.nonpositive_rate_never_crosses
    (model : ConstantNetFlow)
    (initialBelow : model.initial < model.threshold)
    (nonpositiveRate : model.netRate ≤ 0)
    {t : ℚ}
    (nonnegativeTime : 0 ≤ t) :
    model.levelAt t < model.threshold := by
  simp only [ConstantNetFlow.levelAt]
  have productNonpositive : t * model.netRate ≤ 0 :=
    mul_nonpos_of_nonneg_of_nonpos nonnegativeTime nonpositiveRate
  linarith

/-- Exact sensitivity of crossing time to a threshold perturbation. -/
theorem ConstantNetFlow.crossingTime_threshold_sensitivity
    (model : ConstantNetFlow)
    (newThreshold : ℚ)
    (_nonzeroRate : model.netRate ≠ 0) :
    ({ model with threshold := newThreshold }).crossingTime - model.crossingTime =
      (newThreshold - model.threshold) / model.netRate := by
  simp only [ConstantNetFlow.crossingTime, div_eq_mul_inv]
  ring

/-- Two regimes induced by one explicitly declared observable threshold. -/
inductive ThresholdRegime where
  | below
  | crossed
  deriving DecidableEq, Repr

def ConstantNetFlow.regimeAt (model : ConstantNetFlow) (t : ℚ) : ThresholdRegime :=
  if model.threshold ≤ model.levelAt t then .crossed else .below

theorem ConstantNetFlow.regimeAt_eq_crossed_iff
    (model : ConstantNetFlow) (t : ℚ) :
    model.regimeAt t = .crossed ↔ model.threshold ≤ model.levelAt t := by
  simp [ConstantNetFlow.regimeAt]

end OCKIndividuationMSpaceComposition
