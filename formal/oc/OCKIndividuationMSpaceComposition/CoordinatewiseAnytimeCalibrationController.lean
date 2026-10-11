import OCKIndividuationMSpaceComposition.AnytimeCalibrationReoptimizationController

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory

/-!
# Coordinatewise anytime calibration control

Real calibration adapters normally estimate several coefficients separately.
This module composes one anytime-valid e-process per coefficient into a finite
simultaneous coefficient box and then into the autonomous reoptimization
controller.  Dependence across coordinates and across looks is unrestricted;
the price is the explicit finite union budget.
-/

/-- Failure of coordinate `index` to retain its true scalar coefficient at
some registered monitoring look. -/
def coordinateEConfidenceFailure
    {Ω Index : Type*}
    (evidence : Index → ℝ → ℕ → Ω → ℝ)
    (threshold : Index → ℝ≥0)
    (trueCoefficient : Index → ℝ)
    (horizon : ℕ) (index : Index) : Set Ω :=
  {ω | ∃ look ∈ Finset.range (horizon + 1),
    trueCoefficient index ∉
      eConfidenceSet (evidence index) (threshold index) look ω}

/-- Registered familywise error budget of finitely many coordinate e-processes.
Each coordinate contributes the Ville term `1 / threshold_i`. -/
noncomputable def coordinatewiseFalseSwitchBudget
    {Index : Type*} [Fintype Index]
    (threshold : Index → ℝ≥0) : ℝ≥0∞ :=
  ∑ index, (((threshold index : ℝ≥0) : ℝ≥0∞)⁻¹)

/-- Semantic adapter: if every scalar inverted confidence set is exactly its
registered interval, any failure of the coefficient box occurs in at least one
coordinate confidence sequence. -/
theorem coefficient_box_failure_subset_coordinate_union
    {Ω : Type*} {Index : Type} [Fintype Index]
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (evidence : Index → ℝ → ℕ → Ω → ℝ)
    (threshold : Index → ℝ≥0) (horizon : ℕ)
    (coordinateSetIsInterval : ∀ index look ω,
      trueCoefficient index ∈
          eConfidenceSet (evidence index) (threshold index) look ω ↔
        |trueCoefficient index - estimatedCoefficient look ω index| ≤
          coefficientRadius look ω index) :
    calibrationCoefficientCoverageFailure trueCoefficient
        estimatedCoefficient coefficientRadius horizon ⊆
      ⋃ index, coordinateEConfidenceFailure evidence threshold
        trueCoefficient horizon index := by
  classical
  intro ω coverageFailure
  rcases coverageFailure with ⟨look, lookRegistered, notCovered⟩
  simp only [calibrationCoefficientCoveredAt] at notCovered
  push_neg at notCovered
  obtain ⟨index, coordinateNotCovered⟩ := notCovered
  simp only [Set.mem_iUnion]
  refine ⟨index, look, lookRegistered, ?_⟩
  intro retained
  exact (not_lt_of_ge ((coordinateSetIsInterval index look ω).1 retained))
    coordinateNotCovered

/-- Main coordinatewise theorem: with one normalized nonnegative test
supermartingale per coefficient, the probability of one or more false
history-adaptive switches is bounded by the sum of inverse thresholds. -/
theorem coordinatewise_anytime_calibration_false_switch_probability
    {Ω : Type*} {Index : Type} [Fintype Index]
    {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (preferred stale : ℕ → Ω → Index → ℝ)
    (evidence : Index → ℝ → ℕ → Ω → ℝ)
    (threshold : Index → ℝ≥0) (horizon : ℕ)
    (supermartingale : ∀ index,
      Supermartingale (evidence index (trueCoefficient index)) filtration μ)
    (nonnegative : ∀ index,
      0 ≤ evidence index (trueCoefficient index))
    (initialMeanBound : ∀ index,
      ∫ ω, evidence index (trueCoefficient index) 0 ω ∂μ ≤ 1)
    (coordinateSetIsInterval : ∀ index look ω,
      trueCoefficient index ∈
          eConfidenceSet (evidence index) (threshold index) look ω ↔
        |trueCoefficient index - estimatedCoefficient look ω index| ≤
          coefficientRadius look ω index) :
    μ (calibrationFalseSwitch trueCoefficient estimatedCoefficient
        coefficientRadius preferred stale horizon) ≤
      coordinatewiseFalseSwitchBudget threshold := by
  classical
  let coordinateFailure := fun index =>
    coordinateEConfidenceFailure evidence threshold trueCoefficient
      horizon index
  have falseSwitchSubset :
      calibrationFalseSwitch trueCoefficient estimatedCoefficient
          coefficientRadius preferred stale horizon ⊆
        ⋃ index, coordinateFailure index :=
    (calibration_false_switch_subset_coverage_failure trueCoefficient
      estimatedCoefficient coefficientRadius preferred stale horizon).trans
      (coefficient_box_failure_subset_coordinate_union trueCoefficient
        estimatedCoefficient coefficientRadius evidence threshold horizon
        coordinateSetIsInterval)
  have coordinateBound : ∀ index,
      μ (coordinateFailure index) ≤
        (((threshold index : ℝ≥0) : ℝ≥0∞)⁻¹) := by
    intro index
    exact test_supermartingale_confidence_sequence_exclusion_control
      (evidence index) (trueCoefficient index) (supermartingale index)
      (nonnegative index) (initialMeanBound index) (threshold index) horizon
  calc
    μ (calibrationFalseSwitch trueCoefficient estimatedCoefficient
        coefficientRadius preferred stale horizon) ≤
      μ (⋃ index, coordinateFailure index) := measure_mono falseSwitchSubset
    _ ≤ ∑ index, μ (coordinateFailure index) :=
      measure_iUnion_fintype_le μ coordinateFailure
    _ ≤ ∑ index, (((threshold index : ℝ≥0) : ℝ≥0∞)⁻¹) :=
      Finset.sum_le_sum fun index _ => coordinateBound index
    _ = coordinatewiseFalseSwitchBudget threshold := rfl

/-- Uniform coordinate thresholds multiply the single-coordinate Ville budget
by the finite coefficient count. -/
theorem uniform_coordinate_threshold_budget
    {Index : Type*} [Fintype Index] (threshold : ℝ≥0) :
    coordinatewiseFalseSwitchBudget (fun _ : Index => threshold) =
      (Fintype.card Index : ℝ≥0∞) * ((threshold : ℝ≥0∞)⁻¹) := by
  simp [coordinatewiseFalseSwitchBudget]

/-- Reciprocal conversion from the alpha-allocation language used by the
existing target-blind optimizer to the e-process threshold language used by
the controller. -/
theorem reciprocal_alpha_coordinate_budget_exact
    {Index : Type*} [Fintype Index]
    (alpha : Index → ℝ≥0)
    (alphaPositive : ∀ index, 0 < alpha index) :
    coordinatewiseFalseSwitchBudget (fun index => (alpha index)⁻¹) =
      ∑ index, ((alpha index : ℝ≥0) : ℝ≥0∞) := by
  unfold coordinatewiseFalseSwitchBudget
  apply Finset.sum_congr rfl
  intro index _
  rw [ENNReal.coe_inv (ne_of_gt (alphaPositive index)), inv_inv]

/-- Therefore every positive finite alpha allocation whose total mass is at
most `delta` induces a coordinate e-process threshold schedule with the same
familywise controller budget. -/
theorem reciprocal_alpha_coordinate_budget_le
    {Index : Type*} [Fintype Index]
    (alpha : Index → ℝ≥0) (delta : ℝ≥0∞)
    (alphaPositive : ∀ index, 0 < alpha index)
    (totalBound : (∑ index, ((alpha index : ℝ≥0) : ℝ≥0∞)) ≤ delta) :
    coordinatewiseFalseSwitchBudget (fun index => (alpha index)⁻¹) ≤
      delta := by
  rw [reciprocal_alpha_coordinate_budget_exact alpha alphaPositive]
  exact totalBound

/-- Numeric two-coordinate canary: threshold `40` on each coefficient gives
the same familywise budget `1/20` as a joint threshold `20`. -/
theorem two_coordinate_threshold_forty_budget :
    coordinatewiseFalseSwitchBudget (fun _ : Fin 2 => (40 : ℝ≥0)) =
      (20 : ℝ≥0∞)⁻¹ := by
  rw [uniform_coordinate_threshold_budget]
  apply (ENNReal.toReal_eq_toReal_iff'
    (ENNReal.mul_ne_top (by simp)
      (ENNReal.inv_ne_top.mpr (by norm_num))) (by simp)).mp
  norm_num

end OCKIndividuationMSpaceComposition
