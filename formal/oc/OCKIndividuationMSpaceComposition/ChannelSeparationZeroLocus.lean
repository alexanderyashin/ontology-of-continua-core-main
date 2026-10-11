import OCKIndividuationMSpaceComposition.ZeroFailureCertification

namespace OCKIndividuationMSpaceComposition

open MeasureTheory ProbabilityTheory InformationTheory
open scoped NNReal

/-! ## Zero-locus compatibility of probability measures and formula adapters -/

theorem gaussianLocationKL_eq_zero_iff
    (separation variance : ℝ) (variancePositive : 0 < variance) :
    gaussianLocationKL separation variance = 0 ↔ separation = 0 := by
  unfold gaussianLocationKL
  rw [div_eq_zero_iff]
  simp [variancePositive.ne']

/-- For a shared positive variance, the Gaussian measure-level KL and the
registered location formula vanish on exactly the same parameter pairs. -/
theorem gaussianMeasure_formula_zero_locus
    (firstMean secondMean : ℝ) (variance : ℝ≥0)
    (variancePositive : 0 < variance) :
    klDiv (gaussianReal firstMean variance) (gaussianReal secondMean variance) = 0 ↔
      gaussianLocationKL (firstMean - secondMean) variance = 0 := by
  rw [gaussianMeasure_klDiv_eq_zero_iff,
    gaussianLocationKL_eq_zero_iff _ _ (by exact_mod_cast variancePositive)]
  simp [sub_eq_zero]

/-- The registered Bernoulli Hellinger-coordinate surface vanishes exactly
when its nonnegative probability coordinates agree. -/
theorem bernoulliHellingerSeparation_eq_zero_iff
    (first second : ℝ≥0) :
    bernoulliHellingerSeparation first second = 0 ↔ first = second := by
  constructor
  · intro separationZero
    unfold bernoulliHellingerSeparation at separationZero
    have firstSquareZero :
        (Real.sqrt (first : ℝ) - Real.sqrt (second : ℝ)) ^ 2 = 0 := by
      nlinarith [sq_nonneg
        (Real.sqrt (1 - (first : ℝ)) - Real.sqrt (1 - (second : ℝ)))]
    have squareRootsEqual :
        Real.sqrt (first : ℝ) = Real.sqrt (second : ℝ) := by
      exact sub_eq_zero.mp (sq_eq_zero_iff.mp firstSquareZero)
    exact NNReal.eq ((Real.sqrt_inj first.coe_nonneg second.coe_nonneg).mp
      squareRootsEqual)
  · rintro rfl
    simp [bernoulliHellingerSeparation]

/-- Concrete Bernoulli KL and the registered Hellinger-coordinate surface
have the same zero locus. -/
theorem bernoulliMeasure_formula_zero_locus
    (first second : ℝ≥0) (firstAtMostOne : first ≤ 1)
    (secondAtMostOne : second ≤ 1) :
    klDiv (PMF.bernoulli first firstAtMostOne).toMeasure
        (PMF.bernoulli second secondAtMostOne).toMeasure = 0 ↔
      bernoulliHellingerSeparation first second = 0 := by
  rw [bernoulliMeasure_klDiv_eq_zero_iff,
    bernoulliHellingerSeparation_eq_zero_iff]

/-- Under positive exposure, the registered Poisson Bhattacharyya exponent
vanishes exactly when the two nonnegative event rates agree. -/
theorem poissonBhattacharyyaExponent_eq_zero_iff
    (horizon firstRate secondRate : ℝ≥0) (horizonPositive : 0 < horizon) :
    poissonBhattacharyyaExponent horizon firstRate secondRate = 0 ↔
      firstRate = secondRate := by
  constructor
  · intro exponentZero
    unfold poissonBhattacharyyaExponent at exponentZero
    have factorPositive : 0 < (horizon : ℝ) / 2 := by
      exact div_pos (by exact_mod_cast horizonPositive) (by norm_num)
    have squareZero :
        (Real.sqrt (firstRate : ℝ) - Real.sqrt (secondRate : ℝ)) ^ 2 = 0 :=
      (mul_eq_zero.mp exponentZero).resolve_left factorPositive.ne'
    have squareRootsEqual :
        Real.sqrt (firstRate : ℝ) = Real.sqrt (secondRate : ℝ) := by
      exact sub_eq_zero.mp (sq_eq_zero_iff.mp squareZero)
    exact NNReal.eq ((Real.sqrt_inj firstRate.coe_nonneg secondRate.coe_nonneg).mp
      squareRootsEqual)
  · rintro rfl
    simp [poissonBhattacharyyaExponent]

/-- Positive-exposure Poisson KL and the registered exponent surface have the
same zero locus. -/
theorem poissonExposureMeasure_formula_zero_locus
    (horizon firstRate secondRate : ℝ≥0) (horizonPositive : 0 < horizon) :
    klDiv (poissonExposureMeasure horizon firstRate)
        (poissonExposureMeasure horizon secondRate) = 0 ↔
      poissonBhattacharyyaExponent horizon firstRate secondRate = 0 := by
  rw [poissonExposureMeasure_klDiv_eq_zero_iff _ _ _ horizonPositive,
    poissonBhattacharyyaExponent_eq_zero_iff _ _ _ horizonPositive]

end OCKIndividuationMSpaceComposition
