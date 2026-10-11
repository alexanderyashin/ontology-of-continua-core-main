import OCKIndividuationMSpaceComposition.DependentInformationBudget
import Mathlib.MeasureTheory.Integral.Prod

namespace OCKIndividuationMSpaceComposition

open MeasureTheory InformationTheory Real
open scoped ENNReal

/-!
## Exact information addition for independent product channels

This module separates a mathematical theorem from an empirical assumption.
If two observation channels are represented by an actual product measure,
their likelihood ratios factor and their finite KL information adds exactly.
Whether two concrete Logion observation blocks satisfy the product-measure
hypothesis is a domain-level proposition that must be tested rather than
inferred from labels such as site, team, or time window.
-/

variable {Alpha Beta : Type*}
  [MeasurableSpace Alpha] [MeasurableSpace Beta]

/-- Radon--Nikodym derivatives factor for an absolutely-continuous product
channel. -/
theorem rnDeriv_prod_eq_mul
    (muA nuA : Measure Alpha) (muB nuB : Measure Beta)
    [SigmaFinite muA] [SigmaFinite nuA]
    [SigmaFinite muB] [SigmaFinite nuB]
    (hA : muA ≪ nuA) (hB : muB ≪ nuB) :
    (muA.prod muB).rnDeriv (nuA.prod nuB) =ᵐ[nuA.prod nuB]
      fun z ↦ muA.rnDeriv nuA z.1 * muB.rnDeriv nuB z.2 := by
  have hRepresentation :
      muA.prod muB = (nuA.prod nuB).withDensity
        (fun z ↦ muA.rnDeriv nuA z.1 * muB.rnDeriv nuB z.2) := by
    have hRepresentationA :
        nuA.withDensity (muA.rnDeriv nuA) = muA :=
      Measure.withDensity_rnDeriv_eq muA nuA hA
    have hRepresentationB :
        nuB.withDensity (muB.rnDeriv nuB) = muB :=
      Measure.withDensity_rnDeriv_eq muB nuB hB
    calc
      muA.prod muB =
          (nuA.withDensity (muA.rnDeriv nuA)).prod
            (nuB.withDensity (muB.rnDeriv nuB)) :=
        congrArg₂ Measure.prod hRepresentationA.symm hRepresentationB.symm
      _ = (nuA.prod nuB).withDensity
          (fun z ↦ muA.rnDeriv nuA z.1 * muB.rnDeriv nuB z.2) :=
        prod_withDensity (μ := nuA) (ν := nuB)
          (Measure.measurable_rnDeriv muA nuA)
          (Measure.measurable_rnDeriv muB nuB)
  rw [hRepresentation]
  exact Measure.rnDeriv_withDensity (nuA.prod nuB) (by fun_prop)

/-- Under the generating product law, the log-likelihood ratio of two
independent channels is the pointwise sum of the channel log-likelihood
ratios. -/
theorem llr_prod_eq_add
    (muA nuA : Measure Alpha) (muB nuB : Measure Beta)
    [SigmaFinite muA] [SigmaFinite nuA]
    [SigmaFinite muB] [SigmaFinite nuB]
    (hA : muA ≪ nuA) (hB : muB ≪ nuB) :
    llr (muA.prod muB) (nuA.prod nuB) =ᵐ[muA.prod muB]
      fun z ↦ llr muA nuA z.1 + llr muB nuB z.2 := by
  have hProd : muA.prod muB ≪ nuA.prod nuB := hA.prod hB
  have hFactorNu := rnDeriv_prod_eq_mul muA nuA muB nuB hA hB
  have hFactorMu := hProd.ae_le hFactorNu
  have hPositive := Measure.rnDeriv_pos hProd
  have hFinite := hProd.ae_le
    (Measure.rnDeriv_lt_top (muA.prod muB) (nuA.prod nuB))
  filter_upwards [hFactorMu, hPositive, hFinite] with z hz hPositive hFinite
  have hProductToRealPositive :
      0 < ((muA.prod muB).rnDeriv (nuA.prod nuB) z).toReal :=
    ENNReal.toReal_pos hPositive.ne' hFinite.ne
  rw [hz, ENNReal.toReal_mul] at hProductToRealPositive
  have hFirstToRealPositive : 0 < (muA.rnDeriv nuA z.1).toReal :=
    pos_of_mul_pos_left hProductToRealPositive ENNReal.toReal_nonneg
  have hSecondToRealPositive : 0 < (muB.rnDeriv nuB z.2).toReal :=
    pos_of_mul_pos_right hProductToRealPositive ENNReal.toReal_nonneg
  simp only [llr_def, hz, ENNReal.toReal_mul]
  exact Real.log_mul hFirstToRealPositive.ne' hSecondToRealPositive.ne'

/-- Finite channel log-likelihoods remain integrable after independent
product composition. -/
theorem llr_prod_integrable
    (muA nuA : Measure Alpha) (muB nuB : Measure Beta)
    [SigmaFinite muA] [SigmaFinite nuA]
    [SigmaFinite muB] [SigmaFinite nuB]
    [IsFiniteMeasure muA] [IsFiniteMeasure muB]
    (hA : muA ≪ nuA) (hB : muB ≪ nuB)
    (hIntegrableA : Integrable (llr muA nuA) muA)
    (hIntegrableB : Integrable (llr muB nuB) muB) :
    Integrable (llr (muA.prod muB) (nuA.prod nuB)) (muA.prod muB) := by
  have hSum : Integrable
      (fun z ↦ llr muA nuA z.1 + llr muB nuB z.2) (muA.prod muB) :=
    (hIntegrableA.comp_fst muB).add (hIntegrableB.comp_snd muA)
  exact hSum.congr (llr_prod_eq_add muA nuA muB nuB hA hB).symm

/-- Exact additivity of finite KL information for two independent
probability channels.  This is the measure-level theorem that licenses
linear information accumulation across genuinely independent blocks. -/
theorem toReal_klDiv_prod_eq_add
    (muA nuA : Measure Alpha) (muB nuB : Measure Beta)
    [SigmaFinite muA] [SigmaFinite nuA]
    [SigmaFinite muB] [SigmaFinite nuB]
    [IsProbabilityMeasure muA] [IsProbabilityMeasure nuA]
    [IsProbabilityMeasure muB] [IsProbabilityMeasure nuB]
    (hA : muA ≪ nuA) (hB : muB ≪ nuB)
    (hIntegrableA : Integrable (llr muA nuA) muA)
    (hIntegrableB : Integrable (llr muB nuB) muB) :
    (klDiv (muA.prod muB) (nuA.prod nuB)).toReal =
      (klDiv muA nuA).toReal + (klDiv muB nuB).toReal := by
  have hProd : muA.prod muB ≪ nuA.prod nuB := hA.prod hB
  have hIntegrableProd :=
    llr_prod_integrable muA nuA muB nuB hA hB hIntegrableA hIntegrableB
  rw [toReal_klDiv hProd hIntegrableProd,
    toReal_klDiv hA hIntegrableA, toReal_klDiv hB hIntegrableB]
  rw [integral_congr_ae (llr_prod_eq_add muA nuA muB nuB hA hB)]
  rw [integral_add (hIntegrableA.comp_fst muB) (hIntegrableB.comp_snd muA)]
  simp only [integral_fun_fst, integral_fun_snd, probReal_univ, one_smul]
  ring

end OCKIndividuationMSpaceComposition
