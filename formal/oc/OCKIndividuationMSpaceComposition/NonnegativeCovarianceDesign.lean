import OCKIndividuationMSpaceComposition.WeightedAdaptiveExperimentalDesign
import Mathlib.Analysis.SpecialFunctions.Pow.Real

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/--
For a covariance kernel with nonnegative entries, a design column whose
entries have absolute value at most one has covariance quadratic form no
larger than the all-ones affine-intercept column.
-/
theorem signedCovarianceInformation_le_intercept
    {trials : ℕ}
    (covariance : Fin trials → Fin trials → ℝ)
    (sign : Fin trials → ℝ)
    (covarianceNonnegative : ∀ i j, 0 ≤ covariance i j)
    (signBound : ∀ i, |sign i| ≤ 1) :
    (∑ i, ∑ j, covariance i j * sign i * sign j) ≤
      ∑ i, ∑ j, covariance i j := by
  apply Finset.sum_le_sum
  intro i _
  apply Finset.sum_le_sum
  intro j _
  have productBound : sign i * sign j ≤ 1 := by
    calc
      sign i * sign j ≤ |sign i * sign j| := le_abs_self _
      _ = |sign i| * |sign j| := abs_mul _ _
      _ ≤ 1 * 1 := mul_le_mul (signBound i) (signBound j) (abs_nonneg _) zero_le_one
      _ = 1 := one_mul 1
  calc
    covariance i j * sign i * sign j =
        covariance i j * (sign i * sign j) := by ring
    _ ≤ covariance i j * 1 :=
      mul_le_mul_of_nonneg_left productBound (covarianceNonnegative i j)
    _ = covariance i j := mul_one _

/-- The intercept dominates every registered family of bounded sign columns. -/
theorem registeredSignedColumns_all_bounded_by_intercept
    {trials columns : ℕ}
    (covariance : Fin trials → Fin trials → ℝ)
    (design : Fin columns → Fin trials → ℝ)
    (covarianceNonnegative : ∀ i j, 0 ≤ covariance i j)
    (designBound : ∀ column i, |design column i| ≤ 1) :
    ∀ column,
      (∑ i, ∑ j, covariance i j * design column i * design column j) ≤
        ∑ i, ∑ j, covariance i j := by
  intro column
  exact signedCovarianceInformation_le_intercept
    covariance (design column) covarianceNonnegative (designBound column)

end OCKIndividuationMSpaceComposition
