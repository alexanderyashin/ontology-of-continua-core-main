import OCKIndividuationMSpaceComposition.TomographicResolutionMargin
import OCKIndividuationMSpaceComposition.TomographicCalibrationDrift
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

universe uWorld uView

/-!
# Observation distortion and resolution margins

This module supplies the missing quantitative bridge from a calibrated
reference observable to a current distorted observable.  A pointwise bound is
charged twice for a pairwise contrast; therefore a reference separation margin
survives only when the complete two-sided distortion budget is below it.
No correction algorithm or physical distortion model is inferred.
-/

section DistortionBoundary

variable {World : Type uWorld} {View : Type uView}

/-- A current observation stays within a declared pointwise distortion budget
of a source-bound reference observation. -/
def TomographicObservationDistortionBound
    (reference current : View → World → ℝ) (bound : ℝ) : Prop :=
  0 ≤ bound ∧ ∀ view world,
    |current view world - reference view world| ≤ bound

/-! Lift the existing per-observable calibration contract to the dependent
family-of-views contract used by resolution and fusion. -/
theorem tomographicCalibrationDriftBound_as_observationDistortionBound
    (reference current : View → World → ℝ)
    (bound : ℝ)
    (bound_nonnegative : 0 ≤ bound)
    (drift : ∀ view,
      TomographicCalibrationDriftBound (reference view) (current view) bound) :
    TomographicObservationDistortionBound reference current bound := by
  constructor
  · exact bound_nonnegative
  · intro view world
    exact (drift view).2 world

/-! Calibration and acquisition distortion are separate budgets at the source
boundary, but downstream resolution checks need their composed total. -/
theorem tomographicObservationDistortionBound_compose
    (reference calibrated current : View → World → ℝ)
    (calibrationBound distortionBound : ℝ)
    (calibration_nonnegative : 0 ≤ calibrationBound)
    (calibration : ∀ view world,
      |calibrated view world - reference view world| ≤ calibrationBound)
    (distortion : TomographicObservationDistortionBound calibrated current
      distortionBound) :
    TomographicObservationDistortionBound reference current
      (calibrationBound + distortionBound) := by
  constructor
  · linarith [distortion.1]
  · intro view world
    calc
      |current view world - reference view world| =
          |(current view world - calibrated view world) +
            (calibrated view world - reference view world)| := by ring
      _ ≤ |current view world - calibrated view world| +
          |calibrated view world - reference view world| := abs_add_le _ _
      _ ≤ distortionBound + calibrationBound := by
        exact add_le_add (distortion.2 view world) (calibration view world)
      _ = calibrationBound + distortionBound := by ring

/-- The reference pairwise contrast cannot exceed the current contrast plus
the two endpoint distortion budgets. -/
theorem tomographicDistortedPair_reference_contrast_bound
    (reference current : View → World → ℝ)
    (bound : ℝ)
    (distortion : TomographicObservationDistortionBound reference current bound)
    (view : View) (left right : World) :
    |reference view left - reference view right| ≤
      |current view left - current view right| + 2 * bound := by
  have difference_bound :
      |(reference view left - reference view right) -
        (current view left - current view right)| ≤ 2 * bound := by
    have rewritten :
        (reference view left - reference view right) -
            (current view left - current view right) =
          (reference view left - current view left) -
            (reference view right - current view right) := by
      ring
    rw [rewritten]
    calc
      |(reference view left - current view left) -
          (reference view right - current view right)| ≤
          |reference view left - current view left| +
            |reference view right - current view right| :=
        by
          simpa [abs_sub_comm] using
            (abs_sub_le (reference view left - current view left) (0 : ℝ)
              (reference view right - current view right))
      _ ≤ bound + bound := by
        have left_bound :
            |reference view left - current view left| ≤ bound := by
          rw [abs_sub_comm]
          exact distortion.2 view left
        have right_bound :
            |reference view right - current view right| ≤ bound := by
          rw [abs_sub_comm]
          exact distortion.2 view right
        exact add_le_add left_bound right_bound
      _ = 2 * bound := by ring
  have reference_decomposition :
      reference view left - reference view right =
        (current view left - current view right) +
          ((reference view left - reference view right) -
            (current view left - current view right)) := by
    ring
  rw [reference_decomposition]
  calc
    |(current view left - current view right) +
        ((reference view left - reference view right) -
          (current view left - current view right))| ≤
        |current view left - current view right| +
          |(reference view left - reference view right) -
            (current view left - current view right)| :=
      abs_add_le _ _
    _ ≤ |current view left - current view right| + 2 * bound :=
      by
        simpa using
          (add_le_add_left difference_bound
            |current view left - current view right|)

/-- A reference resolution margin degrades by at most twice the pointwise
distortion budget. -/
theorem tomographicDistortedPair_current_margin_lower_bound
    (reference current : View → World → ℝ)
    (bound margin : ℝ)
    (distortion : TomographicObservationDistortionBound reference current bound)
    (view : View) (left right : World)
    (reference_margin : margin ≤
      |reference view left - reference view right|) :
    margin - 2 * bound ≤
      |current view left - current view right| := by
  have contrast_bound := tomographicDistortedPair_reference_contrast_bound
    reference current bound distortion view left right
  linarith

/-- Positive reference separation remains observable after distortion when
the two-sided budget is strictly below the registered margin. -/
theorem tomographicDistortion_preserves_positive_margin
    (reference current : View → World → ℝ)
    (bound margin : ℝ)
    (distortion : TomographicObservationDistortionBound reference current bound)
    (view : View) (left right : World)
    (margin_positive : 0 < margin)
    (reference_margin : margin ≤
      |reference view left - reference view right|)
    (budget_below_margin : 2 * bound < margin) :
    current view left ≠ current view right := by
  have lower := tomographicDistortedPair_current_margin_lower_bound
    reference current bound margin distortion view left right reference_margin
  have positive_current :
      0 < |current view left - current view right| := by
    linarith
  exact sub_ne_zero.mp (by
    exact (abs_pos.mp positive_current))

/-! The generic margin theorem above is deliberately reusable.  This adapter
    binds it to the existing source-bound pair-resolution certificate so a
    registered view witness is not silently replaced by an untyped margin. -/
theorem tomographicDistortion_preserves_pair_resolution
    (reference current : View → World → ℝ)
    (bound : ℝ)
    (distortion : TomographicObservationDistortionBound reference current bound)
    (left right : World)
    (certificate : TomographicPairResolutionCertificate reference left right)
    (budget_below_margin : 2 * bound < certificate.margin) :
    current certificate.view left ≠ current certificate.view right := by
  exact tomographicDistortion_preserves_positive_margin
    reference current bound certificate.margin distortion certificate.view
    left right certificate.margin_positive certificate.lower_bound
    budget_below_margin

/-- Zero distortion is exact pointwise reuse of the reference observable. -/
theorem tomographicZeroDistortion_reference_eq_current
    (reference current : View → World → ℝ)
    (distortion : TomographicObservationDistortionBound reference current 0) :
    ∀ view world, current view world = reference view world := by
  intro view world
  have bound : |current view world - reference view world| ≤ 0 :=
    distortion.2 view world
  exact sub_eq_zero.mp (abs_eq_zero.mp
    (le_antisymm bound (abs_nonneg _)))

end DistortionBoundary

end OCKIndividuationMSpaceComposition
