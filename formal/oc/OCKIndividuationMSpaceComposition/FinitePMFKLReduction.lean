import OCKIndividuationMSpaceComposition.ChannelSeparationZeroLocus
import Mathlib.Probability.ProbabilityMassFunction.Integrals
import Mathlib.MeasureTheory.Measure.Dirac

namespace OCKIndividuationMSpaceComposition

open MeasureTheory InformationTheory
open scoped ENNReal NNReal

variable {Outcome : Type*} [MeasurableSpace Outcome]
  [MeasurableSingletonClass Outcome] [Fintype Outcome]

/-- Pointwise likelihood ratio of two probability mass functions. -/
noncomputable def pmfLikelihoodRatio
    (first second : PMF Outcome) (outcome : Outcome) : ℝ≥0∞ :=
  first outcome / second outcome

/-- On a finite full-support channel, the first PMF measure is exactly the
second PMF measure weighted by the pointwise likelihood ratio. -/
theorem pmf_toMeasure_eq_withDensity_likelihoodRatio
    (first second : PMF Outcome)
    (secondFullSupport : ∀ outcome, second outcome ≠ 0) :
    first.toMeasure =
      second.toMeasure.withDensity (pmfLikelihoodRatio first second) := by
  apply Measure.ext_of_singleton
  intro outcome
  rw [first.toMeasure_apply_singleton outcome (MeasurableSet.singleton outcome),
    withDensity_apply _ (MeasurableSet.singleton outcome),
    lintegral_singleton,
    second.toMeasure_apply_singleton outcome (MeasurableSet.singleton outcome)]
  exact (ENNReal.div_mul_cancel (secondFullSupport outcome)
    (second.apply_ne_top outcome)).symm

/-- The Radon--Nikodym derivative of two finite full-support PMF measures is
the pointwise likelihood ratio, almost everywhere under the reference law. -/
theorem pmf_rnDeriv_eq_likelihoodRatio
    (first second : PMF Outcome)
    (secondFullSupport : ∀ outcome, second outcome ≠ 0) :
    first.toMeasure.rnDeriv second.toMeasure =ᵐ[second.toMeasure]
      pmfLikelihoodRatio first second := by
  rw [pmf_toMeasure_eq_withDensity_likelihoodRatio first second secondFullSupport]
  exact Measure.rnDeriv_withDensity second.toMeasure
    (measurable_of_countable (pmfLikelihoodRatio first second))

/-- Exact finite-channel KL reduction.  This is a measure-level theorem: the
Mathlib KL divergence is reduced to a finite sum over the concrete PMF values,
not to an assumed divergence certificate. -/
theorem pmf_toReal_klDiv_eq_sum_klFun
    (first second : PMF Outcome)
    (secondFullSupport : ∀ outcome, second outcome ≠ 0) :
    (klDiv first.toMeasure second.toMeasure).toReal =
      ∑ outcome,
        (second outcome).toReal *
          klFun ((pmfLikelihoodRatio first second outcome).toReal) := by
  have absolutelyContinuous : first.toMeasure ≪ second.toMeasure := by
    rw [pmf_toMeasure_eq_withDensity_likelihoodRatio first second secondFullSupport]
    exact withDensity_absolutelyContinuous _ _
  rw [toReal_klDiv_eq_integral_klFun absolutelyContinuous]
  calc
    (∫ outcome, klFun
        (first.toMeasure.rnDeriv second.toMeasure outcome).toReal
          ∂second.toMeasure) =
        ∫ outcome, klFun
          (pmfLikelihoodRatio first second outcome).toReal
            ∂second.toMeasure := by
      apply integral_congr_ae
      exact (pmf_rnDeriv_eq_likelihoodRatio first second secondFullSupport).mono
        (fun _ ratioEqual => congrArg (fun ratio => klFun ratio.toReal) ratioEqual)
    _ = ∑ outcome,
        (second outcome).toReal *
          klFun ((pmfLikelihoodRatio first second outcome).toReal) := by
      rw [PMF.integral_eq_sum]
      simp only [smul_eq_mul]

/-- Explicit two-atom KL surface in the same `klFun` normalization used by
Mathlib's measure-level KL divergence. -/
noncomputable def bernoulliKLKlFun (first second : ℝ≥0) : ℝ :=
  (second : ℝ) * klFun ((first : ℝ) / (second : ℝ)) +
    (1 - (second : ℝ)) *
      klFun ((1 - (first : ℝ)) / (1 - (second : ℝ)))

/-- Exact Bernoulli magnitude reduction for interior reference probability.
Unlike the earlier zero-locus bridge, this identifies the full real value of
the concrete measure-level KL divergence. -/
theorem bernoulli_toReal_klDiv_eq_klFun_formula
    (first second : ℝ≥0) (firstAtMostOne : first ≤ 1)
    (secondPositive : 0 < second) (secondBelowOne : second < 1) :
    (klDiv (PMF.bernoulli first firstAtMostOne).toMeasure
      (PMF.bernoulli second secondBelowOne.le).toMeasure).toReal =
        bernoulliKLKlFun first second := by
  have firstENNRealLeOne : (first : ℝ≥0∞) ≤ 1 := by
    exact_mod_cast firstAtMostOne
  have secondENNRealLeOne : (second : ℝ≥0∞) ≤ 1 := by
    exact_mod_cast secondBelowOne.le
  rw [pmf_toReal_klDiv_eq_sum_klFun]
  · rw [Fintype.sum_bool]
    simp [bernoulliKLKlFun, pmfLikelihoodRatio, PMF.bernoulli_apply,
      ENNReal.toReal_div,
      ENNReal.toReal_sub_of_le firstENNRealLeOne (by simp),
      ENNReal.toReal_sub_of_le secondENNRealLeOne (by simp)]
  · intro outcome
    cases outcome
    · rw [PMF.bernoulli_apply]
      simp only [Bool.cond_false]
      exact ENNReal.coe_ne_zero.mpr (tsub_pos_iff_lt.mpr secondBelowOne).ne'
    · rw [PMF.bernoulli_apply]
      simp only [Bool.cond_true]
      exact ENNReal.coe_ne_zero.mpr secondPositive.ne'

end OCKIndividuationMSpaceComposition
