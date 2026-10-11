import OCKIndividuationMSpaceComposition.DesignCostAdjustedSampleAllocation

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Capacity- and quota-bounded inverse-square-root allocation

This module adapts the supporting-line proof to active lower and upper bounds.
It is a finite KKT verifier: an optimizer emits local slopes, a common shadow
price and a per-coordinate complementarity regime.  Lean proves global, and
for positive width coefficients strict, optimality.
-/

/-- Per-coordinate bounded complementarity relative to a common shadow price.
The competitor is constrained in the direction permitted by the active bound.
-/
def BoundedAllocationComplementarity
    (lower upper candidate competitor localSlope shadowPrice : ℝ) : Prop :=
  (candidate = lower ∧ lower ≤ competitor ∧ shadowPrice ≤ localSlope) ∨
  (lower < candidate ∧ candidate < upper ∧ localSlope = shadowPrice) ∨
  (candidate = upper ∧ competitor ≤ upper ∧ localSlope ≤ shadowPrice)

/-- Every bounded complementarity regime makes the local KKT correction
nonnegative. -/
theorem boundedAllocationComplementarity_correction_nonnegative
    (lower upper candidate competitor localSlope shadowPrice : ℝ)
    (complementarity : BoundedAllocationComplementarity
      lower upper candidate competitor localSlope shadowPrice) :
    0 ≤ (localSlope - shadowPrice) * (competitor - candidate) := by
  rcases complementarity with lowerActive | interior | upperActive
  · rcases lowerActive with ⟨candidateAtLower, competitorAbove, slopeAbove⟩
    rw [candidateAtLower]
    exact mul_nonneg (sub_nonneg.mpr slopeAbove)
      (sub_nonneg.mpr competitorAbove)
  · rcases interior with ⟨_, _, slopeEqual⟩
    rw [slopeEqual]
    simp
  · rcases upperActive with ⟨candidateAtUpper, competitorBelow, slopeBelow⟩
    rw [candidateAtUpper]
    exact mul_nonneg_of_nonpos_of_nonpos
      (sub_nonpos.mpr slopeBelow) (sub_nonpos.mpr competitorBelow)

/-- Generic bounded supporting-slope certificate for a separable finite
allocation problem. -/
theorem bounded_supporting_slopes_certify_global_allocation_optimum
    {Index : Type} [Fintype Index]
    (cost : Index → ℝ → ℝ)
    (candidate competitor localSlope : Index → ℝ)
    (shadowPrice : ℝ)
    (shadowNonpositive : shadowPrice ≤ 0)
    (support : ∀ index,
      cost index (candidate index) +
          localSlope index * (competitor index - candidate index) ≤
        cost index (competitor index))
    (localCorrection : ∀ index,
      0 ≤ (localSlope index - shadowPrice) *
        (competitor index - candidate index))
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index) :
    (∑ index, cost index (candidate index)) ≤
      ∑ index, cost index (competitor index) := by
  have supportSum :
      (∑ index, (cost index (candidate index) +
        localSlope index * (competitor index - candidate index))) ≤
      ∑ index, cost index (competitor index) :=
    Finset.sum_le_sum fun index _ => support index
  have localCorrectionSum :
      0 ≤ ∑ index, (localSlope index - shadowPrice) *
        (competitor index - candidate index) :=
    Finset.sum_nonneg fun index _ => localCorrection index
  have totalDifferenceNonpositive :
      (∑ index, competitor index) - (∑ index, candidate index) ≤ 0 :=
    sub_nonpos.mpr competitorBudget
  have shadowCorrectionNonnegative :
      0 ≤ shadowPrice *
        ((∑ index, competitor index) - (∑ index, candidate index)) :=
    mul_nonneg_of_nonpos_of_nonpos shadowNonpositive
      totalDifferenceNonpositive
  have correctionIdentity :
      (∑ index, localSlope index *
        (competitor index - candidate index)) =
      shadowPrice *
          ((∑ index, competitor index) - (∑ index, candidate index)) +
        ∑ index, (localSlope index - shadowPrice) *
          (competitor index - candidate index) := by
    rw [← Finset.sum_sub_distrib, Finset.mul_sum,
      ← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro index _
    ring
  have supportIdentity :
      (∑ index, (cost index (candidate index) +
        localSlope index * (competitor index - candidate index))) =
      (∑ index, cost index (candidate index)) +
        ∑ index, localSlope index *
          (competitor index - candidate index) := by
    simp [Finset.sum_add_distrib]
  rw [supportIdentity, correctionIdentity] at supportSum
  linarith

/-- A strict supporting inequality on any changed coordinate makes the bounded
global optimum strict. -/
theorem bounded_supporting_slopes_certify_strict_allocation_optimum
    {Index : Type} [Fintype Index]
    (cost : Index → ℝ → ℝ)
    (candidate competitor localSlope : Index → ℝ)
    (shadowPrice : ℝ)
    (shadowNonpositive : shadowPrice ≤ 0)
    (support : ∀ index,
      cost index (candidate index) +
          localSlope index * (competitor index - candidate index) ≤
        cost index (competitor index))
    (strictAt : ∃ index,
      cost index (candidate index) +
          localSlope index * (competitor index - candidate index) <
        cost index (competitor index))
    (localCorrection : ∀ index,
      0 ≤ (localSlope index - shadowPrice) *
        (competitor index - candidate index))
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index) :
    (∑ index, cost index (candidate index)) <
      ∑ index, cost index (competitor index) := by
  have supportSum :
      (∑ index, (cost index (candidate index) +
        localSlope index * (competitor index - candidate index))) <
      ∑ index, cost index (competitor index) := by
    apply Finset.sum_lt_sum
    · intro index _
      exact support index
    · obtain ⟨index, strict⟩ := strictAt
      exact ⟨index, Finset.mem_univ _, strict⟩
  have localCorrectionSum :
      0 ≤ ∑ index, (localSlope index - shadowPrice) *
        (competitor index - candidate index) :=
    Finset.sum_nonneg fun index _ => localCorrection index
  have totalDifferenceNonpositive :
      (∑ index, competitor index) - (∑ index, candidate index) ≤ 0 :=
    sub_nonpos.mpr competitorBudget
  have shadowCorrectionNonnegative :
      0 ≤ shadowPrice *
        ((∑ index, competitor index) - (∑ index, candidate index)) :=
    mul_nonneg_of_nonpos_of_nonpos shadowNonpositive
      totalDifferenceNonpositive
  have correctionIdentity :
      (∑ index, localSlope index *
        (competitor index - candidate index)) =
      shadowPrice *
          ((∑ index, competitor index) - (∑ index, candidate index)) +
        ∑ index, (localSlope index - shadowPrice) *
          (competitor index - candidate index) := by
    rw [← Finset.sum_sub_distrib, Finset.mul_sum,
      ← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro index _
    ring
  have supportIdentity :
      (∑ index, (cost index (candidate index) +
        localSlope index * (competitor index - candidate index))) =
      (∑ index, cost index (candidate index)) +
        ∑ index, localSlope index *
          (competitor index - candidate index) := by
    simp [Finset.sum_add_distrib]
  rw [supportIdentity, correctionIdentity] at supportSum
  linarith

/-- The exact local slope used by the inverse-square-root supporting line. -/
noncomputable def inverseSqrtAllocationLocalSlope
    (coefficient observations : ℝ) : ℝ :=
  -(coefficient / (2 * observations * Real.sqrt observations))

/-- Bounded KKT complementarity plus positive coefficients certifies a strict
and therefore unique optimum against every different positive feasible
competitor. -/
theorem bounded_inverseSqrt_KKT_certifies_unique_optimum
    {Index : Type} [Fintype Index]
    (coefficient lower upper candidate competitor : Index → ℝ)
    (shadowPrice : ℝ)
    (coefficientPositive : ∀ index, 0 < coefficient index)
    (candidatePositive : ∀ index, 0 < candidate index)
    (competitorPositive : ∀ index, 0 < competitor index)
    (shadowNonpositive : shadowPrice ≤ 0)
    (complementarity : ∀ index,
      BoundedAllocationComplementarity
        (lower index) (upper index) (candidate index) (competitor index)
        (inverseSqrtAllocationLocalSlope
          (coefficient index) (candidate index)) shadowPrice)
    (competitorBudget :
      (∑ index, competitor index) ≤ ∑ index, candidate index)
    (different : competitor ≠ candidate) :
    (∑ index, inverseSqrtAllocationCost
        (coefficient index) (candidate index)) <
      ∑ index, inverseSqrtAllocationCost
        (coefficient index) (competitor index) := by
  apply bounded_supporting_slopes_certify_strict_allocation_optimum
    (fun index observations =>
      inverseSqrtAllocationCost (coefficient index) observations)
    candidate competitor
    (fun index => inverseSqrtAllocationLocalSlope
      (coefficient index) (candidate index)) shadowPrice shadowNonpositive
  · intro index
    exact inverseSqrtAllocationCost_supporting_line
      (coefficient index) (candidate index) (competitor index)
      (le_of_lt (coefficientPositive index)) (candidatePositive index)
      (competitorPositive index)
  · have coordinateDifferent : ∃ index, competitor index ≠ candidate index := by
      by_contra none
      push_neg at none
      exact different (funext none)
    obtain ⟨index, indexDifferent⟩ := coordinateDifferent
    refine ⟨index, ?_⟩
    exact inverseSqrtAllocationCost_strict_supporting_line
      (coefficient index) (candidate index) (competitor index)
      (coefficientPositive index) (candidatePositive index)
      (competitorPositive index) indexDifferent
  · intro index
    exact boundedAllocationComplementarity_correction_nonnegative
      (lower index) (upper index) (candidate index) (competitor index)
      (inverseSqrtAllocationLocalSlope
        (coefficient index) (candidate index)) shadowPrice
      (complementarity index)
  · exact competitorBudget

/-- If a candidate is strictly inside its bounds, complementarity forces its
local marginal slope to equal the common shadow price. -/
theorem interior_bounded_coordinate_has_common_shadow_price
    (lower upper candidate competitor localSlope shadowPrice : ℝ)
    (lowerStrict : lower < candidate)
    (upperStrict : candidate < upper)
    (complementarity : BoundedAllocationComplementarity
      lower upper candidate competitor localSlope shadowPrice) :
    localSlope = shadowPrice := by
  rcases complementarity with lowerActive | interior | upperActive
  · linarith [lowerActive.1]
  · exact interior.2.2
  · linarith [upperActive.1]

end OCKIndividuationMSpaceComposition
