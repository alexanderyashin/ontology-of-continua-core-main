import OCKIndividuationMSpaceComposition.BoundedInverseSqrtSampleAllocation

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Robustness of adaptive sample allocation under coefficient drift

The static allocation theorem is conditional on registered width
coefficients.  This module quantifies how coefficient error propagates to the
allocation objective, derives a regret certificate for an estimated optimum,
and proves that without a finite drift budget stale-plan regret is unbounded.
-/

/-- Aggregate inverse-square-root width of a finite allocation. -/
noncomputable def aggregateInverseSqrtAllocationCost
    {Index : Type} [Fintype Index]
    (coefficient allocation : Index → ℝ) : ℝ :=
  ∑ index, inverseSqrtAllocationCost
    (coefficient index) (allocation index)

/-- Exact observable discrepancy budget induced by coefficient perturbation
at a fixed positive allocation. -/
noncomputable def allocationCoefficientDiscrepancy
    {Index : Type} [Fintype Index]
    (trueCoefficient estimatedCoefficient allocation : Index → ℝ) : ℝ :=
  ∑ index, |trueCoefficient index - estimatedCoefficient index| /
    Real.sqrt (allocation index)

/-- Computable upper budget obtained from simultaneous coefficient radii. -/
noncomputable def registeredAllocationDriftBudget
    {Index : Type} [Fintype Index]
    (coefficientRadius allocation : Index → ℝ) : ℝ :=
  ∑ index, coefficientRadius index / Real.sqrt (allocation index)

/-- Coefficient perturbations propagate linearly through a fixed allocation's
aggregate width. -/
theorem aggregateInverseSqrtAllocationCost_coefficient_perturbation
    {Index : Type} [Fintype Index]
    (trueCoefficient estimatedCoefficient allocation : Index → ℝ)
    (allocationPositive : ∀ index, 0 < allocation index) :
    |aggregateInverseSqrtAllocationCost trueCoefficient allocation -
        aggregateInverseSqrtAllocationCost estimatedCoefficient allocation| ≤
      allocationCoefficientDiscrepancy
        trueCoefficient estimatedCoefficient allocation := by
  rw [aggregateInverseSqrtAllocationCost,
    aggregateInverseSqrtAllocationCost, ← Finset.sum_sub_distrib]
  calc
    |∑ index, (inverseSqrtAllocationCost
        (trueCoefficient index) (allocation index) -
      inverseSqrtAllocationCost
        (estimatedCoefficient index) (allocation index))| ≤
      ∑ index, |inverseSqrtAllocationCost
        (trueCoefficient index) (allocation index) -
      inverseSqrtAllocationCost
        (estimatedCoefficient index) (allocation index)| :=
      Finset.abs_sum_le_sum_abs _ _
    _ = allocationCoefficientDiscrepancy
        trueCoefficient estimatedCoefficient allocation := by
      unfold allocationCoefficientDiscrepancy
      apply Finset.sum_congr rfl
      intro index _
      unfold inverseSqrtAllocationCost
      rw [← sub_div, abs_div,
        abs_of_pos (Real.sqrt_pos.2 (allocationPositive index))]

/-- Simultaneous pointwise coefficient radii upper-bound the allocation
discrepancy. -/
theorem allocationCoefficientDiscrepancy_le_registered_radius_budget
    {Index : Type} [Fintype Index]
    (trueCoefficient estimatedCoefficient coefficientRadius allocation :
      Index → ℝ)
    (allocationPositive : ∀ index, 0 < allocation index)
    (radiusCoverage : ∀ index,
      |trueCoefficient index - estimatedCoefficient index| ≤
        coefficientRadius index) :
    allocationCoefficientDiscrepancy
        trueCoefficient estimatedCoefficient allocation ≤
      registeredAllocationDriftBudget coefficientRadius allocation := by
  unfold allocationCoefficientDiscrepancy registeredAllocationDriftBudget
  apply Finset.sum_le_sum
  intro index _
  exact div_le_div_of_nonneg_right (radiusCoverage index)
    (le_of_lt (Real.sqrt_pos.2 (allocationPositive index)))

/-- On a simultaneous confidence-sequence coverage event, the drift budget is
valid at every registered monitoring look. -/
theorem simultaneous_coefficient_radius_coverage_controls_every_look
    {Index : Type} [Fintype Index]
    (horizon : ℕ)
    (trueCoefficient : Index → ℝ)
    (estimatedCoefficient coefficientRadius : ℕ → Index → ℝ)
    (allocation : ℕ → Index → ℝ)
    (allocationPositive : ∀ look index, 0 < allocation look index)
    (simultaneousCoverage : ∀ look ∈ Finset.range (horizon + 1), ∀ index,
      |trueCoefficient index - estimatedCoefficient look index| ≤
        coefficientRadius look index) :
    ∀ look ∈ Finset.range (horizon + 1),
      |aggregateInverseSqrtAllocationCost trueCoefficient (allocation look) -
          aggregateInverseSqrtAllocationCost
            (estimatedCoefficient look) (allocation look)| ≤
        registeredAllocationDriftBudget
          (coefficientRadius look) (allocation look) := by
  intro look lookMem
  have perturbation :=
    aggregateInverseSqrtAllocationCost_coefficient_perturbation
      trueCoefficient (estimatedCoefficient look) (allocation look)
      (allocationPositive look)
  have discrepancy :=
    allocationCoefficientDiscrepancy_le_registered_radius_budget
      trueCoefficient (estimatedCoefficient look) (coefficientRadius look)
      (allocation look) (allocationPositive look)
      (simultaneousCoverage look lookMem)
  exact perturbation.trans discrepancy

/-- If an allocation is optimal for estimated coefficients, its true regret
is bounded by the coefficient discrepancies at the chosen and oracle
allocations. -/
theorem estimated_optimum_true_regret_le_two_allocation_discrepancies
    {Index : Type} [Fintype Index]
    (trueCoefficient estimatedCoefficient chosen oracle : Index → ℝ)
    (chosenPositive : ∀ index, 0 < chosen index)
    (oraclePositive : ∀ index, 0 < oracle index)
    (estimatedOptimal :
      aggregateInverseSqrtAllocationCost estimatedCoefficient chosen ≤
        aggregateInverseSqrtAllocationCost estimatedCoefficient oracle) :
    aggregateInverseSqrtAllocationCost trueCoefficient chosen -
        aggregateInverseSqrtAllocationCost trueCoefficient oracle ≤
      allocationCoefficientDiscrepancy
          trueCoefficient estimatedCoefficient chosen +
        allocationCoefficientDiscrepancy
          trueCoefficient estimatedCoefficient oracle := by
  have chosenBound :=
    aggregateInverseSqrtAllocationCost_coefficient_perturbation
      trueCoefficient estimatedCoefficient chosen chosenPositive
  have oracleBound :=
    aggregateInverseSqrtAllocationCost_coefficient_perturbation
      trueCoefficient estimatedCoefficient oracle oraclePositive
  have chosenUpper := (abs_le.mp chosenBound).2
  have oracleLower := (abs_le.mp oracleBound).1
  linarith

/-- Uniform discrepancy budget form: an estimated optimum has at most twice
the registered coefficient-drift budget of true regret. -/
theorem estimated_optimum_true_regret_le_twice_drift_budget
    {Index : Type} [Fintype Index]
    (trueCoefficient estimatedCoefficient chosen oracle : Index → ℝ)
    (driftBudget : ℝ)
    (chosenPositive : ∀ index, 0 < chosen index)
    (oraclePositive : ∀ index, 0 < oracle index)
    (estimatedOptimal :
      aggregateInverseSqrtAllocationCost estimatedCoefficient chosen ≤
        aggregateInverseSqrtAllocationCost estimatedCoefficient oracle)
    (chosenDiscrepancy : allocationCoefficientDiscrepancy
      trueCoefficient estimatedCoefficient chosen ≤ driftBudget)
    (oracleDiscrepancy : allocationCoefficientDiscrepancy
      trueCoefficient estimatedCoefficient oracle ≤ driftBudget) :
    aggregateInverseSqrtAllocationCost trueCoefficient chosen -
        aggregateInverseSqrtAllocationCost trueCoefficient oracle ≤
      2 * driftBudget := by
  have regret := estimated_optimum_true_regret_le_two_allocation_discrepancies
    trueCoefficient estimatedCoefficient chosen oracle
    chosenPositive oraclePositive estimatedOptimal
  linarith

/-- A registered estimated gap larger than both coefficient-discrepancy
budgets certifies that the strict allocation ordering survives drift. -/
theorem estimated_gap_exceeding_drift_certifies_true_order
    {Index : Type} [Fintype Index]
    (trueCoefficient estimatedCoefficient preferred competitor : Index → ℝ)
    (preferredPositive : ∀ index, 0 < preferred index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (robustGap :
      aggregateInverseSqrtAllocationCost estimatedCoefficient preferred +
          allocationCoefficientDiscrepancy
            trueCoefficient estimatedCoefficient preferred <
        aggregateInverseSqrtAllocationCost estimatedCoefficient competitor -
          allocationCoefficientDiscrepancy
            trueCoefficient estimatedCoefficient competitor) :
    aggregateInverseSqrtAllocationCost trueCoefficient preferred <
      aggregateInverseSqrtAllocationCost trueCoefficient competitor := by
  have preferredBound :=
    aggregateInverseSqrtAllocationCost_coefficient_perturbation
      trueCoefficient estimatedCoefficient preferred preferredPositive
  have competitorBound :=
    aggregateInverseSqrtAllocationCost_coefficient_perturbation
      trueCoefficient estimatedCoefficient competitor competitorPositive
  have preferredUpper := (abs_le.mp preferredBound).2
  have competitorLower := (abs_le.mp competitorBound).1
  linarith

/-- Radius-only operational form of robust ordering. -/
theorem estimated_gap_exceeding_registered_radii_certifies_true_order
    {Index : Type} [Fintype Index]
    (trueCoefficient estimatedCoefficient coefficientRadius
      preferred competitor : Index → ℝ)
    (preferredPositive : ∀ index, 0 < preferred index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (radiusCoverage : ∀ index,
      |trueCoefficient index - estimatedCoefficient index| ≤
        coefficientRadius index)
    (robustGap :
      aggregateInverseSqrtAllocationCost estimatedCoefficient preferred +
          registeredAllocationDriftBudget coefficientRadius preferred <
        aggregateInverseSqrtAllocationCost estimatedCoefficient competitor -
          registeredAllocationDriftBudget coefficientRadius competitor) :
    aggregateInverseSqrtAllocationCost trueCoefficient preferred <
      aggregateInverseSqrtAllocationCost trueCoefficient competitor := by
  have preferredDiscrepancy :=
    allocationCoefficientDiscrepancy_le_registered_radius_budget
      trueCoefficient estimatedCoefficient coefficientRadius preferred
      preferredPositive radiusCoverage
  have competitorDiscrepancy :=
    allocationCoefficientDiscrepancy_le_registered_radius_budget
      trueCoefficient estimatedCoefficient coefficientRadius competitor
      competitorPositive radiusCoverage
  apply estimated_gap_exceeding_drift_certifies_true_order
    trueCoefficient estimatedCoefficient preferred competitor
    preferredPositive competitorPositive
  linarith

/-- An adversarial positive coefficient profile witnessing unbounded stale-plan
regret between the fixed allocations `(1,4)` and `(4,1)`. -/
def adversarialDriftCoefficientProfile (requestedRegret : ℝ) : Fin 2 → ℝ :=
  ![2 * (|requestedRegret| + 2), 1]

def fourOneSampleAllocation : Fin 2 → ℝ := ![4, 1]

/-- Without a finite coefficient-drift bound, the regret of retaining the old
`(1,4)` allocation instead of `(4,1)` can exceed every requested real budget.
-/
theorem stale_allocation_regret_unbounded_without_coefficient_drift_bound
    (requestedRegret : ℝ) :
    (∀ index, 0 < adversarialDriftCoefficientProfile requestedRegret index) ∧
      requestedRegret <
        aggregateInverseSqrtAllocationCost
            (adversarialDriftCoefficientProfile requestedRegret)
            oneFourSampleAllocation -
          aggregateInverseSqrtAllocationCost
            (adversarialDriftCoefficientProfile requestedRegret)
            fourOneSampleAllocation := by
  have sqrtFour : Real.sqrt (4 : ℝ) = 2 := by
    calc
      Real.sqrt (4 : ℝ) = Real.sqrt ((2 : ℝ) ^ 2) := by norm_num
      _ = 2 := Real.sqrt_sq (by norm_num)
  constructor
  · intro index
    fin_cases index
    · simp [adversarialDriftCoefficientProfile]
      have := abs_nonneg requestedRegret
      linarith
    · norm_num [adversarialDriftCoefficientProfile]
  · simp [aggregateInverseSqrtAllocationCost, Fin.sum_univ_two,
      inverseSqrtAllocationCost, adversarialDriftCoefficientProfile,
      oneFourSampleAllocation, fourOneSampleAllocation, sqrtFour]
    have lower := le_abs_self requestedRegret
    linarith

end OCKIndividuationMSpaceComposition
