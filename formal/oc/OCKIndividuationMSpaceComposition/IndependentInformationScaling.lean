import OCKIndividuationMSpaceComposition.FinitePMFKLReduction

namespace OCKIndividuationMSpaceComposition

open scoped NNReal

/-! ## Closed-form information accumulation and experimental budgets -/

/-- Union-bound error surface for `competitors` alternatives, an effective
number of independent observations, and a positive per-observation exponent. -/
noncomputable def exponentialUnionBudget
    (competitors observations exponent : ℝ) : ℝ :=
  competitors * Real.exp (-observations * exponent)

/-- Real-valued observation threshold obtained by solving the exponential
union budget for a requested error target. -/
noncomputable def requiredRealObservations
    (competitors targetError exponent : ℝ) : ℝ :=
  Real.log (competitors / targetError) / exponent

/-- The closed-form threshold really discharges the exponential budget; the
budget is no longer an assumed field of a recovery certificate. -/
theorem requiredRealObservations_guarantees_budget
    (competitors targetError exponent observations : ℝ)
    (competitorsPositive : 0 < competitors)
    (targetPositive : 0 < targetError)
    (exponentPositive : 0 < exponent)
    (enoughObservations :
      requiredRealObservations competitors targetError exponent ≤ observations) :
    exponentialUnionBudget competitors observations exponent ≤ targetError := by
  have logBound :
      Real.log (competitors / targetError) ≤ observations * exponent := by
    calc
      Real.log (competitors / targetError) =
          (Real.log (competitors / targetError) / exponent) * exponent := by
            field_simp
      _ ≤ observations * exponent :=
        mul_le_mul_of_nonneg_right enoughObservations exponentPositive.le
  have exponentialBound :
      Real.exp (-observations * exponent) ≤
        Real.exp (-Real.log (competitors / targetError)) := by
    apply Real.exp_le_exp.mpr
    linarith
  have ratioPositive : 0 < competitors / targetError :=
    div_pos competitorsPositive targetPositive
  have inverseRatio :
      Real.exp (-Real.log (competitors / targetError)) =
        targetError / competitors := by
    rw [Real.exp_neg, Real.exp_log ratioPositive]
    field_simp
  calc
    exponentialUnionBudget competitors observations exponent =
        competitors * Real.exp (-observations * exponent) := rfl
    _ ≤ competitors * Real.exp (-Real.log (competitors / targetError)) :=
      mul_le_mul_of_nonneg_left exponentialBound competitorsPositive.le
    _ = targetError := by
      rw [inverseRatio]
      field_simp

/-- More observations cannot increase the certified exponential error budget. -/
theorem exponentialUnionBudget_antitone_observations
    (competitors exponent firstObservations secondObservations : ℝ)
    (competitorsNonnegative : 0 ≤ competitors)
    (exponentNonnegative : 0 ≤ exponent)
    (observationOrder : firstObservations ≤ secondObservations) :
    exponentialUnionBudget competitors secondObservations exponent ≤
      exponentialUnionBudget competitors firstObservations exponent := by
  unfold exponentialUnionBudget
  apply mul_le_mul_of_nonneg_left _ competitorsNonnegative
  apply Real.exp_le_exp.mpr
  exact mul_le_mul_of_nonneg_right (neg_le_neg observationOrder) exponentNonnegative

/-- Gaussian equal-variance recovery threshold in fully expanded engineering
coordinates. -/
noncomputable def gaussianRequiredRealObservations
    (competitors targetError separation variance : ℝ) : ℝ :=
  8 * variance * Real.log (competitors / targetError) / separation ^ 2

/-- The expanded Gaussian sample formula is exactly the generic information
threshold, not a heuristic approximation. -/
theorem gaussian_requiredRealObservations_exact
    (competitors targetError separation variance : ℝ)
    (separationNonzero : separation ≠ 0)
    (variancePositive : 0 < variance) :
    requiredRealObservations competitors targetError
        (gaussianChernoffExponent separation variance) =
      gaussianRequiredRealObservations competitors targetError separation variance := by
  unfold requiredRealObservations gaussianChernoffExponent
    gaussianRequiredRealObservations
  field_simp

/-- Operational Gaussian prediction: any (possibly integer-valued) observation
count above the expanded threshold meets the requested finite-hypothesis error
budget. -/
theorem gaussian_observation_threshold_guarantees_budget
    (competitors targetError separation variance observations : ℝ)
    (competitorsPositive : 0 < competitors)
    (targetPositive : 0 < targetError)
    (separationNonzero : separation ≠ 0)
    (variancePositive : 0 < variance)
    (enoughObservations :
      gaussianRequiredRealObservations competitors targetError separation variance ≤
        observations) :
    exponentialUnionBudget competitors observations
        (gaussianChernoffExponent separation variance) ≤ targetError := by
  have exponentPositive :
      0 < gaussianChernoffExponent separation variance := by
    unfold gaussianChernoffExponent
    exact div_pos (sq_pos_of_ne_zero separationNonzero)
      (mul_pos (by norm_num) variancePositive)
  apply requiredRealObservations_guarantees_budget competitors targetError
    (gaussianChernoffExponent separation variance) observations
    competitorsPositive targetPositive exponentPositive
  rw [gaussian_requiredRealObservations_exact competitors targetError separation variance
    separationNonzero variancePositive]
  exact enoughObservations

/-- Information exponent accumulated by independent Poisson exposure is
exactly linear in total exposure. -/
theorem poissonBhattacharyyaExponent_exposure_scaling
    (horizon : ℝ) (firstRate secondRate : ℝ≥0) :
    poissonBhattacharyyaExponent horizon firstRate secondRate =
      horizon * poissonBhattacharyyaExponent 1 firstRate secondRate := by
  unfold poissonBhattacharyyaExponent
  ring

/-- Exposure required to reach a target error at the registered Poisson
Bhattacharyya information rate. -/
noncomputable def poissonRequiredExposure
    (competitors targetError : ℝ) (firstRate secondRate : ℝ≥0) : ℝ :=
  requiredRealObservations competitors targetError
    (poissonBhattacharyyaExponent 1 firstRate secondRate)

/-- Operational Poisson prediction: distinct rates and sufficient total
exposure imply the requested exponential error budget. -/
theorem poisson_exposure_threshold_guarantees_budget
    (competitors targetError horizon : ℝ) (firstRate secondRate : ℝ≥0)
    (competitorsPositive : 0 < competitors)
    (targetPositive : 0 < targetError)
    (ratesDistinct : firstRate ≠ secondRate)
    (enoughExposure :
      poissonRequiredExposure competitors targetError firstRate secondRate ≤ horizon) :
    competitors * Real.exp
        (-poissonBhattacharyyaExponent horizon firstRate secondRate) ≤ targetError := by
  have unitHorizonPositive : (0 : ℝ≥0) < 1 := by norm_num
  have exponentNonnegative :
      0 ≤ poissonBhattacharyyaExponent 1 firstRate secondRate :=
    poissonBhattacharyyaExponent_nonnegative 1 firstRate secondRate (by norm_num)
  have exponentNonzero :
      poissonBhattacharyyaExponent 1 firstRate secondRate ≠ 0 :=
    (poissonBhattacharyyaExponent_eq_zero_iff 1 firstRate secondRate
      unitHorizonPositive).not.mpr ratesDistinct
  have exponentPositive :
      0 < poissonBhattacharyyaExponent 1 firstRate secondRate :=
    lt_of_le_of_ne exponentNonnegative (Ne.symm exponentNonzero)
  have budget := requiredRealObservations_guarantees_budget competitors targetError
    (poissonBhattacharyyaExponent 1 firstRate secondRate) horizon
    competitorsPositive targetPositive exponentPositive enoughExposure
  rw [poissonBhattacharyyaExponent_exposure_scaling]
  simpa [exponentialUnionBudget] using budget

end OCKIndividuationMSpaceComposition
