import OCKIndividuationMSpaceComposition.CertifiedOpticDominanceSampleComplexity
import OCKIndividuationMSpaceComposition.TargetBlindConfidenceAllocation

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Target-blind allocation for inverse-square-root risk widths

Separable convex resource allocation and its KKT certificates are mature
prior art.  This module supplies the OC adapter for registered forecast-width
coefficients.  It proves the supporting inequality inside Lean, reuses the
generic finite allocation theorem, and records the task-dependence no-go that
prevents a coefficient-blind allocation from being called universally
optimal.
-/

/-- Per-optic contribution to an inverse-square-root forecast width. -/
noncomputable def inverseSqrtAllocationCost
    (coefficient observations : ℝ) : ℝ :=
  coefficient / Real.sqrt observations

/-- Algebraic supporting-line inequality for the unit inverse-square-root
cost.  This is the convexity fact required by the allocation certificate. -/
theorem inverseSqrtAllocationCost_unit_supporting_line
    (candidate competitor : ℝ)
    (candidatePositive : 0 < candidate)
    (competitorPositive : 0 < competitor) :
    1 / Real.sqrt candidate +
        (-(1 / (2 * candidate * Real.sqrt candidate))) *
          (competitor - candidate) ≤
      1 / Real.sqrt competitor := by
  have sqrtCandidatePositive : 0 < Real.sqrt candidate :=
    Real.sqrt_pos.2 candidatePositive
  have sqrtCompetitorPositive : 0 < Real.sqrt competitor :=
    Real.sqrt_pos.2 competitorPositive
  have candidateSquare : (Real.sqrt candidate) ^ 2 = candidate :=
    Real.sq_sqrt (le_of_lt candidatePositive)
  have competitorSquare : (Real.sqrt competitor) ^ 2 = competitor :=
    Real.sq_sqrt (le_of_lt competitorPositive)
  let x := Real.sqrt candidate
  let y := Real.sqrt competitor
  have xPositive : 0 < x := sqrtCandidatePositive
  have yPositive : 0 < y := sqrtCompetitorPositive
  have factorNonnegative : 0 ≤ (y - x) ^ 2 * (y + 2 * x) := by
    positivity
  have polynomialBound : 3 * x ^ 2 * y - y ^ 3 ≤ 2 * x ^ 3 := by
    nlinarith [factorNonnegative]
  change 1 / x + (-(1 / (2 * candidate * x))) *
      (competitor - candidate) ≤ 1 / y
  rw [← candidateSquare, ← competitorSquare]
  change 1 / x + (-(1 / (2 * x ^ 2 * x))) *
      (y ^ 2 - x ^ 2) ≤ 1 / y
  field_simp
  nlinarith

/-- Strict supporting inequality away from the candidate. -/
theorem inverseSqrtAllocationCost_unit_strict_supporting_line
    (candidate competitor : ℝ)
    (candidatePositive : 0 < candidate)
    (competitorPositive : 0 < competitor)
    (different : competitor ≠ candidate) :
    1 / Real.sqrt candidate +
        (-(1 / (2 * candidate * Real.sqrt candidate))) *
          (competitor - candidate) <
      1 / Real.sqrt competitor := by
  have sqrtCandidatePositive : 0 < Real.sqrt candidate :=
    Real.sqrt_pos.2 candidatePositive
  have sqrtCompetitorPositive : 0 < Real.sqrt competitor :=
    Real.sqrt_pos.2 competitorPositive
  have candidateSquare : (Real.sqrt candidate) ^ 2 = candidate :=
    Real.sq_sqrt (le_of_lt candidatePositive)
  have competitorSquare : (Real.sqrt competitor) ^ 2 = competitor :=
    Real.sq_sqrt (le_of_lt competitorPositive)
  let x := Real.sqrt candidate
  let y := Real.sqrt competitor
  have xPositive : 0 < x := sqrtCandidatePositive
  have yPositive : 0 < y := sqrtCompetitorPositive
  have xyDifferent : y ≠ x := by
    intro equal
    apply different
    nlinarith [candidateSquare, competitorSquare]
  have differenceSquarePositive : 0 < (y - x) ^ 2 :=
    sq_pos_of_ne_zero (sub_ne_zero.mpr xyDifferent)
  have factorPositive : 0 < (y - x) ^ 2 * (y + 2 * x) := by
    exact mul_pos differenceSquarePositive (by positivity)
  have polynomialBound : 3 * x ^ 2 * y - y ^ 3 < 2 * x ^ 3 := by
    nlinarith [factorPositive]
  change 1 / x + (-(1 / (2 * candidate * x))) *
      (competitor - candidate) < 1 / y
  rw [← candidateSquare, ← competitorSquare]
  change 1 / x + (-(1 / (2 * x ^ 2 * x))) *
      (y ^ 2 - x ^ 2) < 1 / y
  field_simp
  nlinarith

/-- Supporting-line inequality for a nonnegative registered coefficient. -/
theorem inverseSqrtAllocationCost_supporting_line
    (coefficient candidate competitor : ℝ)
    (coefficientNonnegative : 0 ≤ coefficient)
    (candidatePositive : 0 < candidate)
    (competitorPositive : 0 < competitor) :
    inverseSqrtAllocationCost coefficient candidate +
        (-(coefficient /
          (2 * candidate * Real.sqrt candidate))) *
          (competitor - candidate) ≤
      inverseSqrtAllocationCost coefficient competitor := by
  have unit := inverseSqrtAllocationCost_unit_supporting_line
    candidate competitor candidatePositive competitorPositive
  have scaled := mul_le_mul_of_nonneg_left unit coefficientNonnegative
  unfold inverseSqrtAllocationCost
  calc
    coefficient / Real.sqrt candidate +
          (-(coefficient / (2 * candidate * Real.sqrt candidate))) *
            (competitor - candidate) =
        coefficient *
          (1 / Real.sqrt candidate +
            (-(1 / (2 * candidate * Real.sqrt candidate))) *
              (competitor - candidate)) := by ring
    _ ≤ coefficient * (1 / Real.sqrt competitor) := scaled
    _ = coefficient / Real.sqrt competitor := by ring

/-- Strict supporting inequality when a positive-width coordinate actually
changes allocation. -/
theorem inverseSqrtAllocationCost_strict_supporting_line
    (coefficient candidate competitor : ℝ)
    (coefficientPositive : 0 < coefficient)
    (candidatePositive : 0 < candidate)
    (competitorPositive : 0 < competitor)
    (different : competitor ≠ candidate) :
    inverseSqrtAllocationCost coefficient candidate +
        (-(coefficient /
          (2 * candidate * Real.sqrt candidate))) *
          (competitor - candidate) <
      inverseSqrtAllocationCost coefficient competitor := by
  have unit := inverseSqrtAllocationCost_unit_strict_supporting_line
    candidate competitor candidatePositive competitorPositive different
  have scaled := mul_lt_mul_of_pos_left unit coefficientPositive
  unfold inverseSqrtAllocationCost
  calc
    coefficient / Real.sqrt candidate +
          (-(coefficient / (2 * candidate * Real.sqrt candidate))) *
            (competitor - candidate) =
        coefficient *
          (1 / Real.sqrt candidate +
            (-(1 / (2 * candidate * Real.sqrt candidate))) *
              (competitor - candidate)) := by ring
    _ < coefficient * (1 / Real.sqrt competitor) := scaled
    _ = coefficient / Real.sqrt competitor := by ring

/-- Equal registered marginal rates plus budget feasibility certify a global
minimum of total inverse-square-root width.  A numerical optimizer need only
emit these checkable premises; it is not trusted as an oracle. -/
theorem common_inverseSqrt_marginal_certifies_global_allocation_optimum
    {Index : Type} [Fintype Index] [Nonempty Index]
    (coefficient candidate competitor : Index → ℝ)
    (rate : ℝ)
    (coefficientNonnegative : ∀ index, 0 ≤ coefficient index)
    (candidatePositive : ∀ index, 0 < candidate index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (commonMarginal : ∀ index,
      coefficient index /
          (2 * candidate index * Real.sqrt (candidate index)) = rate)
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index) :
    (∑ index, inverseSqrtAllocationCost
        (coefficient index) (candidate index)) ≤
      ∑ index, inverseSqrtAllocationCost
        (coefficient index) (competitor index) := by
  apply common_supporting_slope_certifies_global_allocation_optimum
    (fun index observations =>
      inverseSqrtAllocationCost (coefficient index) observations)
    candidate competitor (-rate)
  · have rateNonnegative : 0 ≤ rate := by
      let index : Index := Classical.choice (inferInstanceAs (Nonempty Index))
      rw [← commonMarginal index]
      have denominatorNonnegative :
          0 ≤ 2 * candidate index * Real.sqrt (candidate index) := by
        exact mul_nonneg
          (mul_nonneg (by norm_num) (le_of_lt (candidatePositive index)))
          (Real.sqrt_nonneg _)
      exact div_nonneg (coefficientNonnegative index) denominatorNonnegative
    exact neg_nonpos.mpr rateNonnegative
  · intro index
    have support := inverseSqrtAllocationCost_supporting_line
      (coefficient index) (candidate index) (competitor index)
      (coefficientNonnegative index) (candidatePositive index)
      (competitorPositive index)
    rw [commonMarginal index] at support
    exact support
  · exact competitorBudget

/-- With positive coefficients, the common-marginal allocation is the unique
global minimizer over positive allocations with no larger total budget. -/
theorem common_inverseSqrt_marginal_certifies_unique_allocation_optimum
    {Index : Type} [Fintype Index] [Nonempty Index]
    (coefficient candidate competitor : Index → ℝ)
    (rate : ℝ)
    (coefficientPositive : ∀ index, 0 < coefficient index)
    (candidatePositive : ∀ index, 0 < candidate index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (commonMarginal : ∀ index,
      coefficient index /
          (2 * candidate index * Real.sqrt (candidate index)) = rate)
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index)
    (different : competitor ≠ candidate) :
    (∑ index, inverseSqrtAllocationCost
        (coefficient index) (candidate index)) <
      ∑ index, inverseSqrtAllocationCost
        (coefficient index) (competitor index) := by
  apply common_supporting_slope_certifies_strict_allocation_optimum
    (fun index observations =>
      inverseSqrtAllocationCost (coefficient index) observations)
    candidate competitor (-rate)
  · have rateNonnegative : 0 ≤ rate := by
      let index : Index := Classical.choice (inferInstanceAs (Nonempty Index))
      rw [← commonMarginal index]
      have denominatorNonnegative :
          0 ≤ 2 * candidate index * Real.sqrt (candidate index) := by
        exact mul_nonneg
          (mul_nonneg (by norm_num) (le_of_lt (candidatePositive index)))
          (Real.sqrt_nonneg _)
      exact div_nonneg (le_of_lt (coefficientPositive index))
        denominatorNonnegative
    exact neg_nonpos.mpr rateNonnegative
  · intro index
    have support := inverseSqrtAllocationCost_supporting_line
      (coefficient index) (candidate index) (competitor index)
      (le_of_lt (coefficientPositive index)) (candidatePositive index)
      (competitorPositive index)
    rw [commonMarginal index] at support
    exact support
  · have coordinateDifferent : ∃ index, competitor index ≠ candidate index := by
      by_contra none
      push_neg at none
      exact different (funext none)
    obtain ⟨index, indexDifferent⟩ := coordinateDifferent
    refine ⟨index, ?_⟩
    have strict := inverseSqrtAllocationCost_strict_supporting_line
      (coefficient index) (candidate index) (competitor index)
      (coefficientPositive index) (candidatePositive index)
      (competitorPositive index) indexDifferent
    rw [commonMarginal index] at strict
    exact strict
  · exact competitorBudget

/-- The common-marginal equation has a cube-balance form.  For two optics it
is the algebraic, root-free implementation rule behind the familiar
`n_i proportional to a_i^(2/3)` allocation. -/
theorem equal_inverseSqrt_marginals_imply_cube_balance
    (leftCoefficient rightCoefficient leftCount rightCount : ℝ)
    (leftCountPositive : 0 < leftCount)
    (rightCountPositive : 0 < rightCount)
    (equalMarginal :
      leftCoefficient /
          (2 * leftCount * Real.sqrt leftCount) =
        rightCoefficient /
          (2 * rightCount * Real.sqrt rightCount)) :
    leftCoefficient ^ 2 * rightCount ^ 3 =
      rightCoefficient ^ 2 * leftCount ^ 3 := by
  have leftDenominatorNonzero :
      2 * leftCount * Real.sqrt leftCount ≠ 0 := by positivity
  have rightDenominatorNonzero :
      2 * rightCount * Real.sqrt rightCount ≠ 0 := by positivity
  have cross := (div_eq_div_iff leftDenominatorNonzero
    rightDenominatorNonzero).mp equalMarginal
  have squared := congrArg (fun value : ℝ => value ^ 2) cross
  change (leftCoefficient * (2 * rightCount * Real.sqrt rightCount)) ^ 2 =
      (rightCoefficient * (2 * leftCount * Real.sqrt leftCount)) ^ 2 at squared
  have leftSquare : (Real.sqrt leftCount) ^ 2 = leftCount :=
    Real.sq_sqrt (le_of_lt leftCountPositive)
  have rightSquare : (Real.sqrt rightCount) ^ 2 = rightCount :=
    Real.sq_sqrt (le_of_lt rightCountPositive)
  calc
    leftCoefficient ^ 2 * rightCount ^ 3 =
        (leftCoefficient *
          (2 * rightCount * Real.sqrt rightCount)) ^ 2 / 4 := by
      rw [mul_pow, mul_pow, mul_pow, rightSquare]
      ring
    _ = (rightCoefficient *
          (2 * leftCount * Real.sqrt leftCount)) ^ 2 / 4 := by rw [squared]
    _ = rightCoefficient ^ 2 * leftCount ^ 3 := by
      rw [mul_pow, mul_pow, mul_pow, leftSquare]
      ring

/-- For positive coefficients and counts, the root-free cube balance is also
sufficient for equality of inverse-square-root marginals. -/
theorem cube_balance_implies_equal_inverseSqrt_marginals
    (leftCoefficient rightCoefficient leftCount rightCount : ℝ)
    (leftCoefficientPositive : 0 < leftCoefficient)
    (rightCoefficientPositive : 0 < rightCoefficient)
    (leftCountPositive : 0 < leftCount)
    (rightCountPositive : 0 < rightCount)
    (cubeBalance :
      leftCoefficient ^ 2 * rightCount ^ 3 =
        rightCoefficient ^ 2 * leftCount ^ 3) :
    leftCoefficient /
        (2 * leftCount * Real.sqrt leftCount) =
      rightCoefficient /
        (2 * rightCount * Real.sqrt rightCount) := by
  have leftSquare : (Real.sqrt leftCount) ^ 2 = leftCount :=
    Real.sq_sqrt (le_of_lt leftCountPositive)
  have rightSquare : (Real.sqrt rightCount) ^ 2 = rightCount :=
    Real.sq_sqrt (le_of_lt rightCountPositive)
  have positiveLeftCross :
      0 < leftCoefficient * (rightCount * Real.sqrt rightCount) := by
    positivity
  have positiveRightCross :
      0 < rightCoefficient * (leftCount * Real.sqrt leftCount) := by
    positivity
  have crossSquares :
      (leftCoefficient * (rightCount * Real.sqrt rightCount)) ^ 2 =
        (rightCoefficient * (leftCount * Real.sqrt leftCount)) ^ 2 := by
    calc
      (leftCoefficient * (rightCount * Real.sqrt rightCount)) ^ 2 =
          leftCoefficient ^ 2 * rightCount ^ 3 := by
        rw [mul_pow, mul_pow, rightSquare]
        ring
      _ = rightCoefficient ^ 2 * leftCount ^ 3 := cubeBalance
      _ = (rightCoefficient * (leftCount * Real.sqrt leftCount)) ^ 2 := by
        rw [mul_pow, mul_pow, leftSquare]
        ring
  have crossEqual :
      leftCoefficient * (rightCount * Real.sqrt rightCount) =
        rightCoefficient * (leftCount * Real.sqrt leftCount) := by
    nlinarith
  have leftDenominatorNonzero :
      2 * leftCount * Real.sqrt leftCount ≠ 0 := by positivity
  have rightDenominatorNonzero :
      2 * rightCount * Real.sqrt rightCount ≠ 0 := by positivity
  apply (div_eq_div_iff leftDenominatorNonzero
    rightDenominatorNonzero).2
  nlinarith

/-- A finite numerical allocation can be certified without trusting roots or
an optimizer: positivity, total-budget feasibility and pairwise polynomial
cube balances against one reference coordinate are sufficient. -/
theorem cube_balance_certificate_global_allocation_optimum
    {Index : Type} [Fintype Index] [Nonempty Index]
    (coefficient candidate competitor : Index → ℝ)
    (reference : Index)
    (coefficientPositive : ∀ index, 0 < coefficient index)
    (candidatePositive : ∀ index, 0 < candidate index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (cubeBalance : ∀ index,
      coefficient index ^ 2 * candidate reference ^ 3 =
        coefficient reference ^ 2 * candidate index ^ 3)
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index) :
    (∑ index, inverseSqrtAllocationCost
        (coefficient index) (candidate index)) ≤
      ∑ index, inverseSqrtAllocationCost
        (coefficient index) (competitor index) := by
  apply common_inverseSqrt_marginal_certifies_global_allocation_optimum
    coefficient candidate competitor
    (coefficient reference /
      (2 * candidate reference * Real.sqrt (candidate reference)))
    (fun index => le_of_lt (coefficientPositive index))
    candidatePositive competitorPositive
  · intro index
    exact cube_balance_implies_equal_inverseSqrt_marginals
      (coefficient index) (coefficient reference)
      (candidate index) (candidate reference)
      (coefficientPositive index) (coefficientPositive reference)
      (candidatePositive index) (candidatePositive reference)
      (cubeBalance index)
  · exact competitorBudget

/-- Under positive coefficients, the root-free cube-balance certificate also
proves strict uniqueness against every different positive feasible
allocation. -/
theorem cube_balance_certificate_unique_allocation_optimum
    {Index : Type} [Fintype Index] [Nonempty Index]
    (coefficient candidate competitor : Index → ℝ)
    (reference : Index)
    (coefficientPositive : ∀ index, 0 < coefficient index)
    (candidatePositive : ∀ index, 0 < candidate index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (cubeBalance : ∀ index,
      coefficient index ^ 2 * candidate reference ^ 3 =
        coefficient reference ^ 2 * candidate index ^ 3)
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index)
    (different : competitor ≠ candidate) :
    (∑ index, inverseSqrtAllocationCost
        (coefficient index) (candidate index)) <
      ∑ index, inverseSqrtAllocationCost
        (coefficient index) (competitor index) := by
  apply common_inverseSqrt_marginal_certifies_unique_allocation_optimum
    coefficient candidate competitor
    (coefficient reference /
      (2 * candidate reference * Real.sqrt (candidate reference)))
    coefficientPositive candidatePositive competitorPositive
  · intro index
    exact cube_balance_implies_equal_inverseSqrt_marginals
      (coefficient index) (coefficient reference)
      (candidate index) (candidate reference)
      (coefficientPositive index) (coefficientPositive reference)
      (candidatePositive index) (candidatePositive reference)
      (cubeBalance index)
  · exact competitorBudget
  · exact different

/-- Exact two-optic coefficient profile used as a numerical canary. -/
def oneEightCoefficientProfile : Fin 2 → ℝ := ![1, 8]

/-- Exact five-unit continuous allocation associated with the canary. -/
def oneFourSampleAllocation : Fin 2 → ℝ := ![1, 4]

/-- Concrete quantitative prediction: for width coefficients `(1,8)` and a
five-unit independent-equivalent budget, `(1,4)` is the unique positive
continuous optimum. -/
theorem one_eight_coefficients_five_budget_unique_optimum
    (competitor : Fin 2 → ℝ)
    (competitorPositive : ∀ index, 0 < competitor index)
    (competitorBudget : (∑ index, competitor index) ≤ 5)
    (different : competitor ≠ oneFourSampleAllocation) :
    (∑ index, inverseSqrtAllocationCost
        (oneEightCoefficientProfile index)
        (oneFourSampleAllocation index)) <
      ∑ index, inverseSqrtAllocationCost
        (oneEightCoefficientProfile index) (competitor index) := by
  apply cube_balance_certificate_unique_allocation_optimum
    oneEightCoefficientProfile oneFourSampleAllocation competitor 0
  · intro index
    fin_cases index <;> norm_num [oneEightCoefficientProfile]
  · intro index
    fin_cases index <;> norm_num [oneFourSampleAllocation]
  · exact competitorPositive
  · intro index
    fin_cases index <;>
      norm_num [oneEightCoefficientProfile, oneFourSampleAllocation]
  · convert competitorBudget using 1 <;>
      norm_num [oneFourSampleAllocation, Fin.sum_univ_two]
  · exact different

/-- No coefficient-blind allocation can be universally optimal: the same two
feasible allocations are strictly ordered in opposite directions by two
registered coefficient profiles. -/
theorem inverseSqrt_allocation_preference_reverses_with_task_coefficients :
    inverseSqrtAllocationCost 1 1 + inverseSqrtAllocationCost 4 4 <
        inverseSqrtAllocationCost 1 4 + inverseSqrtAllocationCost 4 1 ∧
      inverseSqrtAllocationCost 4 4 + inverseSqrtAllocationCost 1 1 <
        inverseSqrtAllocationCost 4 1 + inverseSqrtAllocationCost 1 4 := by
  have sqrtFour : Real.sqrt (4 : ℝ) = 2 := by
    calc
      Real.sqrt (4 : ℝ) = Real.sqrt ((2 : ℝ) ^ 2) := by norm_num
      _ = 2 := Real.sqrt_sq (by norm_num)
  norm_num [inverseSqrtAllocationCost, sqrtFour]

end OCKIndividuationMSpaceComposition
