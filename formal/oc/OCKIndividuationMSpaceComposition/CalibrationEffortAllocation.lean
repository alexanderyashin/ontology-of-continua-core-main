import OCKIndividuationMSpaceComposition.RobustTransportHazardPrediction
import OCKIndividuationMSpaceComposition.IntegerSampleAllocationRounding

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Optimal allocation of calibration effort

Suppose coordinate `i` has a calibration-width law `a_i / sqrt(n_i)`.
The robust transport-to-CDF theorem multiplies that width by horizon,
response sensitivity and the observed directed drop.  This module turns those
quantities into the coefficient of the already verified inverse-square-root
allocation problem.
-/

def calibrationPredictionWidthCoefficient
    (horizon : ℕ) (sensitivity directedDropValue radiusCoefficient : ℝ) : ℝ :=
  (horizon : ℝ) * sensitivity * directedDropValue * radiusCoefficient

theorem calibrationPredictionWidthCoefficient_nonnegative
    (horizon : ℕ) {sensitivity directedDropValue radiusCoefficient : ℝ}
    (sensitivityNonnegative : 0 ≤ sensitivity)
    (dropNonnegative : 0 ≤ directedDropValue)
    (radiusNonnegative : 0 ≤ radiusCoefficient) :
    0 ≤ calibrationPredictionWidthCoefficient horizon sensitivity
      directedDropValue radiusCoefficient := by
  unfold calibrationPredictionWidthCoefficient
  positivity

theorem calibrationPredictionWidthCoefficient_positive
    {horizon : ℕ} {sensitivity directedDropValue radiusCoefficient : ℝ}
    (horizonPositive : 0 < horizon)
    (sensitivityPositive : 0 < sensitivity)
    (dropPositive : 0 < directedDropValue)
    (radiusPositive : 0 < radiusCoefficient) :
    0 < calibrationPredictionWidthCoefficient horizon sensitivity
      directedDropValue radiusCoefficient := by
  unfold calibrationPredictionWidthCoefficient
  positivity

noncomputable def totalCalibrationPredictionWidth
    {Index : Type} [Fintype Index]
    (horizon : ℕ) (sensitivity : ℝ)
    (directedDropValue radiusCoefficient observations : Index → ℝ) : ℝ :=
  ∑ index, inverseSqrtAllocationCost
    (calibrationPredictionWidthCoefficient horizon sensitivity
      (directedDropValue index) (radiusCoefficient index))
    (observations index)

/-- A common-marginal certificate proves global optimality of calibration
effort for the finite-horizon CDF-width upper bound. -/
theorem common_marginal_certifies_optimal_calibration_effort
    {Index : Type} [Fintype Index] [Nonempty Index]
    (horizon : ℕ) (sensitivity : ℝ)
    (directedDropValue radiusCoefficient candidate competitor : Index → ℝ)
    (rate : ℝ)
    (coefficientNonnegative : ∀ index,
      0 ≤ calibrationPredictionWidthCoefficient horizon sensitivity
        (directedDropValue index) (radiusCoefficient index))
    (candidatePositive : ∀ index, 0 < candidate index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (commonMarginal : ∀ index,
      calibrationPredictionWidthCoefficient horizon sensitivity
          (directedDropValue index) (radiusCoefficient index) /
        (2 * candidate index * Real.sqrt (candidate index)) = rate)
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index) :
    totalCalibrationPredictionWidth horizon sensitivity directedDropValue
        radiusCoefficient candidate ≤
      totalCalibrationPredictionWidth horizon sensitivity directedDropValue
        radiusCoefficient competitor := by
  exact common_inverseSqrt_marginal_certifies_global_allocation_optimum
    (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
      (directedDropValue index) (radiusCoefficient index))
    candidate competitor rate coefficientNonnegative candidatePositive
    competitorPositive commonMarginal competitorBudget

/-- Root-free cube balance is a finite exact certificate for the same
calibration-effort optimum. -/
theorem cube_balance_certifies_optimal_calibration_effort
    {Index : Type} [Fintype Index] [Nonempty Index]
    (horizon : ℕ) (sensitivity : ℝ)
    (directedDropValue radiusCoefficient candidate competitor : Index → ℝ)
    (reference : Index)
    (coefficientPositive : ∀ index,
      0 < calibrationPredictionWidthCoefficient horizon sensitivity
        (directedDropValue index) (radiusCoefficient index))
    (candidatePositive : ∀ index, 0 < candidate index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (cubeBalance : ∀ index,
      calibrationPredictionWidthCoefficient horizon sensitivity
          (directedDropValue index) (radiusCoefficient index) ^ 2 *
          candidate reference ^ 3 =
        calibrationPredictionWidthCoefficient horizon sensitivity
          (directedDropValue reference) (radiusCoefficient reference) ^ 2 *
          candidate index ^ 3)
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index) :
    totalCalibrationPredictionWidth horizon sensitivity directedDropValue
        radiusCoefficient candidate ≤
      totalCalibrationPredictionWidth horizon sensitivity directedDropValue
        radiusCoefficient competitor := by
  exact cube_balance_certificate_global_allocation_optimum
    (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
      (directedDropValue index) (radiusCoefficient index))
    candidate competitor reference coefficientPositive candidatePositive
    competitorPositive cubeBalance competitorBudget

/-- A common positive scale on all width coefficients does not alter the
root-free optimal allocation ratios.  Hence a common horizon and response
sensitivity scale total uncertainty but not relative sample shares. -/
theorem common_positive_scale_preserves_allocation_cube_balance
    {Index : Type} [Fintype Index]
    (scale : ℝ) (coefficient candidate : Index → ℝ)
    (reference index : Index)
    (scalePositive : 0 < scale) :
    (scale * coefficient index) ^ 2 * candidate reference ^ 3 =
        (scale * coefficient reference) ^ 2 * candidate index ^ 3 ↔
      coefficient index ^ 2 * candidate reference ^ 3 =
        coefficient reference ^ 2 * candidate index ^ 3 := by
  have scaleSquarePositive : 0 < scale ^ 2 := sq_pos_of_pos scalePositive
  constructor <;> intro equality
  · nlinarith
  · nlinarith

/-- A coordinate with zero directed drop contributes zero calibration-driven
prediction width at every positive sample count.  More samples cannot improve
this particular bound term. -/
theorem zero_drop_coordinate_has_zero_calibration_prediction_width
    (horizon : ℕ) (sensitivity radiusCoefficient observations : ℝ) :
    inverseSqrtAllocationCost
      (calibrationPredictionWidthCoefficient horizon sensitivity 0
        radiusCoefficient) observations = 0 := by
  simp [calibrationPredictionWidthCoefficient, inverseSqrtAllocationCost]

def oneEightCalibrationDropProfile : Fin 2 → ℝ := ![1, 8]

/-- Numerical canary: at unit horizon, sensitivity and radius coefficient,
directed drops `(1,8)` produce the unique five-unit continuous allocation
`(1,4)`. -/
theorem one_eight_calibration_drops_five_budget_unique_optimum
    (competitor : Fin 2 → ℝ)
    (competitorPositive : ∀ index, 0 < competitor index)
    (competitorBudget : (∑ index, competitor index) ≤ 5)
    (different : competitor ≠ oneFourSampleAllocation) :
    totalCalibrationPredictionWidth 1 1 oneEightCalibrationDropProfile
        (fun _ => 1) oneFourSampleAllocation <
      totalCalibrationPredictionWidth 1 1 oneEightCalibrationDropProfile
        (fun _ => 1) competitor := by
  simpa [totalCalibrationPredictionWidth,
    calibrationPredictionWidthCoefficient, oneEightCalibrationDropProfile,
    oneEightCoefficientProfile] using
    one_eight_coefficients_five_budget_unique_optimum competitor
      competitorPositive competitorBudget different

end OCKIndividuationMSpaceComposition
