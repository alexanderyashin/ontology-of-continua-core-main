import OCKIndividuationMSpaceComposition.BoundedInverseSqrtSampleAllocation
import Mathlib.Algebra.Order.Floor.Semifield

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Integer execution of continuous sample allocations

The inverse-square-root allocation modules optimize real-valued effective
counts.  Experiments execute integer counts.  This module supplies two
verified adapters:

* floor rounding preserves the original budget and exposes its exact risk gap;
* ceiling rounding never worsens risk and needs less than one additional raw
  observation per coordinate.

The choice between them is an explicit budget/risk decision, not hidden
rounding inside an optimizer.
-/

noncomputable def floorSampleAllocation
    {Index : Type} (plan : Index → ℝ) (index : Index) : ℕ :=
  Nat.floor (plan index)

noncomputable def ceilingSampleAllocation
    {Index : Type} (plan : Index → ℝ) (index : Index) : ℕ :=
  Nat.ceil (plan index)

/-- Inverse-square-root width is antitone in every positive observation
count. -/
theorem inverseSqrtAllocationCost_antitone
    (coefficient smaller larger : ℝ)
    (coefficientNonnegative : 0 ≤ coefficient)
    (smallerPositive : 0 < smaller)
    (ordered : smaller ≤ larger) :
    inverseSqrtAllocationCost coefficient larger ≤
      inverseSqrtAllocationCost coefficient smaller := by
  have largerPositive : 0 < larger := smallerPositive.trans_le ordered
  have sqrtSmallerPositive : 0 < Real.sqrt smaller :=
    Real.sqrt_pos.2 smallerPositive
  have sqrtLargerPositive : 0 < Real.sqrt larger :=
    Real.sqrt_pos.2 largerPositive
  unfold inverseSqrtAllocationCost
  rw [div_le_div_iff₀ sqrtLargerPositive sqrtSmallerPositive]
  exact mul_le_mul_of_nonneg_left (Real.sqrt_le_sqrt ordered)
    coefficientNonnegative

theorem floorSampleAllocation_positive
    {Index : Type} (plan : Index → ℝ)
    (planAtLeastOne : ∀ index, 1 ≤ plan index) (index : Index) :
    0 < floorSampleAllocation plan index := by
  unfold floorSampleAllocation
  exact (Nat.floor_pos).2 (planAtLeastOne index)

theorem floorSampleAllocation_cast_le
    {Index : Type} (plan : Index → ℝ)
    (planNonnegative : ∀ index, 0 ≤ plan index) (index : Index) :
    (floorSampleAllocation plan index : ℝ) ≤ plan index := by
  exact Nat.floor_le (planNonnegative index)

/-- Floor rounding never exceeds the continuous total budget. -/
theorem floorSampleAllocation_preserves_budget
    {Index : Type} [Fintype Index]
    (plan : Index → ℝ)
    (planNonnegative : ∀ index, 0 ≤ plan index) :
    (∑ index, (floorSampleAllocation plan index : ℝ)) ≤
      ∑ index, plan index := by
  exact Finset.sum_le_sum fun index _ =>
    floorSampleAllocation_cast_le plan planNonnegative index

/-- Exact aggregate width increase caused by flooring. -/
noncomputable def floorAllocationRoundingGap
    {Index : Type} [Fintype Index]
    (coefficient plan : Index → ℝ) : ℝ :=
  ∑ index,
    (inverseSqrtAllocationCost (coefficient index)
        (floorSampleAllocation plan index : ℝ) -
      inverseSqrtAllocationCost (coefficient index) (plan index))

theorem floorAllocationRoundingGap_nonnegative
    {Index : Type} [Fintype Index]
    (coefficient plan : Index → ℝ)
    (coefficientNonnegative : ∀ index, 0 ≤ coefficient index)
    (planAtLeastOne : ∀ index, 1 ≤ plan index) :
    0 ≤ floorAllocationRoundingGap coefficient plan := by
  apply Finset.sum_nonneg
  intro index _
  have floorPositive : 0 < (floorSampleAllocation plan index : ℝ) := by
    exact_mod_cast floorSampleAllocation_positive plan planAtLeastOne index
  have floorLe : (floorSampleAllocation plan index : ℝ) ≤ plan index :=
    floorSampleAllocation_cast_le plan
      (fun i => (zero_le_one.trans (planAtLeastOne i))) index
  have costOrder := inverseSqrtAllocationCost_antitone
    (coefficient index) (floorSampleAllocation plan index : ℝ)
    (plan index) (coefficientNonnegative index) floorPositive floorLe
  exact sub_nonneg.mpr costOrder

/-- The reported floor-rounding gap is an identity, not an asymptotic error
term. -/
theorem floorAllocationWidth_eq_continuous_add_exactGap
    {Index : Type} [Fintype Index]
    (coefficient plan : Index → ℝ) :
    (∑ index, inverseSqrtAllocationCost (coefficient index)
        (floorSampleAllocation plan index : ℝ)) =
      (∑ index, inverseSqrtAllocationCost
          (coefficient index) (plan index)) +
        floorAllocationRoundingGap coefficient plan := by
  unfold floorAllocationRoundingGap
  rw [Finset.sum_sub_distrib]
  ring

theorem plan_le_ceilingSampleAllocation
    {Index : Type} (plan : Index → ℝ) (index : Index) :
    plan index ≤ (ceilingSampleAllocation plan index : ℝ) := by
  exact Nat.le_ceil (plan index)

/-- Ceiling rounding never worsens any nonnegative inverse-square-root width. -/
theorem ceilingSampleAllocation_cost_le_continuous
    {Index : Type} (coefficient plan : Index → ℝ)
    (coefficientNonnegative : ∀ index, 0 ≤ coefficient index)
    (planPositive : ∀ index, 0 < plan index) (index : Index) :
    inverseSqrtAllocationCost (coefficient index)
        (ceilingSampleAllocation plan index : ℝ) ≤
      inverseSqrtAllocationCost (coefficient index) (plan index) := by
  exact inverseSqrtAllocationCost_antitone (coefficient index)
    (plan index) (ceilingSampleAllocation plan index : ℝ)
    (coefficientNonnegative index) (planPositive index)
    (plan_le_ceilingSampleAllocation plan index)

theorem ceilingSampleAllocation_totalWidth_le_continuous
    {Index : Type} [Fintype Index]
    (coefficient plan : Index → ℝ)
    (coefficientNonnegative : ∀ index, 0 ≤ coefficient index)
    (planPositive : ∀ index, 0 < plan index) :
    (∑ index, inverseSqrtAllocationCost (coefficient index)
        (ceilingSampleAllocation plan index : ℝ)) ≤
      ∑ index, inverseSqrtAllocationCost
        (coefficient index) (plan index) := by
  exact Finset.sum_le_sum fun index _ =>
    ceilingSampleAllocation_cost_le_continuous coefficient plan
      coefficientNonnegative planPositive index

/-- Ceiling rounding consumes at most one additional unit per coordinate in
the weak closed budget bound.  The underlying coordinate inequality is
strict. -/
theorem ceilingSampleAllocation_budget_augmentation
    {Index : Type} [Fintype Index]
    (plan : Index → ℝ)
    (planNonnegative : ∀ index, 0 ≤ plan index) :
    (∑ index, (ceilingSampleAllocation plan index : ℝ)) ≤
      (∑ index, plan index) + Fintype.card Index := by
  calc
    (∑ index, (ceilingSampleAllocation plan index : ℝ)) ≤
        ∑ index, (plan index + 1) := by
      exact Finset.sum_le_sum fun index _ =>
        (Nat.ceil_lt_add_one (planNonnegative index)).le
    _ = (∑ index, plan index) + Fintype.card Index := by
      simp [Finset.sum_add_distrib]

/-- No-go: zero budget augmentation cannot be promised for ceiling rounding.
Even one half of a planned observation rounds to one. -/
theorem ceiling_rounding_can_exceed_original_budget :
    (1 / 2 : ℝ) < (Nat.ceil (1 / 2 : ℝ) : ℝ) := by
  have ceiling : Nat.ceil (1 / 2 : ℝ) = 1 := by
    apply (Nat.ceil_eq_iff (by decide : (1 : ℕ) ≠ 0)).2
    norm_num
  rw [ceiling]
  norm_num

end OCKIndividuationMSpaceComposition
