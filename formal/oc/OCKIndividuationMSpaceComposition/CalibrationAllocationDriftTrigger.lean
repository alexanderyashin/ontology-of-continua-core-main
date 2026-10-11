import OCKIndividuationMSpaceComposition.CalibrationEffortAllocation
import OCKIndividuationMSpaceComposition.RobustSampleAllocationSensitivity

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Drift-aware recalibration and reoptimization trigger

The calibration allocation coefficient is a product of directed drop and a
radius-law coefficient.  Both can drift.  This module propagates simultaneous
component radii into an allocation-coefficient radius, then reuses the
verified M3 regret theorem to decide whether a stale allocation remains
certified.
-/

/-- Product perturbation bound used by the calibration coefficient adapter. -/
theorem product_perturbation_le_factor_radii
    (trueFirst estimatedFirst trueSecond estimatedSecond
      firstRadius secondRadius firstMagnitudeBound : ℝ)
    (firstMagnitude : |trueFirst| ≤ firstMagnitudeBound)
    (firstCoverage : |trueFirst - estimatedFirst| ≤ firstRadius)
    (secondCoverage : |trueSecond - estimatedSecond| ≤ secondRadius) :
    |trueFirst * trueSecond - estimatedFirst * estimatedSecond| ≤
      firstMagnitudeBound * secondRadius +
        |estimatedSecond| * firstRadius := by
  have decomposition :
      trueFirst * trueSecond - estimatedFirst * estimatedSecond =
        trueFirst * (trueSecond - estimatedSecond) +
          estimatedSecond * (trueFirst - estimatedFirst) := by ring
  rw [decomposition]
  calc
    |trueFirst * (trueSecond - estimatedSecond) +
        estimatedSecond * (trueFirst - estimatedFirst)| ≤
      |trueFirst * (trueSecond - estimatedSecond)| +
        |estimatedSecond * (trueFirst - estimatedFirst)| := abs_add_le _ _
    _ = |trueFirst| * |trueSecond - estimatedSecond| +
        |estimatedSecond| * |trueFirst - estimatedFirst| := by
      rw [abs_mul, abs_mul]
    _ ≤ firstMagnitudeBound * secondRadius +
        |estimatedSecond| * firstRadius := by
      exact add_le_add
        (mul_le_mul firstMagnitude secondCoverage (abs_nonneg _)
          (le_trans (abs_nonneg _) firstMagnitude))
        (mul_le_mul_of_nonneg_left firstCoverage (abs_nonneg _))

def calibrationPredictionCoefficientRadius
    (horizon : ℕ) (sensitivity dropMagnitudeBound estimatedRadiusCoefficient
      dropRadius radiusCoefficientRadius : ℝ) : ℝ :=
  (horizon : ℝ) * sensitivity *
    (dropMagnitudeBound * radiusCoefficientRadius +
      |estimatedRadiusCoefficient| * dropRadius)

/-- Simultaneous drop/radius-law coverage gives a simultaneous radius for the
derived finite-horizon calibration-allocation coefficient. -/
theorem calibrationPredictionCoefficient_radius_coverage
    (horizon : ℕ)
    {sensitivity trueDrop estimatedDrop trueRadiusCoefficient
      estimatedRadiusCoefficient dropMagnitudeBound dropRadius
      radiusCoefficientRadius : ℝ}
    (sensitivityNonnegative : 0 ≤ sensitivity)
    (dropMagnitude : |trueDrop| ≤ dropMagnitudeBound)
    (dropCoverage : |trueDrop - estimatedDrop| ≤ dropRadius)
    (radiusCoverage :
      |trueRadiusCoefficient - estimatedRadiusCoefficient| ≤
        radiusCoefficientRadius) :
    |calibrationPredictionWidthCoefficient horizon sensitivity trueDrop
        trueRadiusCoefficient -
      calibrationPredictionWidthCoefficient horizon sensitivity estimatedDrop
        estimatedRadiusCoefficient| ≤
      calibrationPredictionCoefficientRadius horizon sensitivity
        dropMagnitudeBound estimatedRadiusCoefficient dropRadius
        radiusCoefficientRadius := by
  have productBound := product_perturbation_le_factor_radii
    trueDrop estimatedDrop trueRadiusCoefficient estimatedRadiusCoefficient
    dropRadius radiusCoefficientRadius dropMagnitudeBound dropMagnitude
    dropCoverage radiusCoverage
  have scaleNonnegative :
      0 ≤ (horizon : ℝ) * sensitivity := mul_nonneg (by positivity)
        sensitivityNonnegative
  unfold calibrationPredictionWidthCoefficient
    calibrationPredictionCoefficientRadius
  have factorization :
      (horizon : ℝ) * sensitivity * trueDrop * trueRadiusCoefficient -
          (horizon : ℝ) * sensitivity * estimatedDrop *
            estimatedRadiusCoefficient =
        ((horizon : ℝ) * sensitivity) *
          (trueDrop * trueRadiusCoefficient -
            estimatedDrop * estimatedRadiusCoefficient) := by ring
  rw [factorization, abs_mul, abs_of_nonneg scaleNonnegative]
  exact mul_le_mul_of_nonneg_left productBound scaleNonnegative

/-- A stale estimated optimum has a computable true-regret certificate from
drop and radius-law confidence radii at both the chosen and oracle plans. -/
theorem estimated_calibration_optimum_true_regret_le_registered_drift_budgets
    {Index : Type} [Fintype Index]
    (horizon : ℕ) (sensitivity : ℝ)
    (trueDrop estimatedDrop trueRadiusCoefficient estimatedRadiusCoefficient
      dropMagnitudeBound dropRadius radiusCoefficientRadius chosen oracle :
      Index → ℝ)
    (sensitivityNonnegative : 0 ≤ sensitivity)
    (chosenPositive : ∀ index, 0 < chosen index)
    (oraclePositive : ∀ index, 0 < oracle index)
    (dropMagnitude : ∀ index,
      |trueDrop index| ≤ dropMagnitudeBound index)
    (dropCoverage : ∀ index,
      |trueDrop index - estimatedDrop index| ≤ dropRadius index)
    (radiusCoverage : ∀ index,
      |trueRadiusCoefficient index - estimatedRadiusCoefficient index| ≤
        radiusCoefficientRadius index)
    (estimatedOptimal :
      aggregateInverseSqrtAllocationCost
          (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
            (estimatedDrop index) (estimatedRadiusCoefficient index)) chosen ≤
        aggregateInverseSqrtAllocationCost
          (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
            (estimatedDrop index) (estimatedRadiusCoefficient index)) oracle) :
    aggregateInverseSqrtAllocationCost
        (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
          (trueDrop index) (trueRadiusCoefficient index)) chosen -
      aggregateInverseSqrtAllocationCost
        (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
          (trueDrop index) (trueRadiusCoefficient index)) oracle ≤
      registeredAllocationDriftBudget
          (fun index => calibrationPredictionCoefficientRadius horizon sensitivity
            (dropMagnitudeBound index) (estimatedRadiusCoefficient index)
            (dropRadius index) (radiusCoefficientRadius index)) chosen +
        registeredAllocationDriftBudget
          (fun index => calibrationPredictionCoefficientRadius horizon sensitivity
            (dropMagnitudeBound index) (estimatedRadiusCoefficient index)
            (dropRadius index) (radiusCoefficientRadius index)) oracle := by
  let trueCoefficient := fun index =>
    calibrationPredictionWidthCoefficient horizon sensitivity
      (trueDrop index) (trueRadiusCoefficient index)
  let estimatedCoefficient := fun index =>
    calibrationPredictionWidthCoefficient horizon sensitivity
      (estimatedDrop index) (estimatedRadiusCoefficient index)
  let coefficientRadius := fun index =>
    calibrationPredictionCoefficientRadius horizon sensitivity
      (dropMagnitudeBound index) (estimatedRadiusCoefficient index)
      (dropRadius index) (radiusCoefficientRadius index)
  have coefficientCoverage : ∀ index,
      |trueCoefficient index - estimatedCoefficient index| ≤
        coefficientRadius index := by
    intro index
    exact calibrationPredictionCoefficient_radius_coverage horizon
      sensitivityNonnegative (dropMagnitude index) (dropCoverage index)
      (radiusCoverage index)
  have baseRegret :=
    estimated_optimum_true_regret_le_two_allocation_discrepancies
      trueCoefficient estimatedCoefficient chosen oracle chosenPositive
      oraclePositive estimatedOptimal
  have chosenBound :=
    allocationCoefficientDiscrepancy_le_registered_radius_budget
      trueCoefficient estimatedCoefficient coefficientRadius chosen
      chosenPositive coefficientCoverage
  have oracleBound :=
    allocationCoefficientDiscrepancy_le_registered_radius_budget
      trueCoefficient estimatedCoefficient coefficientRadius oracle
      oraclePositive coefficientCoverage
  exact baseRegret.trans (add_le_add chosenBound oracleBound)

/-- Reoptimization trigger: a candidate allocation is truly better than the
stale plan when its estimated improvement exceeds both registered drift
budgets. -/
theorem calibration_reoptimization_gap_certifies_true_improvement
    {Index : Type} [Fintype Index]
    (horizon : ℕ) (sensitivity : ℝ)
    (trueDrop estimatedDrop trueRadiusCoefficient estimatedRadiusCoefficient
      coefficientRadius preferred stale : Index → ℝ)
    (preferredPositive : ∀ index, 0 < preferred index)
    (stalePositive : ∀ index, 0 < stale index)
    (coefficientCoverage : ∀ index,
      |calibrationPredictionWidthCoefficient horizon sensitivity
          (trueDrop index) (trueRadiusCoefficient index) -
        calibrationPredictionWidthCoefficient horizon sensitivity
          (estimatedDrop index) (estimatedRadiusCoefficient index)| ≤
        coefficientRadius index)
    (robustGap :
      aggregateInverseSqrtAllocationCost
          (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
            (estimatedDrop index) (estimatedRadiusCoefficient index)) preferred +
        registeredAllocationDriftBudget coefficientRadius preferred <
      aggregateInverseSqrtAllocationCost
          (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
            (estimatedDrop index) (estimatedRadiusCoefficient index)) stale -
        registeredAllocationDriftBudget coefficientRadius stale) :
    aggregateInverseSqrtAllocationCost
        (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
          (trueDrop index) (trueRadiusCoefficient index)) preferred <
      aggregateInverseSqrtAllocationCost
        (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
          (trueDrop index) (trueRadiusCoefficient index)) stale := by
  exact estimated_gap_exceeding_registered_radii_certifies_true_order
    (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
      (trueDrop index) (trueRadiusCoefficient index))
    (fun index => calibrationPredictionWidthCoefficient horizon sensitivity
      (estimatedDrop index) (estimatedRadiusCoefficient index))
    coefficientRadius preferred stale preferredPositive stalePositive
    coefficientCoverage robustGap

end OCKIndividuationMSpaceComposition
