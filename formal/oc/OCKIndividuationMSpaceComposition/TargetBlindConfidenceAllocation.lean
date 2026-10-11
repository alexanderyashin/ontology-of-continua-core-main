import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Target-blind allocation of a finite confidence budget

The empirical M3 adapter reports a weighted collection of finite-alphabet
confidence radii.  Equal alpha allocation is valid, but it ignores the source
weights and sample sizes known before target outcomes are opened.

This module separates three claims that must not be conflated:

* any positive allocation below the familywise budget remains valid by the
  union bound;
* proportional allocation is the unique global minimizer of the registered
  weighted negative-log (equivalently squared-radius log-ratio) objective;
* without a registered scalarization, two admissible allocations can be
  preferred by opposite tasks, so no task-free universal optimum exists.

The logarithmic concentration inequality itself is prior art.  The OC result
is the typed adapter from forecast weights and sample sizes to a target-blind
optimization contract and its explicit no-go boundary.
-/

/-- A weighted negative-log objective.  In the Weissman adapter the importance
coefficient contains the forecast mixture weight and inverse sample size. -/
noncomputable def weightedNegativeLogObjective
    {Index : Type} [Fintype Index]
    (importance allocation : Index → ℝ) : ℝ :=
  ∑ index, -importance index * Real.log (allocation index)

/-- Allocate a finite familywise budget proportionally to positive registered
importance coefficients. -/
noncomputable def proportionalConfidenceAllocation
    {Index : Type} [Fintype Index]
    (delta : ℝ) (importance : Index → ℝ) (index : Index) : ℝ :=
  delta * importance index / ∑ j, importance j

/-- Proportional allocation exhausts the registered budget. -/
theorem proportionalConfidenceAllocation_total
    {Index : Type} [Fintype Index]
    (delta : ℝ) (importance : Index → ℝ)
    (totalNonzero : (∑ j, importance j) ≠ 0) :
    (∑ index, proportionalConfidenceAllocation delta importance index) = delta := by
  simp only [proportionalConfidenceAllocation, div_eq_mul_inv]
  rw [← Finset.sum_mul, ← Finset.mul_sum]
  field_simp

/-- Every coordinate of a proportional allocation has the same
importance-to-alpha ratio.  This is the finite KKT stationarity equation. -/
theorem proportionalConfidenceAllocation_common_rate
    {Index : Type} [Fintype Index]
    (delta : ℝ) (importance : Index → ℝ) (index : Index)
    (deltaNonzero : delta ≠ 0)
    (importancePositive : 0 < importance index)
    (totalPositive : 0 < ∑ j, importance j) :
    importance index /
        proportionalConfidenceAllocation delta importance index =
      (∑ j, importance j) / delta := by
  unfold proportionalConfidenceAllocation
  have importanceNonzero : importance index ≠ 0 := ne_of_gt importancePositive
  have totalNonzero : (∑ j, importance j) ≠ 0 := ne_of_gt totalPositive
  field_simp

/-- Supporting-line inequality for `-q log alpha`. -/
theorem negativeLogCost_supporting_line
    (q candidate competitor : ℝ)
    (qNonnegative : 0 ≤ q)
    (candidatePositive : 0 < candidate)
    (competitorPositive : 0 < competitor) :
    -q * Real.log candidate +
        (-(q / candidate)) * (competitor - candidate) ≤
      -q * Real.log competitor := by
  have logBound := Real.log_le_sub_one_of_pos
    (div_pos competitorPositive candidatePositive)
  rw [Real.log_div competitorPositive.ne' candidatePositive.ne'] at logBound
  have scaled := mul_le_mul_of_nonneg_left logBound qNonnegative
  have candidateNonzero : candidate ≠ 0 := ne_of_gt candidatePositive
  have algebra : q * (competitor / candidate - 1) =
      (q / candidate) * (competitor - candidate) := by
    field_simp
  rw [algebra] at scaled
  linarith

/-- The supporting inequality is strict away from the candidate when the
importance coefficient is positive. -/
theorem negativeLogCost_strict_supporting_line
    (q candidate competitor : ℝ)
    (qPositive : 0 < q)
    (candidatePositive : 0 < candidate)
    (competitorPositive : 0 < competitor)
    (different : competitor ≠ candidate) :
    -q * Real.log candidate +
        (-(q / candidate)) * (competitor - candidate) <
      -q * Real.log competitor := by
  have ratioDifferent : competitor / candidate ≠ 1 := by
    intro ratioOne
    have candidateNonzero : candidate ≠ 0 := ne_of_gt candidatePositive
    apply different
    exact (div_eq_one_iff_eq candidateNonzero).mp ratioOne
  have logBound := Real.log_lt_sub_one_of_pos
    (div_pos competitorPositive candidatePositive) ratioDifferent
  rw [Real.log_div competitorPositive.ne' candidatePositive.ne'] at logBound
  have scaled := mul_lt_mul_of_pos_left logBound qPositive
  have candidateNonzero : candidate ≠ 0 := ne_of_gt candidatePositive
  have algebra : q * (competitor / candidate - 1) =
      (q / candidate) * (competitor - candidate) := by
    field_simp
  rw [algebra] at scaled
  linarith

/-- A common supporting slope plus budget feasibility is a complete global
optimality certificate for a separable finite allocation problem. -/
theorem common_supporting_slope_certifies_global_allocation_optimum
    {Index : Type} [Fintype Index]
    (cost : Index → ℝ → ℝ)
    (candidate competitor : Index → ℝ)
    (slope : ℝ)
    (slopeNonpositive : slope ≤ 0)
    (support : ∀ index,
      cost index (candidate index) +
          slope * (competitor index - candidate index) ≤
        cost index (competitor index))
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index) :
    (∑ index, cost index (candidate index)) ≤
      ∑ index, cost index (competitor index) := by
  have supportSum :
      (∑ index, (cost index (candidate index) +
        slope * (competitor index - candidate index))) ≤
      ∑ index, cost index (competitor index) := by
    exact Finset.sum_le_sum fun index _ => support index
  have differenceNonpositive :
      (∑ index, competitor index) - (∑ index, candidate index) ≤ 0 :=
    sub_nonpos.mpr competitorBudget
  have correctionNonnegative :
      0 ≤ slope * ((∑ index, competitor index) -
        (∑ index, candidate index)) :=
    mul_nonneg_of_nonpos_of_nonpos slopeNonpositive differenceNonpositive
  have sumIdentity :
      (∑ index, (cost index (candidate index) +
        slope * (competitor index - candidate index))) =
      (∑ index, cost index (candidate index)) +
        slope * ((∑ index, competitor index) -
          (∑ index, candidate index)) := by
    simp only [Finset.sum_add_distrib, ← Finset.mul_sum,
      Finset.sum_sub_distrib]
  rw [sumIdentity] at supportSum
  linarith

/-- One strict supporting inequality makes the certified global optimum
strict. -/
theorem common_supporting_slope_certifies_strict_allocation_optimum
    {Index : Type} [Fintype Index]
    (cost : Index → ℝ → ℝ)
    (candidate competitor : Index → ℝ)
    (slope : ℝ)
    (slopeNonpositive : slope ≤ 0)
    (support : ∀ index,
      cost index (candidate index) +
          slope * (competitor index - candidate index) ≤
        cost index (competitor index))
    (strictAt : ∃ index,
      cost index (candidate index) +
          slope * (competitor index - candidate index) <
        cost index (competitor index))
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index) :
    (∑ index, cost index (candidate index)) <
      ∑ index, cost index (competitor index) := by
  have supportSum :
      (∑ index, (cost index (candidate index) +
        slope * (competitor index - candidate index))) <
      ∑ index, cost index (competitor index) := by
    apply Finset.sum_lt_sum
    · intro index _
      exact support index
    · obtain ⟨index, strict⟩ := strictAt
      exact ⟨index, Finset.mem_univ _, strict⟩
  have differenceNonpositive :
      (∑ index, competitor index) - (∑ index, candidate index) ≤ 0 :=
    sub_nonpos.mpr competitorBudget
  have correctionNonnegative :
      0 ≤ slope * ((∑ index, competitor index) -
        (∑ index, candidate index)) :=
    mul_nonneg_of_nonpos_of_nonpos slopeNonpositive differenceNonpositive
  have sumIdentity :
      (∑ index, (cost index (candidate index) +
        slope * (competitor index - candidate index))) =
      (∑ index, cost index (candidate index)) +
        slope * ((∑ index, competitor index) -
          (∑ index, candidate index)) := by
    simp only [Finset.sum_add_distrib, ← Finset.mul_sum,
      Finset.sum_sub_distrib]
  rw [sumIdentity] at supportSum
  linarith

/-- Proportional alpha allocation globally minimizes the registered weighted
negative-log objective among all positive allocations using no more budget. -/
theorem proportional_allocation_minimizes_weighted_negative_log
    {Index : Type} [Fintype Index] [Nonempty Index]
    (delta : ℝ) (importance competitor : Index → ℝ)
    (deltaPositive : 0 < delta)
    (importancePositive : ∀ index, 0 < importance index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (competitorBudget : (∑ index, competitor index) ≤ delta) :
    weightedNegativeLogObjective importance
        (proportionalConfidenceAllocation delta importance) ≤
      weightedNegativeLogObjective importance competitor := by
  have totalPositive : 0 < ∑ index, importance index := by
    exact Finset.sum_pos (fun index _ => importancePositive index)
      Finset.univ_nonempty
  have candidatePositive : ∀ index,
      0 < proportionalConfidenceAllocation delta importance index := by
    intro index
    unfold proportionalConfidenceAllocation
    exact div_pos (mul_pos deltaPositive (importancePositive index)) totalPositive
  have candidateTotal :
      (∑ index, proportionalConfidenceAllocation delta importance index) = delta :=
    proportionalConfidenceAllocation_total delta importance
      (ne_of_gt totalPositive)
  apply common_supporting_slope_certifies_global_allocation_optimum
    (fun index alpha => -importance index * Real.log alpha)
    (proportionalConfidenceAllocation delta importance) competitor
    (-((∑ index, importance index) / delta))
  · exact neg_nonpos.mpr
      (div_nonneg (le_of_lt totalPositive) (le_of_lt deltaPositive))
  · intro index
    have commonRate := proportionalConfidenceAllocation_common_rate
      delta importance index (ne_of_gt deltaPositive)
      (importancePositive index) totalPositive
    have support := negativeLogCost_supporting_line
      (importance index) (proportionalConfidenceAllocation delta importance index)
      (competitor index) (le_of_lt (importancePositive index))
      (candidatePositive index) (competitorPositive index)
    rw [commonRate] at support
    exact support
  · rwa [candidateTotal]

/-- The positive proportional allocation is the unique minimizer: every
different positive feasible allocation has strictly larger objective. -/
theorem proportional_allocation_is_unique_weighted_negative_log_minimizer
    {Index : Type} [Fintype Index] [Nonempty Index]
    (delta : ℝ) (importance competitor : Index → ℝ)
    (deltaPositive : 0 < delta)
    (importancePositive : ∀ index, 0 < importance index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (competitorBudget : (∑ index, competitor index) ≤ delta)
    (different :
      competitor ≠ proportionalConfidenceAllocation delta importance) :
    weightedNegativeLogObjective importance
        (proportionalConfidenceAllocation delta importance) <
      weightedNegativeLogObjective importance competitor := by
  have totalPositive : 0 < ∑ index, importance index := by
    exact Finset.sum_pos (fun index _ => importancePositive index)
      Finset.univ_nonempty
  have candidatePositive : ∀ index,
      0 < proportionalConfidenceAllocation delta importance index := by
    intro index
    unfold proportionalConfidenceAllocation
    exact div_pos (mul_pos deltaPositive (importancePositive index)) totalPositive
  have candidateTotal :
      (∑ index, proportionalConfidenceAllocation delta importance index) = delta :=
    proportionalConfidenceAllocation_total delta importance
      (ne_of_gt totalPositive)
  apply common_supporting_slope_certifies_strict_allocation_optimum
    (fun index alpha => -importance index * Real.log alpha)
    (proportionalConfidenceAllocation delta importance) competitor
    (-((∑ index, importance index) / delta))
  · exact neg_nonpos.mpr
      (div_nonneg (le_of_lt totalPositive) (le_of_lt deltaPositive))
  · intro index
    have commonRate := proportionalConfidenceAllocation_common_rate
      delta importance index (ne_of_gt deltaPositive)
      (importancePositive index) totalPositive
    have support := negativeLogCost_supporting_line
      (importance index) (proportionalConfidenceAllocation delta importance index)
      (competitor index) (le_of_lt (importancePositive index))
      (candidatePositive index) (competitorPositive index)
    rw [commonRate] at support
    exact support
  · obtain ⟨index, indexDifferent⟩ := Function.ne_iff.mp different
    refine ⟨index, ?_⟩
    have commonRate := proportionalConfidenceAllocation_common_rate
      delta importance index (ne_of_gt deltaPositive)
      (importancePositive index) totalPositive
    have support := negativeLogCost_strict_supporting_line
      (importance index) (proportionalConfidenceAllocation delta importance index)
      (competitor index) (importancePositive index)
      (candidatePositive index) (competitorPositive index) indexDifferent
    rw [commonRate] at support
    exact support
  · rwa [candidateTotal]

/-- Log-ratio objective whose factors are the finite-alphabet concentration
constants. -/
noncomputable def weightedLogRatioObjective
    {Index : Type} [Fintype Index]
    (importance categoryFactor allocation : Index → ℝ) : ℝ :=
  ∑ index, importance index *
    Real.log (categoryFactor index / allocation index)

theorem weightedLogRatioObjective_eq_constant_add_negativeLog
    {Index : Type} [Fintype Index]
    (importance categoryFactor allocation : Index → ℝ)
    (factorNonzero : ∀ index, categoryFactor index ≠ 0)
    (allocationNonzero : ∀ index, allocation index ≠ 0) :
    weightedLogRatioObjective importance categoryFactor allocation =
      (∑ index, importance index * Real.log (categoryFactor index)) +
        weightedNegativeLogObjective importance allocation := by
  simp only [weightedLogRatioObjective, weightedNegativeLogObjective,
    Real.log_div (factorNonzero _) (allocationNonzero _)]
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro index _
  ring

/-- Proportional allocation also minimizes the weighted log-ratio objective;
changing finite-alphabet constants adds only an allocation-independent term. -/
theorem proportional_allocation_minimizes_weighted_log_ratio
    {Index : Type} [Fintype Index] [Nonempty Index]
    (delta : ℝ)
    (importance categoryFactor competitor : Index → ℝ)
    (deltaPositive : 0 < delta)
    (importancePositive : ∀ index, 0 < importance index)
    (categoryFactorPositive : ∀ index, 0 < categoryFactor index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (competitorBudget : (∑ index, competitor index) ≤ delta) :
    weightedLogRatioObjective importance categoryFactor
        (proportionalConfidenceAllocation delta importance) ≤
      weightedLogRatioObjective importance categoryFactor competitor := by
  have totalPositive : 0 < ∑ index, importance index := by
    exact Finset.sum_pos (fun index _ => importancePositive index)
      Finset.univ_nonempty
  have candidatePositive : ∀ index,
      0 < proportionalConfidenceAllocation delta importance index := by
    intro index
    unfold proportionalConfidenceAllocation
    exact div_pos (mul_pos deltaPositive (importancePositive index)) totalPositive
  rw [weightedLogRatioObjective_eq_constant_add_negativeLog
      importance categoryFactor
      (proportionalConfidenceAllocation delta importance)
      (fun index => ne_of_gt (categoryFactorPositive index))
      (fun index => ne_of_gt (candidatePositive index)),
    weightedLogRatioObjective_eq_constant_add_negativeLog
      importance categoryFactor competitor
      (fun index => ne_of_gt (categoryFactorPositive index))
      (fun index => ne_of_gt (competitorPositive index))]
  simpa [add_comm] using add_le_add_left
    (proportional_allocation_minimizes_weighted_negative_log
      delta importance competitor deltaPositive importancePositive
      competitorPositive competitorBudget)
    (∑ index, importance index * Real.log (categoryFactor index))

/-- Analytic Weissman-style TV radius before clipping at one. -/
noncomputable def weissmanTVRadius
    (categoryFactor sampleSize alpha : ℝ) : ℝ :=
  Real.sqrt (Real.log (categoryFactor / alpha) / (2 * sampleSize))

/-- Squaring the raw radius recovers the log-ratio term on its declared
nonnegative domain. -/
theorem weissmanTVRadius_sq
    (categoryFactor sampleSize alpha : ℝ)
    (logRatioNonnegative :
      0 ≤ Real.log (categoryFactor / alpha) / (2 * sampleSize)) :
    weissmanTVRadius categoryFactor sampleSize alpha ^ 2 =
      Real.log (categoryFactor / alpha) / (2 * sampleSize) := by
  exact Real.sq_sqrt logRatioNonnegative

/-- Any finite target-blind allocation preserves the familywise guarantee
provided the per-event failures and union bound are supplied. -/
theorem finite_allocation_controls_familywise_failure
    {Index : Type} [Fintype Index]
    (delta : ℝ) (allocation failure : Index → ℝ)
    (familywiseFailure : ℝ)
    (perEvent : ∀ index, failure index ≤ allocation index)
    (unionBound : familywiseFailure ≤ ∑ index, failure index)
    (totalBudget : (∑ index, allocation index) ≤ delta) :
    familywiseFailure ≤ delta := by
  calc
    familywiseFailure ≤ ∑ index, failure index := unionBound
    _ ≤ ∑ index, allocation index :=
      Finset.sum_le_sum fun index _ => perEvent index
    _ ≤ delta := totalBudget

/-- Two-channel countermodel: equal-budget allocations can be preferred in
opposite directions by two task scalarizations.  Hence an allocation cannot
be called universally optimal before the task weights are registered. -/
theorem two_channel_scalarizations_prefer_opposite_allocations
    (delta epsilon : ℝ)
    (epsilonBelowHalf : 2 * epsilon < delta) :
    let left : Fin 2 → ℝ := ![delta - epsilon, epsilon]
    let right : Fin 2 → ℝ := ![epsilon, delta - epsilon]
    (∑ index, left index) = delta ∧
      (∑ index, right index) = delta ∧
      -left 0 < -right 0 ∧
      -right 1 < -left 1 := by
  dsimp
  simp only [Fin.sum_univ_two]
  constructor
  · simp
  constructor
  · simp
  constructor <;> simp <;> linarith

end OCKIndividuationMSpaceComposition
