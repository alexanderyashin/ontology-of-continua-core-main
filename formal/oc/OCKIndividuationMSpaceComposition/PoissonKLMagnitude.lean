import OCKIndividuationMSpaceComposition.CountablePMFKLReduction

namespace OCKIndividuationMSpaceComposition

open MeasureTheory ProbabilityTheory InformationTheory Real
open scoped ENNReal NNReal Nat

/-- The elementary recursion behind the first moment of a Poisson law. -/
theorem poissonPMFReal_succ_weighted
    (rate : ℝ≥0) (count : ℕ) :
    ((count + 1 : ℕ) : ℝ) * poissonPMFReal rate (count + 1) =
      (rate : ℝ) * poissonPMFReal rate count := by
  simp only [poissonPMFReal, pow_succ, Nat.factorial_succ, Nat.cast_mul,
    Nat.cast_add, Nat.cast_one]
  field_simp

/-- The real Poisson probability weights have first moment equal to the rate. -/
theorem poissonPMFReal_firstMoment_hasSum (rate : ℝ≥0) :
    HasSum (fun count : ℕ ↦ (count : ℝ) * poissonPMFReal rate count)
      (rate : ℝ) := by
  have scaled := (poissonPMFRealSum rate).mul_left (rate : ℝ)
  have shifted : HasSum
      (fun count : ℕ ↦
        ((count + 1 : ℕ) : ℝ) * poissonPMFReal rate (count + 1))
      (rate : ℝ) := by
    simpa using scaled.congr_fun
      (fun count ↦ poissonPMFReal_succ_weighted rate count)
  apply (hasSum_nat_add_iff'
    (g := (rate : ℝ))
    (f := fun count : ℕ ↦ (count : ℝ) * poissonPMFReal rate count) 1).mp
  simpa using shifted

/-- Exact first moment as a convergent real series. -/
theorem poissonPMFReal_firstMoment_tsum (rate : ℝ≥0) :
    ∑' count : ℕ, (count : ℝ) * poissonPMFReal rate count =
      (rate : ℝ) :=
  (poissonPMFReal_firstMoment_hasSum rate).tsum_eq

/-- Coercing a Poisson PMF atom back to the reals recovers its defining
nonnegative real probability. -/
theorem poissonPMF_toReal (rate : ℝ≥0) (count : ℕ) :
    (poissonPMF rate count).toReal = poissonPMFReal rate count := by
  change (ENNReal.ofReal (poissonPMFReal rate count)).toReal = _
  rw [ENNReal.toReal_ofReal poissonPMFReal_nonneg]

/-- Closed logarithm of a positive-rate Poisson atom. -/
theorem log_poissonPMFReal
    (rate : ℝ≥0) (ratePositive : 0 < rate) (count : ℕ) :
    Real.log (poissonPMFReal rate count) =
      -(rate : ℝ) + (count : ℝ) * Real.log (rate : ℝ) -
        Real.log (count.factorial : ℝ) := by
  have rateRealPositive : 0 < (rate : ℝ) := by exact_mod_cast ratePositive
  have factorialPositive : 0 < (count.factorial : ℝ) := by positivity
  rw [poissonPMFReal, Real.log_div
    (mul_ne_zero (Real.exp_ne_zero _) (pow_ne_zero _ rateRealPositive.ne'))
    factorialPositive.ne',
    Real.log_mul (Real.exp_ne_zero _) (pow_ne_zero _ rateRealPositive.ne'),
    Real.log_exp, Real.log_pow]

/-- Definitional atom formula exposed for simplification in measure integrals. -/
theorem poissonPMF_apply_eq_ofReal (rate : ℝ≥0) (count : ℕ) :
    poissonPMF rate count = ENNReal.ofReal (poissonPMFReal rate count) := rfl

/-- The natural-valued count coordinate is integrable under every Poisson
measure, with no unproved moment assumption. -/
theorem poisson_count_integrable (rate : ℝ≥0) :
    Integrable (fun count : ℕ ↦ (count : ℝ)) (poissonMeasure rate) := by
  constructor
  · exact (measurable_of_countable (fun count : ℕ ↦ (count : ℝ))).aestronglyMeasurable
  · rw [hasFiniteIntegral_iff_norm, lintegral_countable']
    have momentSummable : Summable
        (fun count : ℕ ↦ (count : ℝ) * poissonPMFReal rate count) :=
      (poissonPMFReal_firstMoment_hasSum rate).summable
    calc
      (∑' count : ℕ,
          ENNReal.ofReal ‖(count : ℝ)‖ * poissonMeasure rate {count}) =
          ∑' count : ℕ,
            ENNReal.ofReal ((count : ℝ) * poissonPMFReal rate count) := by
              apply tsum_congr
              intro count
              rw [poissonMeasure,
                PMF.toMeasure_apply_singleton (poissonPMF rate) count
                  (MeasurableSet.singleton count)]
              rw [poissonPMF_apply_eq_ofReal]
              simp [ENNReal.ofReal_mul (Nat.cast_nonneg count)]
      _ < ∞ := momentSummable.tsum_ofReal_lt_top

/-- Exact expectation of the count coordinate under the concrete Poisson
measure. -/
theorem poisson_count_integral (rate : ℝ≥0) :
    ∫ count : ℕ, (count : ℝ) ∂(poissonMeasure rate) = (rate : ℝ) := by
  rw [poissonMeasure, PMF.integral_eq_tsum
    (poissonPMF rate) (fun count : ℕ ↦ (count : ℝ))
    (poisson_count_integrable rate)]
  simp only [smul_eq_mul]
  calc
    (∑' count : ℕ, (poissonPMF rate count).toReal * (count : ℝ)) =
        ∑' count : ℕ, (count : ℝ) * poissonPMFReal rate count := by
          apply tsum_congr
          intro count
          rw [poissonPMF_toReal]
          ring
    _ = (rate : ℝ) := poissonPMFReal_firstMoment_tsum rate

/-- Positive Poisson rates give full support on every natural count. -/
theorem poissonPMF_fullSupport
    (rate : ℝ≥0) (ratePositive : 0 < rate) (count : ℕ) :
    poissonPMF rate count ≠ 0 := by
  rw [poissonPMF_apply_eq_ofReal]
  exact ENNReal.ofReal_ne_zero_iff.mpr (poissonPMFReal_pos ratePositive)

/-- Real likelihood ratio of two positive-rate Poisson atoms. -/
theorem poissonLikelihoodRatio_toReal
    (firstRate secondRate : ℝ≥0) (count : ℕ) :
    (pmfLikelihoodRatio (poissonPMF firstRate) (poissonPMF secondRate) count).toReal =
      poissonPMFReal firstRate count / poissonPMFReal secondRate count := by
  unfold pmfLikelihoodRatio
  rw [ENNReal.toReal_div, poissonPMF_toReal, poissonPMF_toReal]

/-- Pointwise Poisson log-likelihood ratio in affine sufficient-statistic
coordinates. -/
theorem poisson_logLikelihoodRatio_formula
    (firstRate secondRate : ℝ≥0)
    (firstPositive : 0 < firstRate) (secondPositive : 0 < secondRate)
    (count : ℕ) :
    Real.log
        (pmfLikelihoodRatio (poissonPMF firstRate) (poissonPMF secondRate) count).toReal =
      -(firstRate : ℝ) + (secondRate : ℝ) +
        (count : ℝ) * Real.log ((firstRate : ℝ) / (secondRate : ℝ)) := by
  rw [poissonLikelihoodRatio_toReal,
    Real.log_div (poissonPMFReal_pos firstPositive).ne'
      (poissonPMFReal_pos secondPositive).ne',
    log_poissonPMFReal firstRate firstPositive,
    log_poissonPMFReal secondRate secondPositive]
  have firstRealPositive : 0 < (firstRate : ℝ) := by exact_mod_cast firstPositive
  have secondRealPositive : 0 < (secondRate : ℝ) := by exact_mod_cast secondPositive
  rw [Real.log_div firstRealPositive.ne' secondRealPositive.ne']
  ring

/-- The concrete Poisson log-likelihood ratio agrees almost everywhere under
the data-generating law with its affine count formula. -/
theorem poisson_llr_ae_formula
    (firstRate secondRate : ℝ≥0)
    (firstPositive : 0 < firstRate) (secondPositive : 0 < secondRate) :
    llr (poissonMeasure firstRate) (poissonMeasure secondRate) =ᵐ[poissonMeasure firstRate]
      fun count : ℕ ↦
        -(firstRate : ℝ) + (secondRate : ℝ) +
          (count : ℝ) * Real.log ((firstRate : ℝ) / (secondRate : ℝ)) := by
  have secondFullSupport : ∀ count, poissonPMF secondRate count ≠ 0 :=
    poissonPMF_fullSupport secondRate secondPositive
  have measureRepresentation :=
    countablePMF_toMeasure_eq_withDensity_likelihoodRatio
      (poissonPMF firstRate) (poissonPMF secondRate) secondFullSupport
  have absolutelyContinuous : poissonMeasure firstRate ≪ poissonMeasure secondRate := by
    rw [poissonMeasure, poissonMeasure, measureRepresentation]
    exact withDensity_absolutelyContinuous _ _
  have derivativeFormula :=
    countablePMF_rnDeriv_eq_likelihoodRatio
      (poissonPMF firstRate) (poissonPMF secondRate) secondFullSupport
  change llr (poissonPMF firstRate).toMeasure (poissonPMF secondRate).toMeasure =ᵐ[
    (poissonPMF firstRate).toMeasure] _
  filter_upwards [absolutelyContinuous.ae_le derivativeFormula] with count ratioEqual
  rw [llr, ratioEqual]
  exact poisson_logLikelihoodRatio_formula firstRate secondRate
    firstPositive secondPositive count

/-- The affine Poisson log-likelihood formula is integrable under its concrete
data-generating law. -/
theorem poisson_logLikelihoodRatio_formula_integrable
    (firstRate secondRate : ℝ≥0) :
    Integrable
      (fun count : ℕ ↦
        -(firstRate : ℝ) + (secondRate : ℝ) +
          (count : ℝ) * Real.log ((firstRate : ℝ) / (secondRate : ℝ)))
      (poissonMeasure firstRate) := by
  have countPart := (poisson_count_integrable firstRate).mul_const
    (Real.log ((firstRate : ℝ) / (secondRate : ℝ)))
  have constantPart : Integrable
      (fun _ : ℕ ↦ -(firstRate : ℝ) + (secondRate : ℝ))
      (poissonMeasure firstRate) := integrable_const _
  exact constantPart.add countPart

/-- Exact nonzero measure-level KL magnitude for two positive-rate Poisson
laws. -/
theorem poissonMeasure_toReal_klDiv_exact
    (firstRate secondRate : ℝ≥0)
    (firstPositive : 0 < firstRate) (secondPositive : 0 < secondRate) :
    (klDiv (poissonMeasure firstRate) (poissonMeasure secondRate)).toReal =
      (firstRate : ℝ) * Real.log ((firstRate : ℝ) / (secondRate : ℝ)) -
        (firstRate : ℝ) + (secondRate : ℝ) := by
  have secondFullSupport : ∀ count, poissonPMF secondRate count ≠ 0 :=
    poissonPMF_fullSupport secondRate secondPositive
  have representation := countablePMF_toMeasure_eq_withDensity_likelihoodRatio
    (poissonPMF firstRate) (poissonPMF secondRate) secondFullSupport
  have absolutelyContinuous : poissonMeasure firstRate ≪ poissonMeasure secondRate := by
    rw [poissonMeasure, poissonMeasure, representation]
    exact withDensity_absolutelyContinuous _ _
  rw [toReal_klDiv_of_measure_eq absolutelyContinuous (by simp)]
  rw [integral_congr_ae
    (poisson_llr_ae_formula firstRate secondRate firstPositive secondPositive)]
  have countIntegrable := poisson_count_integrable firstRate
  have constantIntegrable : Integrable
      (fun _ : ℕ ↦ -(firstRate : ℝ) + (secondRate : ℝ))
      (poissonMeasure firstRate) := integrable_const _
  rw [integral_add constantIntegrable
      (countIntegrable.mul_const
        (Real.log ((firstRate : ℝ) / (secondRate : ℝ)))),
    integral_const, integral_mul_const, poisson_count_integral]
  simp only [probReal_univ, smul_eq_mul, one_mul]
  ring

/-- Exact KL magnitude for a positive-exposure Poisson event channel.  Total
exposure scales information linearly. -/
theorem poissonExposureMeasure_toReal_klDiv_exact
    (horizon firstRate secondRate : ℝ≥0)
    (horizonPositive : 0 < horizon)
    (firstPositive : 0 < firstRate) (secondPositive : 0 < secondRate) :
    (klDiv (poissonExposureMeasure horizon firstRate)
      (poissonExposureMeasure horizon secondRate)).toReal =
        (horizon : ℝ) *
          ((firstRate : ℝ) * Real.log ((firstRate : ℝ) / (secondRate : ℝ)) -
            (firstRate : ℝ) + (secondRate : ℝ)) := by
  rw [poissonExposureMeasure, poissonExposureMeasure,
    poissonMeasure_toReal_klDiv_exact (horizon * firstRate) (horizon * secondRate)
      (mul_pos horizonPositive firstPositive) (mul_pos horizonPositive secondPositive)]
  have horizonRealNonzero : (horizon : ℝ) ≠ 0 := by
    exact_mod_cast horizonPositive.ne'
  have ratioIdentity :
      (((horizon * firstRate : ℝ≥0) : ℝ) /
        ((horizon * secondRate : ℝ≥0) : ℝ)) =
          (firstRate : ℝ) / (secondRate : ℝ) := by
    push_cast
    field_simp
  rw [ratioIdentity]
  push_cast
  ring

end OCKIndividuationMSpaceComposition
