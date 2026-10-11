import OCKIndividuationMSpaceComposition.RobustEvidenceTransportDefect
import OCKIndividuationMSpaceComposition.DefectResponseDynamics

namespace OCKIndividuationMSpaceComposition

universe uFamily

/-!
# Robust transport-defect to governance-hazard prediction

This module connects a registered calibration-weight box to a finite-horizon
behavioral prediction.  The response law is an explicit domain adapter.  OC
does not assert that every governance hazard is affine in transport defect.
-/

def realAffineDefectHazard
    (baseline sensitivity defect : ℝ) : ℝ :=
  baseline + sensitivity * defect

def realClippedAffineDefectHazard
    (baseline sensitivity defect : ℝ) : ℝ :=
  max 0 (min 1 (realAffineDefectHazard baseline sensitivity defect))

def realFiniteHorizonBarrierCdf (hazard : ℝ) (horizon : ℕ) : ℝ :=
  1 - (1 - hazard) ^ horizon

theorem realClippedAffineDefectHazard_bounds
    (baseline sensitivity defect : ℝ) :
    0 ≤ realClippedAffineDefectHazard baseline sensitivity defect ∧
      realClippedAffineDefectHazard baseline sensitivity defect ≤ 1 := by
  constructor
  · exact le_max_left _ _
  · exact max_le (by norm_num) (min_le_left _ _)

theorem realClippedAffineDefectHazard_mono
    {baseline sensitivity first second : ℝ}
    (sensitivityNonnegative : 0 ≤ sensitivity)
    (ordered : first ≤ second) :
    realClippedAffineDefectHazard baseline sensitivity first ≤
      realClippedAffineDefectHazard baseline sensitivity second := by
  have raw : realAffineDefectHazard baseline sensitivity first ≤
      realAffineDefectHazard baseline sensitivity second := by
    unfold realAffineDefectHazard
    simpa [add_comm] using add_le_add_left
      (mul_le_mul_of_nonneg_left ordered sensitivityNonnegative) baseline
  exact max_le_max le_rfl (min_le_min le_rfl raw)

theorem realClippedAffineDefectHazard_eq_affine_of_interior
    {baseline sensitivity defect : ℝ}
    (nonnegative : 0 ≤ realAffineDefectHazard baseline sensitivity defect)
    (atMostOne : realAffineDefectHazard baseline sensitivity defect ≤ 1) :
    realClippedAffineDefectHazard baseline sensitivity defect =
      realAffineDefectHazard baseline sensitivity defect := by
  simp [realClippedAffineDefectHazard, min_eq_right atMostOne,
    max_eq_right nonnegative]

theorem realFiniteHorizonBarrierCdf_mono
    {first second : ℝ}
    (secondBounds : 0 ≤ second ∧ second ≤ 1)
    (ordered : first ≤ second)
    (horizon : ℕ) :
    realFiniteHorizonBarrierCdf first horizon ≤
      realFiniteHorizonBarrierCdf second horizon := by
  have baseOrder : 1 - second ≤ 1 - first := sub_le_sub_left ordered 1
  have secondBaseNonnegative : 0 ≤ 1 - second := sub_nonneg.mpr secondBounds.2
  have powers := pow_le_pow_left₀ secondBaseNonnegative baseOrder horizon
  unfold realFiniteHorizonBarrierCdf
  linarith

/-- Finite-horizon CDF is `horizon`-Lipschitz in a constant hazard on the unit
interval. -/
theorem realFiniteHorizonBarrierCdf_error_le_horizon_mul_hazardError
    (first second : ℝ)
    (firstBounds : 0 ≤ first ∧ first ≤ 1)
    (secondBounds : 0 ≤ second ∧ second ≤ 1)
    (horizon : ℕ) :
    |realFiniteHorizonBarrierCdf first horizon -
        realFiniteHorizonBarrierCdf second horizon| ≤
      (horizon : ℝ) * |first - second| := by
  have firstBaseNonnegative : 0 ≤ 1 - first := sub_nonneg.mpr firstBounds.2
  have secondBaseNonnegative : 0 ≤ 1 - second := sub_nonneg.mpr secondBounds.2
  have firstBaseAbsLe : |1 - first| ≤ 1 := by
    rw [abs_of_nonneg firstBaseNonnegative]
    linarith [firstBounds.1]
  have secondBaseAbsLe : |1 - second| ≤ 1 := by
    rw [abs_of_nonneg secondBaseNonnegative]
    linarith [secondBounds.1]
  have maximumNonnegative : 0 ≤ max |1 - first| |1 - second| :=
    (abs_nonneg _).trans (le_max_left _ _)
  have maximumAtMostOne : max |1 - first| |1 - second| ≤ 1 :=
    max_le firstBaseAbsLe secondBaseAbsLe
  have maximumPowerAtMostOne :
      max |1 - first| |1 - second| ^ (horizon - 1) ≤ 1 :=
    pow_le_one₀ maximumNonnegative maximumAtMostOne
  have powerDifference := abs_pow_sub_pow_le
    (a := (1 - first : ℝ)) (b := (1 - second : ℝ)) (n := horizon)
  unfold realFiniteHorizonBarrierCdf
  calc
    |(1 - (1 - first) ^ horizon) - (1 - (1 - second) ^ horizon)| =
        |(1 - first) ^ horizon - (1 - second) ^ horizon| := by
      rw [abs_sub_comm]
      congr 1
      ring
    _ ≤ |(1 - first) - (1 - second)| * (horizon : ℝ) *
        max |1 - first| |1 - second| ^ (horizon - 1) := powerDifference
    _ ≤ |(1 - first) - (1 - second)| * (horizon : ℝ) * 1 := by
      exact mul_le_mul_of_nonneg_left maximumPowerAtMostOne
        (mul_nonneg (abs_nonneg _) (by positivity))
    _ = (horizon : ℝ) * |first - second| := by
      rw [show (1 - first) - (1 - second) = -(first - second) by ring,
        abs_neg]
      ring

def robustTransportHazardLower
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (baseline sensitivity : ℝ)
    (source target : EvidencePotential Family) : ℝ :=
  realClippedAffineDefectHazard baseline sensitivity
    (robustLowerEvidenceTransportDefect box source target)

def robustTransportHazardUpper
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (baseline sensitivity : ℝ)
    (source target : EvidencePotential Family) : ℝ :=
  realClippedAffineDefectHazard baseline sensitivity
    (robustUpperEvidenceTransportDefect box source target)

def transportHazardAtWeights
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (baseline sensitivity : ℝ)
    (source target : EvidencePotential Family) : ℝ :=
  realClippedAffineDefectHazard baseline sensitivity
    (weightedEvidenceTransportDefect weights source target)

/-- Every admissible calibration yields a hazard inside the robust endpoint
interval when response sensitivity is nonnegative. -/
theorem admissible_weight_transportHazard_sandwich
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    {weights : EvidenceTransportWeights}
    (admissible : box.Admissible weights)
    (baseline sensitivity : ℝ)
    (sensitivityNonnegative : 0 ≤ sensitivity)
    (source target : EvidencePotential Family) :
    robustTransportHazardLower box baseline sensitivity source target ≤
        transportHazardAtWeights weights baseline sensitivity source target ∧
      transportHazardAtWeights weights baseline sensitivity source target ≤
        robustTransportHazardUpper box baseline sensitivity source target := by
  have defectBounds := admissible_weight_defect_sandwich box admissible source target
  exact ⟨
    realClippedAffineDefectHazard_mono sensitivityNonnegative defectBounds.1,
    realClippedAffineDefectHazard_mono sensitivityNonnegative defectBounds.2⟩

def robustTransportCdfLower
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (baseline sensitivity : ℝ)
    (source target : EvidencePotential Family)
    (horizon : ℕ) : ℝ :=
  realFiniteHorizonBarrierCdf
    (robustTransportHazardLower box baseline sensitivity source target) horizon

def robustTransportCdfUpper
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (baseline sensitivity : ℝ)
    (source target : EvidencePotential Family)
    (horizon : ℕ) : ℝ :=
  realFiniteHorizonBarrierCdf
    (robustTransportHazardUpper box baseline sensitivity source target) horizon

def transportCdfAtWeights
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (baseline sensitivity : ℝ)
    (source target : EvidencePotential Family)
    (horizon : ℕ) : ℝ :=
  realFiniteHorizonBarrierCdf
    (transportHazardAtWeights weights baseline sensitivity source target) horizon

/-- The calibration box propagates to a finite-horizon behavioral prediction
interval. -/
theorem admissible_weight_transportCdf_sandwich
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    {weights : EvidenceTransportWeights}
    (admissible : box.Admissible weights)
    (baseline sensitivity : ℝ)
    (sensitivityNonnegative : 0 ≤ sensitivity)
    (source target : EvidencePotential Family)
    (horizon : ℕ) :
    robustTransportCdfLower box baseline sensitivity source target horizon ≤
        transportCdfAtWeights weights baseline sensitivity source target horizon ∧
      transportCdfAtWeights weights baseline sensitivity source target horizon ≤
        robustTransportCdfUpper box baseline sensitivity source target horizon := by
  have hazardBounds := admissible_weight_transportHazard_sandwich box admissible
    baseline sensitivity sensitivityNonnegative source target
  have currentBounds := realClippedAffineDefectHazard_bounds baseline sensitivity
    (weightedEvidenceTransportDefect weights source target)
  have upperBounds := realClippedAffineDefectHazard_bounds baseline sensitivity
    (robustUpperEvidenceTransportDefect box source target)
  exact ⟨
    realFiniteHorizonBarrierCdf_mono currentBounds
      hazardBounds.1 horizon,
    realFiniteHorizonBarrierCdf_mono upperBounds
      hazardBounds.2 horizon⟩

/-- Inside the unclipped affine region, hazard uncertainty is exactly response
sensitivity times defect uncertainty. -/
theorem robustTransportHazard_width_eq_sensitivity_mul_defectWidth_of_interior
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (baseline sensitivity : ℝ)
    (source target : EvidencePotential Family)
    (lowerNonnegative : 0 ≤ realAffineDefectHazard baseline sensitivity
      (robustLowerEvidenceTransportDefect box source target))
    (lowerAtMostOne : realAffineDefectHazard baseline sensitivity
      (robustLowerEvidenceTransportDefect box source target) ≤ 1)
    (upperNonnegative : 0 ≤ realAffineDefectHazard baseline sensitivity
      (robustUpperEvidenceTransportDefect box source target))
    (upperAtMostOne : realAffineDefectHazard baseline sensitivity
      (robustUpperEvidenceTransportDefect box source target) ≤ 1) :
    robustTransportHazardUpper box baseline sensitivity source target -
        robustTransportHazardLower box baseline sensitivity source target =
      sensitivity *
        (robustUpperEvidenceTransportDefect box source target -
          robustLowerEvidenceTransportDefect box source target) := by
  unfold robustTransportHazardUpper robustTransportHazardLower
  rw [realClippedAffineDefectHazard_eq_affine_of_interior
      lowerNonnegative lowerAtMostOne,
    realClippedAffineDefectHazard_eq_affine_of_interior
      upperNonnegative upperAtMostOne]
  unfold realAffineDefectHazard
  ring

/-- Operational uncertainty propagation: under an interior affine adapter,
finite-horizon CDF width is at most horizon times sensitivity times the exact
weight-calibration defect width. -/
theorem robustTransportCdf_width_le_horizon_mul_sensitivity_defectWidth
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (baseline sensitivity : ℝ)
    (sensitivityNonnegative : 0 ≤ sensitivity)
    (source target : EvidencePotential Family)
    (horizon : ℕ)
    (lowerNonnegative : 0 ≤ realAffineDefectHazard baseline sensitivity
      (robustLowerEvidenceTransportDefect box source target))
    (lowerAtMostOne : realAffineDefectHazard baseline sensitivity
      (robustLowerEvidenceTransportDefect box source target) ≤ 1)
    (upperNonnegative : 0 ≤ realAffineDefectHazard baseline sensitivity
      (robustUpperEvidenceTransportDefect box source target))
    (upperAtMostOne : realAffineDefectHazard baseline sensitivity
      (robustUpperEvidenceTransportDefect box source target) ≤ 1) :
    robustTransportCdfUpper box baseline sensitivity source target horizon -
        robustTransportCdfLower box baseline sensitivity source target horizon ≤
      (horizon : ℝ) * sensitivity *
        (robustUpperEvidenceTransportDefect box source target -
          robustLowerEvidenceTransportDefect box source target) := by
  have defectOrder := weightedEvidenceTransportDefect_mono_weights
    box.lower_le_upper source target
  have hazardOrder :
      robustTransportHazardLower box baseline sensitivity source target ≤
        robustTransportHazardUpper box baseline sensitivity source target :=
    realClippedAffineDefectHazard_mono sensitivityNonnegative defectOrder
  have lowerBounds := realClippedAffineDefectHazard_bounds baseline sensitivity
    (robustLowerEvidenceTransportDefect box source target)
  have upperBounds := realClippedAffineDefectHazard_bounds baseline sensitivity
    (robustUpperEvidenceTransportDefect box source target)
  have cdfError := realFiniteHorizonBarrierCdf_error_le_horizon_mul_hazardError
    (robustTransportHazardUpper box baseline sensitivity source target)
    (robustTransportHazardLower box baseline sensitivity source target)
    upperBounds lowerBounds horizon
  have hazardWidth :=
    robustTransportHazard_width_eq_sensitivity_mul_defectWidth_of_interior
      box baseline sensitivity source target lowerNonnegative lowerAtMostOne
      upperNonnegative upperAtMostOne
  calc
    robustTransportCdfUpper box baseline sensitivity source target horizon -
        robustTransportCdfLower box baseline sensitivity source target horizon ≤
      |robustTransportCdfUpper box baseline sensitivity source target horizon -
        robustTransportCdfLower box baseline sensitivity source target horizon| :=
      le_abs_self _
    _ ≤ (horizon : ℝ) *
        |robustTransportHazardUpper box baseline sensitivity source target -
          robustTransportHazardLower box baseline sensitivity source target| :=
      cdfError
    _ = (horizon : ℝ) * sensitivity *
        (robustUpperEvidenceTransportDefect box source target -
          robustLowerEvidenceTransportDefect box source target) := by
      rw [abs_of_nonneg (sub_nonneg.mpr hazardOrder), hazardWidth]
      ring

/-- Fully expanded operational bound: every calibration-width coordinate is
multiplied by its observed directed drop, response sensitivity, and horizon. -/
theorem robustTransportCdf_width_le_expanded_calibration_budget
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (baseline sensitivity : ℝ)
    (sensitivityNonnegative : 0 ≤ sensitivity)
    (source target : EvidencePotential Family)
    (horizon : ℕ)
    (lowerNonnegative : 0 ≤ realAffineDefectHazard baseline sensitivity
      (robustLowerEvidenceTransportDefect box source target))
    (lowerAtMostOne : realAffineDefectHazard baseline sensitivity
      (robustLowerEvidenceTransportDefect box source target) ≤ 1)
    (upperNonnegative : 0 ≤ realAffineDefectHazard baseline sensitivity
      (robustUpperEvidenceTransportDefect box source target))
    (upperAtMostOne : realAffineDefectHazard baseline sensitivity
      (robustUpperEvidenceTransportDefect box source target) ≤ 1) :
    robustTransportCdfUpper box baseline sensitivity source target horizon -
        robustTransportCdfLower box baseline sensitivity source target horizon ≤
      (horizon : ℝ) * sensitivity *
        ((box.upper.lookWeight - box.lower.lookWeight) *
            directedDrop source.look target.look +
          (box.upper.spendWeight - box.lower.spendWeight) *
            directedDrop source.cumulativeAlphaSpend
              target.cumulativeAlphaSpend +
          (box.upper.debtWeight - box.lower.debtWeight) *
            directedDrop source.calibrationDebt target.calibrationDebt) := by
  calc
    robustTransportCdfUpper box baseline sensitivity source target horizon -
        robustTransportCdfLower box baseline sensitivity source target horizon ≤
      (horizon : ℝ) * sensitivity *
        (robustUpperEvidenceTransportDefect box source target -
          robustLowerEvidenceTransportDefect box source target) :=
      robustTransportCdf_width_le_horizon_mul_sensitivity_defectWidth
        box baseline sensitivity sensitivityNonnegative source target horizon
        lowerNonnegative lowerAtMostOne upperNonnegative upperAtMostOne
    _ = (horizon : ℝ) * sensitivity *
        ((box.upper.lookWeight - box.lower.lookWeight) *
            directedDrop source.look target.look +
          (box.upper.spendWeight - box.lower.spendWeight) *
            directedDrop source.cumulativeAlphaSpend
              target.cumulativeAlphaSpend +
          (box.upper.debtWeight - box.lower.debtWeight) *
            directedDrop source.calibrationDebt target.calibrationDebt) := by
      rw [robustEvidenceTransportDefect_width_eq]

/-- If a governance threshold cuts the robust CDF interval, two admissible
calibrations support opposite finite-horizon decisions. -/
theorem threshold_inside_robust_transportCdf_is_calibration_unresolved
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (baseline sensitivity threshold : ℝ)
    (source target : EvidencePotential Family)
    (horizon : ℕ)
    (lowerPass : robustTransportCdfLower box baseline sensitivity
      source target horizon ≤ threshold)
    (upperFails : threshold < robustTransportCdfUpper box baseline sensitivity
      source target horizon) :
    (∃ weights, box.Admissible weights ∧
      transportCdfAtWeights weights baseline sensitivity
        source target horizon ≤ threshold) ∧
    (∃ weights, box.Admissible weights ∧
      threshold < transportCdfAtWeights weights baseline sensitivity
        source target horizon) := by
  exact ⟨⟨box.lower, box.lower_admissible, lowerPass⟩,
    ⟨box.upper, box.upper_admissible, upperFails⟩⟩

end OCKIndividuationMSpaceComposition
