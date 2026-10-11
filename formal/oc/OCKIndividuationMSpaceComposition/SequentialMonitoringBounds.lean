import OCKIndividuationMSpaceComposition.HierarchicalPoolingObservationBounds
import Mathlib.Analysis.SpecificLimits.Basic

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
## Anytime-valid monitoring by geometric alpha spending

A fixed-time error level cannot be reused at every monitoring look.  This
module registers an explicit summable schedule, proves uniform control of
every finite prefix without any independence premise between looks, and gives
an exact independent two-look countermodel to fixed-alpha reuse.
-/

/-- Look `i` receives `delta / 2 * (1/2)^i`; the infinite schedule spends
exactly `delta`, while every finite prefix spends at most `delta`. -/
noncomputable def geometricAlphaSpending (delta : ℝ) (look : ℕ) : ℝ :=
  delta / 2 * (1 / (2 : ℝ)) ^ look

/-- Registered error mass spent through a finite prefix. -/
noncomputable def cumulativeAlphaSpending (delta : ℝ) (looks : ℕ) : ℝ :=
  ∑ index ∈ Finset.range looks, geometricAlphaSpending delta index

theorem geometricAlphaSpending_nonnegative
    (delta : ℝ) (look : ℕ) (deltaNonnegative : 0 ≤ delta) :
    0 ≤ geometricAlphaSpending delta look := by
  unfold geometricAlphaSpending
  positivity

/-- Every finite prefix of the geometric spending schedule is below the
global error budget. -/
theorem cumulative_geometricAlphaSpending_le
    (delta : ℝ) (looks : ℕ) (deltaNonnegative : 0 ≤ delta) :
    cumulativeAlphaSpending delta looks ≤ delta := by
  have geometricBound := sum_geometric_two_le looks
  unfold cumulativeAlphaSpending geometricAlphaSpending
  rw [← Finset.mul_sum]
  calc
    delta / 2 * ∑ index ∈ Finset.range looks, (1 / (2 : ℝ)) ^ index ≤
        delta / 2 * 2 := by
      exact mul_le_mul_of_nonneg_left geometricBound (by positivity)
    _ = delta := by ring

/-- Positive anytime-valid theorem.  If each predetermined look has a valid
fixed-time failure bound equal to its registered spend and the familywise
event obeys the ordinary union bound, every finite monitoring prefix remains
below the global target.  No independence between looks is assumed. -/
theorem geometric_alpha_spending_controls_any_finite_monitor
    (delta : ℝ) (looks : ℕ)
    (perLookFailure : ℕ → ℝ) (familywiseFailure : ℝ)
    (deltaNonnegative : 0 ≤ delta)
    (perLookBound :
      ∀ index ∈ Finset.range looks,
        perLookFailure index ≤ geometricAlphaSpending delta index)
    (unionBound :
      familywiseFailure ≤ ∑ index ∈ Finset.range looks, perLookFailure index) :
    familywiseFailure ≤ delta := by
  calc
    familywiseFailure ≤
        ∑ index ∈ Finset.range looks, perLookFailure index := unionBound
    _ ≤ ∑ index ∈ Finset.range looks,
        geometricAlphaSpending delta index := by
      exact Finset.sum_le_sum perLookBound
    _ = cumulativeAlphaSpending delta looks := rfl
    _ ≤ delta := cumulative_geometricAlphaSpending_le
      delta looks deltaNonnegative

/-- Exact familywise false-positive probability for two independent looks,
each having false-positive probability `alpha`. -/
noncomputable def independentTwoLookFamilywise (alpha : ℝ) : ℝ :=
  1 - (1 - alpha) ^ 2

/-- The amount by which two independent looks exceed the single-look alpha is
exactly `alpha*(1-alpha)`. -/
theorem independentTwoLookFamilywise_excess_exact (alpha : ℝ) :
    independentTwoLookFamilywise alpha - alpha = alpha * (1 - alpha) := by
  unfold independentTwoLookFamilywise
  ring

/-- Fixed-horizon alpha reuse is invalid even after only two independent
looks: for every nontrivial alpha, actual familywise error is strictly larger
than the reported single-look alpha. -/
theorem two_look_fixed_alpha_reuse_strictly_understates_error
    (alpha : ℝ) (alphaPositive : 0 < alpha) (alphaBelowOne : alpha < 1) :
    alpha < independentTwoLookFamilywise alpha := by
  have productPositive : 0 < alpha * (1 - alpha) :=
    mul_pos alphaPositive (sub_pos.mpr alphaBelowOne)
  rw [← independentTwoLookFamilywise_excess_exact alpha] at productPositive
  linarith

/-- The geometric spend at every finite look is positive when the global
budget is positive, so the schedule supports arbitrarily late registered
looks rather than imposing a hidden terminal horizon. -/
theorem geometricAlphaSpending_positive
    (delta : ℝ) (look : ℕ) (deltaPositive : 0 < delta) :
    0 < geometricAlphaSpending delta look := by
  unfold geometricAlphaSpending
  positivity

/-- End-to-end bridge from anytime alpha spending to the pooled,
dependence-corrected population quota at a particular look. -/
theorem geometric_spending_pooled_threshold_guarantees_look_budget
    (groupCount outcomeClassCount look : ℕ)
    (epsilon delta raw designEffect : ℝ)
    (groupCountPositive : 0 < groupCount)
    (outcomeClassCountPositive : 0 < outcomeClassCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (designEffectPositive : 0 < designEffect)
    (enoughRaw :
      designEffect * populationRequiredEffectiveObservations
          (pooledHypothesisCount groupCount outcomeClassCount)
          epsilon (geometricAlphaSpending delta look) ≤ raw) :
    designEffectPopulationBudget
        (pooledHypothesisCount groupCount outcomeClassCount)
        raw designEffect epsilon ≤ geometricAlphaSpending delta look := by
  exact pooled_designEffect_threshold_guarantees_population_budget
    groupCount outcomeClassCount epsilon
    (geometricAlphaSpending delta look) raw designEffect
    groupCountPositive outcomeClassCountPositive epsilonPositive
    (geometricAlphaSpending_positive delta look deltaPositive)
    designEffectPositive enoughRaw

end OCKIndividuationMSpaceComposition
