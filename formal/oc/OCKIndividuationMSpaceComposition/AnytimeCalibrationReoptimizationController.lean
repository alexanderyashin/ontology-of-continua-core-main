import OCKIndividuationMSpaceComposition.CalibrationAllocationDriftTrigger
import OCKIndividuationMSpaceComposition.SubGaussianEProcess

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory

/-!
# Anytime-valid calibration reoptimization controller

The static robust-gap theorem says when one proposed switch is sound.  This
module closes the action-level monitoring gap: estimates, radii, and selected
allocations may all depend on the observed history and monitoring look.  On a
simultaneous coefficient-coverage event, every triggered switch is a true
strict improvement.  If failure of that event is dominated by a normalized
test-supermartingale crossing, Ville's inequality controls the probability of
one or more false autonomous switches over the complete registered horizon.

The final countermodel records why a fixed-time calibration certificate cannot
be reused at multiple looks: two disjoint false-switch modes of mass `alpha`
already have familywise mass `2 * alpha > alpha`.
-/

/-- Pointwise simultaneous coefficient coverage at one monitoring look. -/
def calibrationCoefficientCoveredAt
    {Ω : Type*} {Index : Type}
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (look : ℕ) (ω : Ω) : Prop :=
  ∀ index,
    |trueCoefficient index - estimatedCoefficient look ω index| ≤
      coefficientRadius look ω index

/-- The registered robust-gap decision made by the autonomous controller. -/
def calibrationRobustSwitchAt
    {Ω : Type*} {Index : Type} [Fintype Index]
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (preferred stale : ℕ → Ω → Index → ℝ)
    (look : ℕ) (ω : Ω) : Prop :=
  (∀ index, 0 < preferred look ω index) ∧
  (∀ index, 0 < stale look ω index) ∧
  aggregateInverseSqrtAllocationCost
      (estimatedCoefficient look ω) (preferred look ω) +
    registeredAllocationDriftBudget
      (coefficientRadius look ω) (preferred look ω) <
  aggregateInverseSqrtAllocationCost
      (estimatedCoefficient look ω) (stale look ω) -
    registeredAllocationDriftBudget
      (coefficientRadius look ω) (stale look ω)

/-- A false switch is a registered robust-gap trigger whose selected plan does
not strictly improve the true allocation objective. -/
def calibrationFalseSwitch
    {Ω : Type*} {Index : Type} [Fintype Index]
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (preferred stale : ℕ → Ω → Index → ℝ)
    (horizon : ℕ) : Set Ω :=
  {ω | ∃ look ∈ Finset.range (horizon + 1),
    calibrationRobustSwitchAt estimatedCoefficient coefficientRadius
        preferred stale look ω ∧
      ¬ aggregateInverseSqrtAllocationCost trueCoefficient
          (preferred look ω) <
        aggregateInverseSqrtAllocationCost trueCoefficient
          (stale look ω)}

/-- Failure of simultaneous coefficient coverage somewhere in the registered
monitoring horizon. -/
def calibrationCoefficientCoverageFailure
    {Ω : Type*} {Index : Type}
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (horizon : ℕ) : Set Ω :=
  {ω | ∃ look ∈ Finset.range (horizon + 1),
    ¬ calibrationCoefficientCoveredAt trueCoefficient estimatedCoefficient
      coefficientRadius look ω}

/-- Positive action theorem: simultaneous coverage makes every data-adaptive
registered switch a true strict improvement, even when both allocations were
selected from the same observed history. -/
theorem calibration_robust_switch_sound_on_simultaneous_coverage
    {Ω : Type*} {Index : Type} [Fintype Index]
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (preferred stale : ℕ → Ω → Index → ℝ)
    (horizon look : ℕ) (ω : Ω)
    (lookRegistered : look ∈ Finset.range (horizon + 1))
    (simultaneousCoverage :
      ∀ registeredLook ∈ Finset.range (horizon + 1),
        calibrationCoefficientCoveredAt trueCoefficient estimatedCoefficient
          coefficientRadius registeredLook ω)
    (switches : calibrationRobustSwitchAt estimatedCoefficient
      coefficientRadius preferred stale look ω) :
    aggregateInverseSqrtAllocationCost trueCoefficient (preferred look ω) <
      aggregateInverseSqrtAllocationCost trueCoefficient (stale look ω) := by
  rcases switches with ⟨preferredPositive, stalePositive, robustGap⟩
  exact estimated_gap_exceeding_registered_radii_certifies_true_order
    trueCoefficient (estimatedCoefficient look ω)
    (coefficientRadius look ω) (preferred look ω) (stale look ω)
    preferredPositive stalePositive
    (simultaneousCoverage look lookRegistered) robustGap

/-- Deterministic safety kernel: every false switch implies failure of the
registered simultaneous coefficient-coverage contract. -/
theorem calibration_false_switch_subset_coverage_failure
    {Ω : Type*} {Index : Type} [Fintype Index]
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (preferred stale : ℕ → Ω → Index → ℝ)
    (horizon : ℕ) :
    calibrationFalseSwitch trueCoefficient estimatedCoefficient
        coefficientRadius preferred stale horizon ⊆
      calibrationCoefficientCoverageFailure trueCoefficient
        estimatedCoefficient coefficientRadius horizon := by
  intro ω falseSwitch
  by_contra noCoverageFailure
  have simultaneousCoverage :
      ∀ look ∈ Finset.range (horizon + 1),
        calibrationCoefficientCoveredAt trueCoefficient estimatedCoefficient
          coefficientRadius look ω := by
    intro look lookRegistered
    by_contra uncovered
    exact noCoverageFailure ⟨look, lookRegistered, uncovered⟩
  rcases falseSwitch with
    ⟨look, lookRegistered, switches, notTrulyBetter⟩
  exact notTrulyBetter
    (calibration_robust_switch_sound_on_simultaneous_coverage
      trueCoefficient estimatedCoefficient coefficientRadius preferred stale
      horizon look ω lookRegistered simultaneousCoverage switches)

/-- End-to-end anytime controller guarantee.  The only adapter obligation is
that a failure of the coefficient-coverage contract causes the registered
e-process to cross.  Once that is proved for a domain adapter, the probability
of at least one false automatic switch is at most `1 / threshold`. -/
theorem anytime_calibration_false_switch_probability
    {Ω : Type*} {Index : Type} [Fintype Index]
    {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (preferred stale : ℕ → Ω → Index → ℝ)
    (evidence : ℕ → Ω → ℝ)
    (supermartingale : Supermartingale evidence filtration μ)
    (nonnegative : 0 ≤ evidence)
    (initialMeanBound : ∫ ω, evidence 0 ω ∂μ ≤ 1)
    (threshold : ℝ≥0) (horizon : ℕ)
    (coverageFailureCrosses :
      calibrationCoefficientCoverageFailure trueCoefficient
          estimatedCoefficient coefficientRadius horizon ⊆
        finiteEvidenceCrossing evidence threshold horizon) :
    μ (calibrationFalseSwitch trueCoefficient estimatedCoefficient
        coefficientRadius preferred stale horizon) ≤
      ((threshold : ℝ≥0∞)⁻¹) := by
  calc
    μ (calibrationFalseSwitch trueCoefficient estimatedCoefficient
        coefficientRadius preferred stale horizon) ≤
      μ (finiteEvidenceCrossing evidence threshold horizon) :=
        measure_mono ((calibration_false_switch_subset_coverage_failure
          trueCoefficient estimatedCoefficient coefficientRadius preferred
          stale horizon).trans coverageFailureCrosses)
    _ ≤ ((threshold : ℝ≥0∞)⁻¹) :=
      test_supermartingale_finite_crossing_probability supermartingale
        nonnegative initialMeanBound threshold horizon

/-- Confidence-sequence specialization with no free event-containment premise.
The domain adapter must instead prove the semantic characterization that its
inverted e-confidence set is exactly the registered coefficient box. -/
theorem confidence_sequence_calibration_false_switch_probability
    {Ω : Type*} {Index : Type} [Fintype Index]
    {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (preferred stale : ℕ → Ω → Index → ℝ)
    (evidence : (Index → ℝ) → ℕ → Ω → ℝ)
    (supermartingale :
      Supermartingale (evidence trueCoefficient) filtration μ)
    (nonnegative : 0 ≤ evidence trueCoefficient)
    (initialMeanBound :
      ∫ ω, evidence trueCoefficient 0 ω ∂μ ≤ 1)
    (threshold : ℝ≥0) (horizon : ℕ)
    (confidenceSetIsCoefficientBox : ∀ look ω,
      trueCoefficient ∈ eConfidenceSet evidence threshold look ω ↔
        calibrationCoefficientCoveredAt trueCoefficient
          estimatedCoefficient coefficientRadius look ω) :
    μ (calibrationFalseSwitch trueCoefficient estimatedCoefficient
        coefficientRadius preferred stale horizon) ≤
      ((threshold : ℝ≥0∞)⁻¹) := by
  have failureEventEquality :
      calibrationCoefficientCoverageFailure trueCoefficient
          estimatedCoefficient coefficientRadius horizon =
        {ω | ∃ look ∈ Finset.range (horizon + 1),
          trueCoefficient ∉ eConfidenceSet evidence threshold look ω} := by
    ext ω
    constructor
    · rintro ⟨look, lookRegistered, notCovered⟩
      exact ⟨look, lookRegistered, fun retained =>
        notCovered ((confidenceSetIsCoefficientBox look ω).1 retained)⟩
    · rintro ⟨look, lookRegistered, notRetained⟩
      exact ⟨look, lookRegistered, fun covered =>
        notRetained ((confidenceSetIsCoefficientBox look ω).2 covered)⟩
  calc
    μ (calibrationFalseSwitch trueCoefficient estimatedCoefficient
        coefficientRadius preferred stale horizon) ≤
      μ (calibrationCoefficientCoverageFailure trueCoefficient
        estimatedCoefficient coefficientRadius horizon) :=
        measure_mono (calibration_false_switch_subset_coverage_failure
          trueCoefficient estimatedCoefficient coefficientRadius preferred
          stale horizon)
    _ = μ {ω | ∃ look ∈ Finset.range (horizon + 1),
        trueCoefficient ∉ eConfidenceSet evidence threshold look ω} := by
          rw [failureEventEquality]
    _ ≤ ((threshold : ℝ≥0∞)⁻¹) :=
      test_supermartingale_confidence_sequence_exclusion_control
        evidence trueCoefficient supermartingale nonnegative initialMeanBound
        threshold horizon

/-- Power/completeness direction for the controller.  A true objective gap
larger than twice both registered drift budgets forces the robust-gap trigger;
the factor two is the price of moving both estimated interval centres against
the desired ordering. -/
theorem true_separation_forces_calibration_robust_switch
    {Ω : Type*} {Index : Type} [Fintype Index]
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (preferred stale : ℕ → Ω → Index → ℝ)
    (look : ℕ) (ω : Ω)
    (preferredPositive : ∀ index, 0 < preferred look ω index)
    (stalePositive : ∀ index, 0 < stale look ω index)
    (coverage : calibrationCoefficientCoveredAt trueCoefficient
      estimatedCoefficient coefficientRadius look ω)
    (trueSeparation :
      aggregateInverseSqrtAllocationCost trueCoefficient
          (preferred look ω) +
          2 * registeredAllocationDriftBudget
            (coefficientRadius look ω) (preferred look ω) <
        aggregateInverseSqrtAllocationCost trueCoefficient
          (stale look ω) -
          2 * registeredAllocationDriftBudget
            (coefficientRadius look ω) (stale look ω)) :
    calibrationRobustSwitchAt estimatedCoefficient coefficientRadius
      preferred stale look ω := by
  have preferredError :
      |aggregateInverseSqrtAllocationCost trueCoefficient
          (preferred look ω) -
        aggregateInverseSqrtAllocationCost (estimatedCoefficient look ω)
          (preferred look ω)| ≤
        registeredAllocationDriftBudget (coefficientRadius look ω)
          (preferred look ω) := by
    exact (aggregateInverseSqrtAllocationCost_coefficient_perturbation
      trueCoefficient (estimatedCoefficient look ω) (preferred look ω)
      preferredPositive).trans
        (allocationCoefficientDiscrepancy_le_registered_radius_budget
          trueCoefficient (estimatedCoefficient look ω)
          (coefficientRadius look ω) (preferred look ω) preferredPositive
          coverage)
  have staleError :
      |aggregateInverseSqrtAllocationCost trueCoefficient (stale look ω) -
        aggregateInverseSqrtAllocationCost (estimatedCoefficient look ω)
          (stale look ω)| ≤
        registeredAllocationDriftBudget (coefficientRadius look ω)
          (stale look ω) := by
    exact (aggregateInverseSqrtAllocationCost_coefficient_perturbation
      trueCoefficient (estimatedCoefficient look ω) (stale look ω)
      stalePositive).trans
        (allocationCoefficientDiscrepancy_le_registered_radius_budget
          trueCoefficient (estimatedCoefficient look ω)
          (coefficientRadius look ω) (stale look ω) stalePositive coverage)
  refine ⟨preferredPositive, stalePositive, ?_⟩
  have preferredBounds := abs_le.mp preferredError
  have staleBounds := abs_le.mp staleError
  linarith

/-- Independent-equivalent observation count sufficient for detecting a true
reoptimization gap when both plan budgets decay at inverse-square-root rate. -/
noncomputable def reoptimizationDetectionRequiredCount
    (preferredRadiusCoefficient staleRadiusCoefficient trueGap : ℝ) : ℝ :=
  (2 * (preferredRadiusCoefficient + staleRadiusCoefficient) / trueGap) ^ 2

/-- Explicit detection-delay law.  Once the independent-equivalent count is
strictly above the displayed threshold, twice the two radius budgets fit
inside the true objective gap. -/
theorem reoptimization_detection_sample_threshold
    (preferredRadiusCoefficient staleRadiusCoefficient trueGap
      observations : ℝ)
    (preferredNonnegative : 0 ≤ preferredRadiusCoefficient)
    (staleNonnegative : 0 ≤ staleRadiusCoefficient)
    (gapPositive : 0 < trueGap)
    (observationsPositive : 0 < observations)
    (enough : reoptimizationDetectionRequiredCount preferredRadiusCoefficient
      staleRadiusCoefficient trueGap < observations) :
    2 * inverseSqrtRiskRadius preferredRadiusCoefficient observations +
        2 * inverseSqrtRiskRadius staleRadiusCoefficient observations <
      trueGap := by
  have requiredIdentity :
      dominanceRequiredIndependentCount
          (2 * preferredRadiusCoefficient)
          (2 * staleRadiusCoefficient) trueGap =
        reoptimizationDetectionRequiredCount preferredRadiusCoefficient
          staleRadiusCoefficient trueGap := by
    unfold dominanceRequiredIndependentCount
      reoptimizationDetectionRequiredCount
    ring
  have pairRadii := dominance_sample_threshold_makes_pair_radii_smaller_than_gap
    (2 * preferredRadiusCoefficient) (2 * staleRadiusCoefficient) trueGap
    observations (mul_nonneg (by norm_num) preferredNonnegative)
    (mul_nonneg (by norm_num) staleNonnegative) gapPositive
    observationsPositive (by simpa [requiredIdentity] using enough)
  unfold inverseSqrtRiskRadius at pairRadii ⊢
  convert pairRadii using 1 <;> ring

/-- Numeric canary: radius coefficients `1` and `2` with true gap `1` require
more than `36` independent-equivalent observations. -/
theorem reoptimization_detection_canary_required_count :
    reoptimizationDetectionRequiredCount 1 2 1 = 36 := by
  norm_num [reoptimizationDetectionRequiredCount]

/-- At `49` independent-equivalent observations the canary uncertainty is
exactly `6/7`, hence the gap-one switch is forced on the coverage event. -/
theorem reoptimization_detection_canary_forty_nine :
    2 * inverseSqrtRiskRadius 1 49 +
        2 * inverseSqrtRiskRadius 2 49 = (6 : ℝ) / 7 ∧
      2 * inverseSqrtRiskRadius 1 49 +
          2 * inverseSqrtRiskRadius 2 49 < 1 := by
  have sqrtFortyNine : Real.sqrt (49 : ℝ) = 7 := by
    calc
      Real.sqrt (49 : ℝ) = Real.sqrt ((7 : ℝ) ^ 2) := by norm_num
      _ = 7 := Real.sqrt_sq (by norm_num)
  constructor
  · simp [inverseSqrtRiskRadius, sqrtFortyNine]
    norm_num
  · exact reoptimization_detection_sample_threshold 1 2 1 49
      (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by
        norm_num [reoptimizationDetectionRequiredCount])

/-- Operational specialization: an e-process threshold of `20` bounds the
familywise probability of one or more false switches by `1/20`. -/
theorem threshold_twenty_controls_false_switches_at_one_in_twenty
    {Ω : Type*} {Index : Type} [Fintype Index]
    {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Ω → Index → ℝ)
    (preferred stale : ℕ → Ω → Index → ℝ)
    (evidence : ℕ → Ω → ℝ)
    (supermartingale : Supermartingale evidence filtration μ)
    (nonnegative : 0 ≤ evidence)
    (initialMeanBound : ∫ ω, evidence 0 ω ∂μ ≤ 1)
    (horizon : ℕ)
    (coverageFailureCrosses :
      calibrationCoefficientCoverageFailure trueCoefficient
          estimatedCoefficient coefficientRadius horizon ⊆
        finiteEvidenceCrossing evidence (20 : ℝ≥0) horizon) :
    μ (calibrationFalseSwitch trueCoefficient estimatedCoefficient
        coefficientRadius preferred stale horizon) ≤ (20 : ℝ≥0∞)⁻¹ := by
  exact anytime_calibration_false_switch_probability
    trueCoefficient estimatedCoefficient coefficientRadius preferred stale
    evidence supermartingale nonnegative initialMeanBound 20 horizon
    coverageFailureCrosses

/-- No-go theorem for fixed-time reuse at the action layer.  If two disjoint
false-switch modes each have mass `alpha`, reporting the single-look value
`alpha` is strictly anti-conservative. -/
theorem two_look_fixed_time_false_switch_report_is_anti_conservative
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} (falseSwitchAtFirst falseSwitchAtSecond : Set Ω)
    (alpha : ℝ≥0∞)
    (alphaPositive : 0 < alpha) (alphaFinite : alpha ≠ ∞)
    (firstMeasurable : MeasurableSet falseSwitchAtFirst)
    (disjointFalseSwitches :
      Disjoint falseSwitchAtFirst falseSwitchAtSecond)
    (firstMass : μ falseSwitchAtFirst = alpha)
    (secondMass : μ falseSwitchAtSecond = alpha) :
    alpha < μ (falseSwitchAtFirst ∪ falseSwitchAtSecond) := by
  exact disjoint_fixed_time_crossings_exceed_single_look_report alpha
    alphaPositive alphaFinite firstMeasurable disjointFalseSwitches
    firstMass secondMass

end OCKIndividuationMSpaceComposition
