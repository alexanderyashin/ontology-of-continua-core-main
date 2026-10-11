import OCKIndividuationMSpaceComposition.UnknownSupportInformationBounds
import Mathlib.Analysis.SpecialFunctions.Pow.Real

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-! ## Likelihood separation adapters -/

/-- Per-observation KL separation for two scalar Gaussian locations with a
common positive variance.  The measure-theoretic channel adapter must certify
that its concrete likelihood reduces to this formula. -/
noncomputable def gaussianLocationKL (separation variance : ℝ) : ℝ :=
  separation ^ 2 / (2 * variance)

/-- Equal-prior Gaussian Chernoff exponent used by the pairwise recovery
adapter. -/
noncomputable def gaussianChernoffExponent (separation variance : ℝ) : ℝ :=
  separation ^ 2 / (8 * variance)

theorem gaussianLocationKL_nonnegative
    (separation variance : ℝ) (variancePositive : 0 < variance) :
    0 ≤ gaussianLocationKL separation variance := by
  exact div_nonneg (sq_nonneg separation)
    (mul_nonneg (by norm_num) variancePositive.le)

theorem gaussianChernoffExponent_nonnegative
    (separation variance : ℝ) (variancePositive : 0 < variance) :
    0 ≤ gaussianChernoffExponent separation variance := by
  exact div_nonneg (sq_nonneg separation)
    (mul_nonneg (by norm_num) variancePositive.le)

/-- Exact constant relation between the two Gaussian adapters. -/
theorem gaussianLocationKL_eq_four_mul_chernoff
    (separation variance : ℝ) :
    gaussianLocationKL separation variance =
      4 * gaussianChernoffExponent separation variance := by
  simp [gaussianLocationKL, gaussianChernoffExponent]
  ring

/-- A nonnegative Bernoulli separation surface.  This is twice squared
Hellinger distance in square-root coordinates and is zero for equal laws. -/
noncomputable def bernoulliHellingerSeparation (first second : ℝ) : ℝ :=
  (Real.sqrt first - Real.sqrt second) ^ 2 +
  (Real.sqrt (1 - first) - Real.sqrt (1 - second)) ^ 2

theorem bernoulliHellingerSeparation_nonnegative (first second : ℝ) :
    0 ≤ bernoulliHellingerSeparation first second := by
  exact add_nonneg (sq_nonneg _) (sq_nonneg _)

theorem bernoulliHellingerSeparation_self (probability : ℝ) :
    bernoulliHellingerSeparation probability probability = 0 := by
  simp [bernoulliHellingerSeparation]

/-- Bhattacharyya exponent for constant-rate Poisson observations over a
nonnegative exposure horizon. -/
noncomputable def poissonBhattacharyyaExponent
    (horizon firstRate secondRate : ℝ) : ℝ :=
  horizon / 2 * (Real.sqrt firstRate - Real.sqrt secondRate) ^ 2

theorem poissonBhattacharyyaExponent_nonnegative
    (horizon firstRate secondRate : ℝ) (horizonNonnegative : 0 ≤ horizon) :
    0 ≤ poissonBhattacharyyaExponent horizon firstRate secondRate := by
  exact mul_nonneg (div_nonneg horizonNonnegative (by norm_num)) (sq_nonneg _)

theorem poissonBhattacharyyaExponent_self
    (horizon rate : ℝ) :
    poissonBhattacharyyaExponent horizon rate rate = 0 := by
  simp [poissonBhattacharyyaExponent]

/-! ## Finite-hypothesis recovery upper bound -/

/-- If total decoder error is covered by the sum of all pairwise wrong-law
errors, and each wrong law has error at most `perWrong`, then the total error is
at most `wrongHypotheses * perWrong`. -/
theorem finiteHypothesis_union_error_bound
    {wrongHypotheses : ℕ}
    (pairError : Fin wrongHypotheses → ℝ)
    (totalError perWrong : ℝ)
    (covered : totalError ≤ ∑ j, pairError j)
    (pairBound : ∀ j, pairError j ≤ perWrong) :
    totalError ≤ (wrongHypotheses : ℝ) * perWrong := by
  calc
    totalError ≤ ∑ j, pairError j := covered
    _ ≤ ∑ _j : Fin wrongHypotheses, perWrong :=
      Finset.sum_le_sum fun j _ => pairBound j
    _ = (wrongHypotheses : ℝ) * perWrong := by simp

/-- Positive recovery theorem under a certified pairwise Chernoff exponent. -/
theorem finiteHypothesis_chernoff_recovery_bound
    {wrongHypotheses observations : ℕ}
    (pairError : Fin wrongHypotheses → ℝ)
    (totalError exponent targetError : ℝ)
    (covered : totalError ≤ ∑ j, pairError j)
    (pairChernoff : ∀ j,
      pairError j ≤ Real.exp (-(observations : ℝ) * exponent))
    (budget :
      (wrongHypotheses : ℝ) * Real.exp (-(observations : ℝ) * exponent) ≤
        targetError) :
    totalError ≤ targetError := by
  exact (finiteHypothesis_union_error_bound pairError totalError
    (Real.exp (-(observations : ℝ) * exponent)) covered pairChernoff).trans budget

/-- A checked lower/upper sandwich records both the Fano impossibility floor
and a decoder-specific sufficient error guarantee at the same sample count. -/
structure RecoverySandwichCertificate (hypotheses observations : ℕ) where
  fanoChannel : FanoChannelCertificate hypotheses observations
  wrongHypotheses : ℕ
  pairError : Fin wrongHypotheses → ℝ
  totalError : ℝ
  exponent : ℝ
  targetError : ℝ
  covered : totalError ≤ ∑ j, pairError j
  pairChernoff : ∀ j,
    pairError j ≤ Real.exp (-(observations : ℝ) * exponent)
  upperBudget :
    (wrongHypotheses : ℝ) * Real.exp (-(observations : ℝ) * exponent) ≤
      targetError

theorem recoverySandwich_lower_bound
    {hypotheses observations : ℕ}
    (certificate : RecoverySandwichCertificate hypotheses observations)
    (positiveCapacity : 0 < certificate.fanoChannel.perObservationCapacity) :
    fanoRequiredInformation hypotheses certificate.fanoChannel.error /
        certificate.fanoChannel.perObservationCapacity ≤ observations :=
  fano_observations_lower_bound certificate.fanoChannel positiveCapacity

theorem recoverySandwich_upper_guarantee
    {hypotheses observations : ℕ}
    (certificate : RecoverySandwichCertificate hypotheses observations) :
    certificate.totalError ≤ certificate.targetError := by
  exact finiteHypothesis_chernoff_recovery_bound
    certificate.pairError certificate.totalError certificate.exponent
    certificate.targetError certificate.covered certificate.pairChernoff
    certificate.upperBudget

/-- Combined theorem: one certificate simultaneously verifies that the chosen
sample count is not below the universal information floor and is sufficient
for the registered decoder/error target. -/
theorem recoverySandwich_verified
    {hypotheses observations : ℕ}
    (certificate : RecoverySandwichCertificate hypotheses observations)
    (positiveCapacity : 0 < certificate.fanoChannel.perObservationCapacity) :
    fanoRequiredInformation hypotheses certificate.fanoChannel.error /
          certificate.fanoChannel.perObservationCapacity ≤ observations ∧
      certificate.totalError ≤ certificate.targetError :=
  ⟨recoverySandwich_lower_bound certificate positiveCapacity,
   recoverySandwich_upper_guarantee certificate⟩

end OCKIndividuationMSpaceComposition
