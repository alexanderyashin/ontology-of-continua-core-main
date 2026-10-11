import OCKIndividuationMSpaceComposition.RealValuedSparseRecovery
import Mathlib.InformationTheory.KullbackLeibler.Basic
import Mathlib.Probability.Distributions.Gaussian.Real
import Mathlib.Probability.Distributions.Poisson
import Mathlib.Probability.ProbabilityMassFunction.Constructions

namespace OCKIndividuationMSpaceComposition

open MeasureTheory ProbabilityTheory InformationTheory
open scoped ENNReal NNReal

/-- Measure-level Gaussian identification: KL vanishes exactly when both mean
and variance parameters agree. -/
theorem gaussianMeasure_klDiv_eq_zero_iff
    (firstMean secondMean : ℝ) (firstVariance secondVariance : ℝ≥0) :
    klDiv (gaussianReal firstMean firstVariance)
        (gaussianReal secondMean secondVariance) = 0 ↔
      firstMean = secondMean ∧ firstVariance = secondVariance := by
  rw [klDiv_eq_zero_iff]
  exact gaussianReal_ext_iff

/-- Two Bernoulli probability measures agree exactly when their parameters do. -/
theorem bernoulliMeasure_eq_iff
    (first second : ℝ≥0) (firstAtMostOne : first ≤ 1)
    (secondAtMostOne : second ≤ 1) :
    (PMF.bernoulli first firstAtMostOne).toMeasure =
        (PMF.bernoulli second secondAtMostOne).toMeasure ↔
      first = second := by
  constructor
  · intro measuresEqual
    have pmfsEqual :
        PMF.bernoulli first firstAtMostOne =
          PMF.bernoulli second secondAtMostOne :=
      PMF.toMeasure_inj.mp measuresEqual
    have atTrue := congrArg (fun distribution : PMF Bool => distribution true) pmfsEqual
    simpa [PMF.bernoulli_apply] using atTrue
  · rintro rfl
    rfl

/-- Measure-level Bernoulli identification by KL. -/
theorem bernoulliMeasure_klDiv_eq_zero_iff
    (first second : ℝ≥0) (firstAtMostOne : first ≤ 1)
    (secondAtMostOne : second ≤ 1) :
    klDiv (PMF.bernoulli first firstAtMostOne).toMeasure
        (PMF.bernoulli second secondAtMostOne).toMeasure = 0 ↔
      first = second := by
  rw [klDiv_eq_zero_iff]
  exact bernoulliMeasure_eq_iff first second firstAtMostOne secondAtMostOne

/-- Two Poisson count measures agree exactly when their rates agree. -/
theorem poissonMeasure_eq_iff (first second : ℝ≥0) :
    poissonMeasure first = poissonMeasure second ↔ first = second := by
  constructor
  · intro measuresEqual
    have pmfsEqual : poissonPMF first = poissonPMF second :=
      PMF.toMeasure_inj.mp measuresEqual
    have atZeroRaw :=
      congrArg (fun distribution : PMF ℕ => distribution 0) pmfsEqual
    change ENNReal.ofReal (poissonPMFReal first 0) =
      ENNReal.ofReal (poissonPMFReal second 0) at atZeroRaw
    have atZero :
        ENNReal.ofReal (Real.exp (-(first : ℝ))) =
          ENNReal.ofReal (Real.exp (-(second : ℝ))) := by
      simpa [poissonPMFReal] using atZeroRaw
    have exponentialsEqual :
        Real.exp (-(first : ℝ)) = Real.exp (-(second : ℝ)) := by
      exact (ENNReal.ofReal_eq_ofReal_iff
        (Real.exp_pos _).le (Real.exp_pos _).le).mp atZero
    have negativesEqual : -(first : ℝ) = -(second : ℝ) :=
      Real.exp_injective exponentialsEqual
    exact NNReal.eq (neg_injective negativesEqual)
  · rintro rfl
    rfl

/-- Measure-level Poisson identification by KL. -/
theorem poissonMeasure_klDiv_eq_zero_iff (first second : ℝ≥0) :
    klDiv (poissonMeasure first) (poissonMeasure second) = 0 ↔
      first = second := by
  rw [klDiv_eq_zero_iff]
  exact poissonMeasure_eq_iff first second

/-- Count channel over an exposure horizon. -/
noncomputable def poissonExposureMeasure
    (horizon rate : ℝ≥0) : Measure ℕ :=
  poissonMeasure (horizon * rate)

instance poissonExposureMeasure_isProbabilityMeasure (horizon rate : ℝ≥0) :
    IsProbabilityMeasure (poissonExposureMeasure horizon rate) := by
  unfold poissonExposureMeasure
  infer_instance

/-- Positive exposure preserves rate identifiability. -/
theorem poissonExposureMeasure_eq_iff
    (horizon firstRate secondRate : ℝ≥0) (horizonPositive : 0 < horizon) :
    poissonExposureMeasure horizon firstRate =
        poissonExposureMeasure horizon secondRate ↔
      firstRate = secondRate := by
  rw [poissonExposureMeasure, poissonExposureMeasure, poissonMeasure_eq_iff]
  constructor
  · exact mul_left_cancel₀ horizonPositive.ne'
  · intro ratesEqual
    rw [ratesEqual]

/-- Measure-level event-history count identification by KL under positive exposure. -/
theorem poissonExposureMeasure_klDiv_eq_zero_iff
    (horizon firstRate secondRate : ℝ≥0) (horizonPositive : 0 < horizon) :
    klDiv (poissonExposureMeasure horizon firstRate)
        (poissonExposureMeasure horizon secondRate) = 0 ↔
      firstRate = secondRate := by
  rw [klDiv_eq_zero_iff]
  exact poissonExposureMeasure_eq_iff horizon firstRate secondRate horizonPositive

/-- No-go: zero exposure collapses every Poisson rate to the same count law. -/
theorem zeroExposure_collapses_poissonRates (firstRate secondRate : ℝ≥0) :
    poissonExposureMeasure 0 firstRate = poissonExposureMeasure 0 secondRate := by
  simp [poissonExposureMeasure]

/-- Consequently KL is zero between every pair of rates at zero exposure. -/
theorem zeroExposure_poisson_klDiv_eq_zero (firstRate secondRate : ℝ≥0) :
    klDiv (poissonExposureMeasure 0 firstRate)
      (poissonExposureMeasure 0 secondRate) = 0 := by
  rw [klDiv_eq_zero_iff]
  exact zeroExposure_collapses_poissonRates firstRate secondRate

end OCKIndividuationMSpaceComposition
