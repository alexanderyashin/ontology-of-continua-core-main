import OCKIndividuationMSpaceComposition.BrierResidualAlignmentAdmission

namespace OCKIndividuationMSpaceComposition

/-!
# Conformal coverage under a one-sided transport defect

Chronological calibration is not exchangeable with a later regime by default.
This module makes the missing assumption numerical: `delta` bounds how much
coverage can be lost when a frozen score threshold is transported from the
calibration population to the target population.
-/

/-- A one-sided transport contract for the coverage of one frozen threshold. -/
def CoverageTransportBound
    (calibrationCoverage testCoverage delta : ℝ) : Prop :=
  calibrationCoverage - testCoverage ≤ delta

/-- The guaranteed target coverage implied by nominal miscoverage `alpha` and
one-sided transport-defect budget `delta`. -/
def TransportedCoverageGuarantee (alpha delta : ℝ) : ℝ :=
  1 - alpha - delta

/-- Positive transport theorem: calibration coverage and a one-sided defect
budget give an explicit lower bound on later test coverage. -/
theorem transported_coverage_lower_bound
    (alpha delta calibrationCoverage testCoverage : ℝ)
    (calibrationGuarantee : 1 - alpha ≤ calibrationCoverage)
    (transportBound : CoverageTransportBound calibrationCoverage testCoverage delta) :
    TransportedCoverageGuarantee alpha delta ≤ testCoverage := by
  unfold CoverageTransportBound TransportedCoverageGuarantee at *
  linarith

/-- Operational budget rule: to retain coverage `1-alpha-epsilon`, it is
sufficient that the transported coverage loss is at most `epsilon`. -/
theorem defect_budget_guarantees_requested_coverage
    (alpha delta epsilon calibrationCoverage testCoverage : ℝ)
    (calibrationGuarantee : 1 - alpha ≤ calibrationCoverage)
    (transportBound : CoverageTransportBound calibrationCoverage testCoverage delta)
    (defectWithinBudget : delta ≤ epsilon) :
    1 - alpha - epsilon ≤ testCoverage := by
  have transported := transported_coverage_lower_bound
    alpha delta calibrationCoverage testCoverage calibrationGuarantee transportBound
  unfold TransportedCoverageGuarantee at transported
  linarith

/-- Sharpness theorem: the lower bound is attained exactly, so no uniformly
stronger guarantee follows from these two premises alone. -/
theorem transported_coverage_lower_bound_is_sharp
    (alpha delta : ℝ) :
    ∃ calibrationCoverage testCoverage : ℝ,
      1 - alpha ≤ calibrationCoverage ∧
      CoverageTransportBound calibrationCoverage testCoverage delta ∧
      testCoverage = TransportedCoverageGuarantee alpha delta := by
  refine ⟨1 - alpha, 1 - alpha - delta, le_rfl, ?_, rfl⟩
  unfold CoverageTransportBound
  linarith

/-- Exact minimax characterization: from the calibration guarantee and the
one-sided defect budget, a uniform target guarantee `q` is derivable if and
only if it does not exceed `1-alpha-delta`. -/
theorem uniform_target_coverage_iff_budget
    (alpha delta q : ℝ) :
    (∀ calibrationCoverage testCoverage : ℝ,
        1 - alpha ≤ calibrationCoverage →
        CoverageTransportBound calibrationCoverage testCoverage delta →
        q ≤ testCoverage) ↔
      q ≤ TransportedCoverageGuarantee alpha delta := by
  constructor
  · intro uniformGuarantee
    apply uniformGuarantee (1 - alpha) (1 - alpha - delta) le_rfl
    unfold CoverageTransportBound
    linarith
  · intro qWithinBound calibrationCoverage testCoverage calibrationGuarantee transportBound
    exact qWithinBound.trans
      (transported_coverage_lower_bound
        alpha delta calibrationCoverage testCoverage calibrationGuarantee transportBound)

/-- Under probability-valid parameters, the sharpness witness itself consists
of valid coverages in `[0,1]`.  Hence the minimax obstruction is not an artifact
of allowing impossible coverage numbers. -/
theorem transported_coverage_probability_bound_is_sharp
    (alpha delta : ℝ)
    (alphaNonnegative : 0 ≤ alpha)
    (alphaAtMostOne : alpha ≤ 1)
    (deltaNonnegative : 0 ≤ delta)
    (deltaWithinCoverage : delta ≤ 1 - alpha) :
    ∃ calibrationCoverage testCoverage : ℝ,
      calibrationCoverage ∈ Set.Icc (0 : ℝ) 1 ∧
      testCoverage ∈ Set.Icc (0 : ℝ) 1 ∧
      1 - alpha ≤ calibrationCoverage ∧
      CoverageTransportBound calibrationCoverage testCoverage delta ∧
      testCoverage = TransportedCoverageGuarantee alpha delta := by
  refine ⟨1 - alpha, 1 - alpha - delta, ?_, ?_, le_rfl, ?_, rfl⟩
  · constructor <;> linarith
  · constructor <;> linarith
  · unfold CoverageTransportBound
    linarith

/-- No-go theorem: calibration coverage alone, without a transport constraint,
cannot force any strictly positive coverage in the target regime. -/
theorem calibration_coverage_alone_does_not_force_positive_test
    (targetCoverage : ℝ) (targetPositive : 0 < targetCoverage) :
    ∃ calibrationCoverage testCoverage : ℝ,
      calibrationCoverage = 1 ∧
      testCoverage = 0 ∧
      testCoverage < targetCoverage := by
  exact ⟨1, 0, rfl, rfl, targetPositive⟩

/-- Exact observed defect for a fixed threshold.  This is a diagnostic after
both populations are observed, not a prospective transport guarantee. -/
def ObservedCoverageTransportDefect
    (calibrationCoverage testCoverage : ℝ) : ℝ :=
  calibrationCoverage - testCoverage

/-- The observed defect always satisfies its own transport inequality with
equality; it therefore measures the minimum ex-post scalar defect budget. -/
theorem observedCoverageTransportDefect_is_exact
    (calibrationCoverage testCoverage : ℝ) :
    CoverageTransportBound calibrationCoverage testCoverage
      (ObservedCoverageTransportDefect calibrationCoverage testCoverage) := by
  unfold CoverageTransportBound ObservedCoverageTransportDefect
  exact le_rfl

/-- A requested retained-coverage budget is violated exactly when the observed
coverage loss exceeds it. -/
theorem observed_defect_exceeds_budget_iff
    (calibrationCoverage testCoverage epsilon : ℝ) :
    ¬ ObservedCoverageTransportDefect calibrationCoverage testCoverage ≤ epsilon ↔
      epsilon < calibrationCoverage - testCoverage := by
  unfold ObservedCoverageTransportDefect
  exact not_le

end OCKIndividuationMSpaceComposition
