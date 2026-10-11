import OCKIndividuationMSpaceComposition.IndependentInformationScaling
import Mathlib.Probability.ProbabilityMassFunction.Integrals
import Mathlib.MeasureTheory.Measure.Dirac

namespace OCKIndividuationMSpaceComposition

open MeasureTheory InformationTheory
open scoped ENNReal

variable {Outcome : Type*} [MeasurableSpace Outcome]
  [MeasurableSingletonClass Outcome] [Countable Outcome]

/-- The likelihood-ratio with-density representation does not require a
finite alphabet: countability and full support of the reference PMF suffice. -/
theorem countablePMF_toMeasure_eq_withDensity_likelihoodRatio
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

/-- Radon--Nikodym derivative for a countable full-support PMF channel. -/
theorem countablePMF_rnDeriv_eq_likelihoodRatio
    (first second : PMF Outcome)
    (secondFullSupport : ∀ outcome, second outcome ≠ 0) :
    first.toMeasure.rnDeriv second.toMeasure =ᵐ[second.toMeasure]
      pmfLikelihoodRatio first second := by
  rw [countablePMF_toMeasure_eq_withDensity_likelihoodRatio first second
    secondFullSupport]
  exact Measure.rnDeriv_withDensity second.toMeasure
    (measurable_of_countable (pmfLikelihoodRatio first second))

/-- Exact countable-channel KL reduction.  The explicit integrability
hypothesis distinguishes a finite real KL value from the extended-real
infinite-divergence case. -/
theorem countablePMF_toReal_klDiv_eq_tsum_klFun
    (first second : PMF Outcome)
    (secondFullSupport : ∀ outcome, second outcome ≠ 0)
    (integrableFormula : Integrable
      (fun outcome ↦ klFun
        (pmfLikelihoodRatio first second outcome).toReal)
      second.toMeasure) :
    (klDiv first.toMeasure second.toMeasure).toReal =
      ∑' outcome,
        (second outcome).toReal *
          klFun ((pmfLikelihoodRatio first second outcome).toReal) := by
  have absolutelyContinuous : first.toMeasure ≪ second.toMeasure := by
    rw [countablePMF_toMeasure_eq_withDensity_likelihoodRatio first second
      secondFullSupport]
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
      exact (countablePMF_rnDeriv_eq_likelihoodRatio first second
        secondFullSupport).mono
        (fun _ ratioEqual ↦ congrArg (fun ratio ↦ klFun ratio.toReal) ratioEqual)
    _ = ∑' outcome,
        (second outcome).toReal *
          klFun ((pmfLikelihoodRatio first second outcome).toReal) := by
      rw [PMF.integral_eq_tsum second _ integrableFormula]
      simp only [smul_eq_mul]

end OCKIndividuationMSpaceComposition
