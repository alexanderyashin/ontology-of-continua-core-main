import OCKIndividuationMSpaceComposition.PoissonKLMagnitude
import Mathlib.Probability.Distributions.Gaussian.Real

namespace OCKIndividuationMSpaceComposition

open MeasureTheory ProbabilityTheory InformationTheory Real
open scoped ENNReal NNReal

/-- Two nondegenerate real Gaussian measures with the same variance have the
expected density ratio as their Radon--Nikodym derivative.  The statement is
made with respect to Lebesgue measure, which is equivalent to either Gaussian
measure in this nondegenerate case. -/
theorem gaussianReal_rnDeriv_eq_densityRatio
    (firstMean secondMean : ℝ) (variance : ℝ≥0)
    (varianceNonzero : variance ≠ 0) :
    ∂(gaussianReal firstMean variance)/∂(gaussianReal secondMean variance) =ᵐ[volume]
      fun x ↦ (gaussianPDF secondMean variance x)⁻¹ *
        gaussianPDF firstMean variance x := by
  rw [gaussianReal_of_var_ne_zero secondMean varianceNonzero]
  have rightDensity := Measure.rnDeriv_withDensity_right
    (gaussianReal firstMean variance) volume
    (f := gaussianPDF secondMean variance)
    (measurable_gaussianPDF secondMean variance).aemeasurable
    (ae_of_all volume fun x ↦ (gaussianPDF_pos secondMean varianceNonzero x).ne')
    (ae_of_all volume fun _ ↦ gaussianPDF_ne_top)
  have leftDensity := rnDeriv_gaussianReal firstMean variance
  filter_upwards [rightDensity, leftDensity] with x hxRight hxLeft
  rw [hxRight, hxLeft]

/-- Closed logarithm of the nondegenerate real Gaussian density. -/
theorem log_gaussianPDFReal
    (mean : ℝ) (variance : ℝ≥0) (x : ℝ)
    (varianceNonzero : variance ≠ 0) :
    Real.log (gaussianPDFReal mean variance x) =
      -Real.log (Real.sqrt (2 * Real.pi * (variance : ℝ))) -
        (x - mean) ^ 2 / (2 * (variance : ℝ)) := by
  have variancePositive : 0 < (variance : ℝ) := by
    exact_mod_cast (pos_of_ne_zero varianceNonzero)
  have normalizerPositive :
      0 < Real.sqrt (2 * Real.pi * (variance : ℝ)) := by positivity
  rw [gaussianPDFReal,
    Real.log_mul (inv_ne_zero normalizerPositive.ne') (Real.exp_ne_zero _),
    Real.log_inv, Real.log_exp]
  ring

/-- Pointwise log density ratio for equal-variance Gaussian channels. -/
theorem gaussian_logDensityRatio_formula
    (firstMean secondMean : ℝ) (variance : ℝ≥0) (x : ℝ)
    (varianceNonzero : variance ≠ 0) :
    Real.log ((gaussianPDFReal secondMean variance x)⁻¹ *
      gaussianPDFReal firstMean variance x) =
        ((x - secondMean) ^ 2 - (x - firstMean) ^ 2) /
          (2 * (variance : ℝ)) := by
  have firstPositive := gaussianPDFReal_pos firstMean variance x varianceNonzero
  have secondPositive := gaussianPDFReal_pos secondMean variance x varianceNonzero
  rw [Real.log_mul (inv_ne_zero secondPositive.ne') firstPositive.ne',
    Real.log_inv, log_gaussianPDFReal firstMean variance x varianceNonzero,
    log_gaussianPDFReal secondMean variance x varianceNonzero]
  ring

/-- The equal-variance Gaussian log density ratio is affine in the observed
coordinate.  This is the operational form used by the optimal likelihood
test. -/
theorem gaussian_logDensityRatio_affine_formula
    (firstMean secondMean : ℝ) (variance : ℝ≥0) (x : ℝ)
    (varianceNonzero : variance ≠ 0) :
    Real.log ((gaussianPDFReal secondMean variance x)⁻¹ *
      gaussianPDFReal firstMean variance x) =
        ((firstMean - secondMean) / (variance : ℝ)) * x +
          (secondMean ^ 2 - firstMean ^ 2) /
            (2 * (variance : ℝ)) := by
  rw [gaussian_logDensityRatio_formula firstMean secondMean variance x varianceNonzero]
  have varianceRealNonzero : (variance : ℝ) ≠ 0 := by
    exact_mod_cast varianceNonzero
  field_simp
  ring

/-- The log-likelihood ratio between two nondegenerate equal-variance
Gaussian measures is almost everywhere the explicit affine score. -/
theorem gaussian_llr_ae_affine_formula
    (firstMean secondMean : ℝ) (variance : ℝ≥0)
    (varianceNonzero : variance ≠ 0) :
    llr (gaussianReal firstMean variance) (gaussianReal secondMean variance) =ᵐ[
        gaussianReal firstMean variance]
      fun x ↦ ((firstMean - secondMean) / (variance : ℝ)) * x +
        (secondMean ^ 2 - firstMean ^ 2) /
          (2 * (variance : ℝ)) := by
  have densityRatio := gaussianReal_rnDeriv_eq_densityRatio
    firstMean secondMean variance varianceNonzero
  have underFirst :=
    (gaussianReal_absolutelyContinuous firstMean varianceNonzero).ae_le densityRatio
  filter_upwards [underFirst] with x hx
  rw [llr, hx, ENNReal.toReal_mul, ENNReal.toReal_inv,
    toReal_gaussianPDF, toReal_gaussianPDF]
  exact gaussian_logDensityRatio_affine_formula
    firstMean secondMean variance x varianceNonzero

/-- The explicit Gaussian likelihood score is integrable, rather than merely
formally writable. -/
theorem gaussian_llr_integrable
    (firstMean secondMean : ℝ) (variance : ℝ≥0)
    (varianceNonzero : variance ≠ 0) :
    Integrable
      (llr (gaussianReal firstMean variance) (gaussianReal secondMean variance))
      (gaussianReal firstMean variance) := by
  rw [integrable_congr
    (gaussian_llr_ae_affine_formula firstMean secondMean variance varianceNonzero)]
  have idIntegrable :
      Integrable (fun x : ℝ ↦ x) (gaussianReal firstMean variance) := by
    exact memLp_one_iff_integrable.mp
      (by simpa using (memLp_id_gaussianReal
        (μ := firstMean) (v := variance) (1 : ℝ≥0)))
  exact (idIntegrable.const_mul
    ((firstMean - secondMean) / (variance : ℝ))).add (integrable_const _)

/-- Exact measure-level KL divergence for the nonzero equal-variance Gaussian
location channel. -/
theorem gaussianReal_toReal_klDiv_exact
    (firstMean secondMean : ℝ) (variance : ℝ≥0)
    (varianceNonzero : variance ≠ 0) :
    (klDiv (gaussianReal firstMean variance)
      (gaussianReal secondMean variance)).toReal =
        (firstMean - secondMean) ^ 2 / (2 * (variance : ℝ)) := by
  have absoluteContinuity :
      gaussianReal firstMean variance ≪ gaussianReal secondMean variance :=
    (gaussianReal_absolutelyContinuous firstMean varianceNonzero).trans
      (gaussianReal_absolutelyContinuous' secondMean varianceNonzero)
  have likelihoodIntegrable :=
    gaussian_llr_integrable firstMean secondMean variance varianceNonzero
  rw [toReal_klDiv absoluteContinuity likelihoodIntegrable]
  rw [integral_congr_ae
    (gaussian_llr_ae_affine_formula firstMean secondMean variance varianceNonzero)]
  have idIntegrable :
      Integrable (fun x : ℝ ↦ x) (gaussianReal firstMean variance) := by
    exact memLp_one_iff_integrable.mp
      (by simpa using (memLp_id_gaussianReal
        (μ := firstMean) (v := variance) (1 : ℝ≥0)))
  rw [integral_add
    (idIntegrable.const_mul ((firstMean - secondMean) / (variance : ℝ)))
    (integrable_const _), integral_const_mul, integral_id_gaussianReal]
  simp only [integral_const, measureReal_def, measure_univ]
  norm_num
  have varianceRealNonzero : (variance : ℝ) ≠ 0 := by
    exact_mod_cast varianceNonzero
  field_simp
  ring

end OCKIndividuationMSpaceComposition
