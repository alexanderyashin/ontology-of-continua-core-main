import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

universe uState

/-!
# Bounded calibration drift

This module formalizes only a pointwise drift budget between a registered
reference observable and its current observable.  It does not infer a drift
law, stationarity, identifiability, or a calibration procedure.  The useful
consequence is that pairwise differences inherit twice the pointwise budget;
therefore an old calibrated contrast cannot be reused without accounting for
the current drift.
-/

/-- A current observable stays within `bound` of a registered reference. -/
def TomographicCalibrationDriftBound
    {State : Type uState}
    (reference current : State → ℝ)
    (bound : ℝ) : Prop :=
  0 ≤ bound ∧ ∀ state, |current state - reference state| ≤ bound

/-- The calibration-induced error in a contrast between two states. -/
def tomographicCalibrationContrastDrift
    {State : Type uState}
    (reference current : State → ℝ)
    (left right : State) : ℝ :=
  (current left - current right) - (reference left - reference right)

/-- Two pointwise drift budgets add when a pairwise contrast is compared. -/
theorem tomographicCalibrationContrastDrift_abs_bound
    {State : Type uState}
    (reference current : State → ℝ)
    (bound : ℝ)
    (drift : TomographicCalibrationDriftBound reference current bound)
    (left right : State) :
    |tomographicCalibrationContrastDrift reference current left right| ≤
      2 * bound := by
  have decomposition :
      tomographicCalibrationContrastDrift reference current left right =
        (current left - reference left) +
          (reference right - current right) := by
    unfold tomographicCalibrationContrastDrift
    ring
  rw [decomposition]
  calc
    |(current left - reference left) + (reference right - current right)| ≤
        |current left - reference left| + |reference right - current right| :=
      abs_add_le _ _
    _ ≤ bound + bound := by
      have right_bound : |reference right - current right| ≤ bound := by
        rw [abs_sub_comm]
        exact drift.2 right
      exact add_le_add (drift.2 left) right_bound
    _ = 2 * bound := by ring

/-- With a zero drift budget, the current observable equals the reference
pointwise, so every registered contrast is unchanged. -/
theorem tomographicCalibrationDrift_zero_bound
    {State : Type uState}
    (reference current : State → ℝ)
    (drift : TomographicCalibrationDriftBound reference current 0) :
    ∀ state, current state = reference state := by
  intro state
  have absolute_zero : |current state - reference state| ≤ 0 := by
    simpa using drift.2 state
  have difference_zero : current state - reference state = 0 :=
    abs_eq_zero.mp (le_antisymm absolute_zero (abs_nonneg _))
  exact sub_eq_zero.mp difference_zero

/-! A correction stage can be chained without pretending that it removed the
    drift exactly.  The new bound is the sum of the two declared pointwise
    budgets, which is the deterministic envelope an adaptive observer can
    carry into its next reconstruction step. -/
theorem tomographicCalibrationDriftBound_compose
    {State : Type uState}
    (reference current corrected : State → ℝ)
    (reference_bound correction_bound : ℝ)
    (reference_drift :
      TomographicCalibrationDriftBound reference current reference_bound)
    (correction_drift :
      TomographicCalibrationDriftBound current corrected correction_bound) :
    TomographicCalibrationDriftBound reference corrected
      (reference_bound + correction_bound) := by
  constructor
  · exact add_nonneg reference_drift.1 correction_drift.1
  · intro state
    have decomposition :
        corrected state - reference state =
          (corrected state - current state) +
            (current state - reference state) := by
      ring
    rw [decomposition]
    calc
      |(corrected state - current state) +
          (current state - reference state)| ≤
          |corrected state - current state| +
            |current state - reference state| := abs_add_le _ _
      _ ≤ correction_bound + reference_bound := by
        exact add_le_add (correction_drift.2 state)
          (reference_drift.2 state)
      _ = reference_bound + correction_bound := by ring

end OCKIndividuationMSpaceComposition