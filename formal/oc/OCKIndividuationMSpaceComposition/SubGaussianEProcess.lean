import OCKIndividuationMSpaceComposition.EProcessConfidenceSequences
import Mathlib.Probability.Moments.SubGaussian

namespace OCKIndividuationMSpaceComposition

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory ProbabilityTheory

/-!
## Concrete conditionally sub-Gaussian e-process factors

This module begins the constructive bridge from a conditional sub-Gaussian
increment model to an anytime-valid evidence process.  It isolates two reusable
steps: the normalized exponential factor has conditional mean at most one, and
products of nonnegative adapted factors with that property form a
supermartingale.  No numerical mixture claim is used in these proofs.
-/

/-- The normalized fixed-`lambda` factor for one conditionally sub-Gaussian
increment.  The `c * lambda^2 / 2` term is the exact conditional-MGF penalty. -/
noncomputable def subGaussianExponentialFactor
    {Ω : Type*} (X : Ω → ℝ) (c : ℝ≥0) (lambda : ℝ) : Ω → ℝ :=
  Real.exp (-((c : ℝ) * lambda ^ 2 / 2)) •
    fun ω => Real.exp (lambda * X ω)

theorem subGaussianExponentialFactor_nonnegative
    {Ω : Type*} (X : Ω → ℝ) (c : ℝ≥0) (lambda : ℝ) :
    0 ≤ subGaussianExponentialFactor X c lambda := by
  intro ω
  simp only [subGaussianExponentialFactor, Pi.smul_apply, smul_eq_mul]
  positivity

theorem subGaussianExponentialFactor_integrable
    {Ω : Type*} {m mΩ : MeasurableSpace Ω} {μ : Measure Ω}
    [StandardBorelSpace Ω] [IsFiniteMeasure μ]
    (hm : m ≤ mΩ) {X : Ω → ℝ} {c : ℝ≥0}
    (hX : HasCondSubgaussianMGF m hm X c μ) (lambda : ℝ) :
    Integrable (subGaussianExponentialFactor X c lambda) μ := by
  exact (hX.integrable_exp_mul lambda).const_mul _

/-- A conditional sub-Gaussian MGF bound produces an operational e-factor:
its conditional expectation is at most one. -/
theorem condExp_subGaussianExponentialFactor_le_one
    {Ω : Type*} {m mΩ : MeasurableSpace Ω} {μ : Measure Ω}
    [StandardBorelSpace Ω] [IsFiniteMeasure μ]
    (hm : m ≤ mΩ) {X : Ω → ℝ} {c : ℝ≥0}
    (hX : HasCondSubgaussianMGF m hm X c μ) (lambda : ℝ) :
    μ[subGaussianExponentialFactor X c lambda | m] ≤ᵐ[μ] (1 : Ω → ℝ) := by
  change μ[(Real.exp (-((c : ℝ) * lambda ^ 2 / 2))) •
      (fun ω => Real.exp (lambda * X ω)) | m] ≤ᵐ[μ] (1 : Ω → ℝ)
  have hSmul := condExp_smul (μ := μ)
    (Real.exp (-((c : ℝ) * lambda ^ 2 / 2)))
    (fun ω => Real.exp (lambda * X ω)) m
  filter_upwards [hSmul, hX.ae_condExp_le lambda] with ω hSmulω hBound
  rw [hSmulω]
  simp only [Pi.smul_apply, smul_eq_mul, Pi.one_apply]
  calc
    Real.exp (-((c : ℝ) * lambda ^ 2 / 2)) *
        μ[fun ω => Real.exp (lambda * X ω) | m] ω ≤
        Real.exp (-((c : ℝ) * lambda ^ 2 / 2)) *
          Real.exp ((c : ℝ) * lambda ^ 2 / 2) :=
      mul_le_mul_of_nonneg_left hBound (Real.exp_nonneg _)
    _ = 1 := by rw [← Real.exp_add]; ring_nf; exact Real.exp_zero

/-- Multiplicative evidence accumulated before time `n`. -/
def multiplicativeEvidence
    {Ω : Type*} (factor : ℕ → Ω → ℝ) (n : ℕ) (ω : Ω) : ℝ :=
  ∏ i ∈ Finset.range n, factor i ω

theorem multiplicativeEvidence_zero
    {Ω : Type*} (factor : ℕ → Ω → ℝ) :
    multiplicativeEvidence factor 0 = (1 : Ω → ℝ) := by
  funext ω
  simp [multiplicativeEvidence]

theorem multiplicativeEvidence_succ
    {Ω : Type*} (factor : ℕ → Ω → ℝ) (n : ℕ) :
    multiplicativeEvidence factor (n + 1) =
      multiplicativeEvidence factor n * factor n := by
  funext ω
  simp [multiplicativeEvidence, Finset.prod_range_succ]

theorem multiplicativeEvidence_nonnegative
    {Ω : Type*} {factor : ℕ → Ω → ℝ}
    (factorNonnegative : 0 ≤ factor) :
    0 ≤ multiplicativeEvidence factor := by
  intro n ω
  exact Finset.prod_nonneg fun i _ => factorNonnegative i ω

/-- Positive construction theorem for multiplicative e-processes.  Adaptedness
and integrability are stated separately because they are observable model
obligations; the conditional e-factor inequality supplies the stochastic
dynamics. -/
theorem multiplicativeEvidence_supermartingale
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} [IsFiniteMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    {factor : ℕ → Ω → ℝ}
    (factorNonnegative : 0 ≤ factor)
    (factorIntegrable : ∀ n, Integrable (factor n) μ)
    (adapted : StronglyAdapted filtration (multiplicativeEvidence factor))
    (integrable : ∀ n, Integrable (multiplicativeEvidence factor n) μ)
    (conditionalFactorBound : ∀ n,
      μ[factor n | filtration n] ≤ᵐ[μ] (1 : Ω → ℝ)) :
    Supermartingale (multiplicativeEvidence factor) filtration μ := by
  refine supermartingale_nat adapted integrable fun n => ?_
  have hRecurrence :
      multiplicativeEvidence factor (n + 1) =
        multiplicativeEvidence factor n * factor n :=
    multiplicativeEvidence_succ factor n
  have hPullOut :
      μ[multiplicativeEvidence factor n * factor n | filtration n] =ᵐ[μ]
        multiplicativeEvidence factor n * μ[factor n | filtration n] :=
    condExp_mul_of_stronglyMeasurable_left (adapted n)
      (hRecurrence ▸ integrable (n + 1)) (factorIntegrable n)
  calc
    μ[multiplicativeEvidence factor (n + 1) | filtration n] =ᵐ[μ]
        μ[multiplicativeEvidence factor n * factor n | filtration n] := by
      rw [hRecurrence]
    _ =ᵐ[μ] multiplicativeEvidence factor n *
        μ[factor n | filtration n] := hPullOut
    _ ≤ᵐ[μ] multiplicativeEvidence factor n * (1 : Ω → ℝ) := by
      filter_upwards [conditionalFactorBound n] with ω hω
      exact mul_le_mul_of_nonneg_left hω
        (multiplicativeEvidence_nonnegative factorNonnegative n ω)
    _ = multiplicativeEvidence factor n := by
      funext ω
      simp

/-- The concrete fixed-`lambda` evidence process generated by a sequence of
conditionally sub-Gaussian increments. -/
noncomputable def subGaussianFixedLambdaEvidence
    {Ω : Type*} (increment : ℕ → Ω → ℝ) (varianceProxy : ℕ → ℝ≥0)
    (lambda : ℝ) : ℕ → Ω → ℝ :=
  multiplicativeEvidence fun n =>
    subGaussianExponentialFactor (increment n) (varianceProxy n) lambda

theorem subGaussianFixedLambdaEvidence_nonnegative
    {Ω : Type*} (increment : ℕ → Ω → ℝ) (varianceProxy : ℕ → ℝ≥0)
    (lambda : ℝ) :
    0 ≤ subGaussianFixedLambdaEvidence increment varianceProxy lambda := by
  exact multiplicativeEvidence_nonnegative fun n =>
    subGaussianExponentialFactor_nonnegative
      (increment n) (varianceProxy n) lambda

/-- Lag-one observation measurability is sufficient for strong adaptedness of
the accumulated evidence: increment `i` is visible at time `i+1`, while the
time-`n` product contains exactly the increments with `i<n`. -/
theorem subGaussianFixedLambdaEvidence_stronglyAdapted
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    {filtration : Filtration ℕ measurableSpace}
    (increment : ℕ → Ω → ℝ) (varianceProxy : ℕ → ℝ≥0) (lambda : ℝ)
    (incrementMeasurable : ∀ i,
      StronglyMeasurable[filtration (i + 1)] (increment i)) :
    StronglyAdapted filtration
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda) := by
  intro n
  change StronglyMeasurable[filtration n]
    (fun ω => ∏ i ∈ Finset.range n,
      subGaussianExponentialFactor
        (increment i) (varianceProxy i) lambda ω)
  apply Finset.stronglyMeasurable_fun_prod
  intro i iInRange
  have iSuccLe : i + 1 ≤ n := by
    simpa using (Finset.mem_range.mp iInRange)
  have hIncrement :
      StronglyMeasurable[filtration n] (increment i) :=
    (incrementMeasurable i).mono (filtration.mono iSuccLe)
  have hScaled : StronglyMeasurable[filtration n]
      (fun ω => lambda * increment i ω) :=
    stronglyMeasurable_const.mul hIncrement
  have hExp : StronglyMeasurable[filtration n]
      (fun ω => Real.exp (lambda * increment i ω)) :=
    Real.continuous_exp.comp_stronglyMeasurable hScaled
  simpa only [subGaussianExponentialFactor] using
    hExp.const_smul (Real.exp (-((varianceProxy i : ℝ) * lambda ^ 2 / 2)))

/-- Shift an increment observed between times `i` and `i+1` into Mathlib's
process convention, whose time-zero variable is unconditional. -/
def laggedIncrement
    {Ω : Type*} (increment : ℕ → Ω → ℝ) : ℕ → Ω → ℝ
  | 0 => fun _ => 0
  | i + 1 => increment i

def laggedVarianceProxy (varianceProxy : ℕ → ℝ≥0) : ℕ → ℝ≥0
  | 0 => 0
  | i + 1 => varianceProxy i

theorem laggedIncrement_stronglyAdapted
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    {filtration : Filtration ℕ measurableSpace}
    (increment : ℕ → Ω → ℝ)
    (incrementMeasurable : ∀ i,
      StronglyMeasurable[filtration (i + 1)] (increment i)) :
    StronglyAdapted filtration (laggedIncrement increment) := by
  intro n
  cases n with
  | zero =>
      change StronglyMeasurable[filtration 0] (fun _ : Ω => (0 : ℝ))
      exact stronglyMeasurable_const
  | succ n => simpa [laggedIncrement] using incrementMeasurable n

/-- The conditional increment contract implies the usual unconditional
sub-Gaussian MGF contract for every finite prefix. -/
theorem prefixSum_hasSubgaussianMGF
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (increment : ℕ → Ω → ℝ) (varianceProxy : ℕ → ℝ≥0)
    (incrementMeasurable : ∀ i,
      StronglyMeasurable[filtration (i + 1)] (increment i))
    (conditionalSubGaussian : ∀ i,
      HasCondSubgaussianMGF (filtration i) (filtration.le i)
        (increment i) (varianceProxy i) μ)
    (n : ℕ) :
    HasSubgaussianMGF
      (fun ω => ∑ i ∈ Finset.range n, increment i ω)
      (∑ i ∈ Finset.range n, varianceProxy i) μ := by
  have hLaggedAdapted : StronglyAdapted filtration
      (laggedIncrement increment) :=
    laggedIncrement_stronglyAdapted increment incrementMeasurable
  have hZero : HasSubgaussianMGF
      (laggedIncrement increment 0) (laggedVarianceProxy varianceProxy 0) μ := by
    simp [laggedIncrement, laggedVarianceProxy]
  have hPrefix := HasSubgaussianMGF.sum_of_hasCondSubgaussianMGF
    hLaggedAdapted hZero (n + 1) (fun i _ => by
      simpa [laggedIncrement, laggedVarianceProxy] using
        conditionalSubGaussian i)
  simpa [laggedIncrement, laggedVarianceProxy,
    Finset.sum_range_succ'] using hPrefix

theorem subGaussianExponentialFactor_closedForm
    {Ω : Type*} (X : Ω → ℝ) (c : ℝ≥0) (lambda : ℝ) (ω : Ω) :
    subGaussianExponentialFactor X c lambda ω =
      Real.exp (lambda * X ω - (c : ℝ) * lambda ^ 2 / 2) := by
  simp only [subGaussianExponentialFactor, Pi.smul_apply, smul_eq_mul]
  rw [← Real.exp_add]
  congr 1
  ring

/-- Exact closed form used by an implementation: cumulative evidence is the
exponential of cumulative signed signal minus its variance-proxy penalty. -/
theorem subGaussianFixedLambdaEvidence_closedForm
    {Ω : Type*} (increment : ℕ → Ω → ℝ)
    (varianceProxy : ℕ → ℝ≥0) (lambda : ℝ) (n : ℕ) (ω : Ω) :
    subGaussianFixedLambdaEvidence increment varianceProxy lambda n ω =
      Real.exp
        (lambda * (∑ i ∈ Finset.range n, increment i ω) -
          (∑ i ∈ Finset.range n, (varianceProxy i : ℝ)) * lambda ^ 2 / 2) := by
  simp only [subGaussianFixedLambdaEvidence, multiplicativeEvidence]
  simp_rw [subGaussianExponentialFactor_closedForm]
  rw [← Real.exp_sum]
  congr 1
  rw [Finset.sum_sub_distrib]
  have hVariance :
      (∑ i ∈ Finset.range n,
          (varianceProxy i : ℝ) * lambda ^ 2 / 2) =
        (∑ i ∈ Finset.range n, (varianceProxy i : ℝ)) * lambda ^ 2 / 2 := by
    calc
      (∑ i ∈ Finset.range n,
          (varianceProxy i : ℝ) * lambda ^ 2 / 2) =
          (∑ i ∈ Finset.range n,
            (varianceProxy i : ℝ) * lambda ^ 2) / 2 := by
              rw [Finset.sum_div]
      _ = (∑ i ∈ Finset.range n, (varianceProxy i : ℝ)) *
          lambda ^ 2 / 2 := by
            rw [Finset.sum_mul]
  simp only [← Finset.mul_sum]
  rw [hVariance]

/-- Integrability of every accumulated evidence value follows from the same
increment-level contract; it is not an independent modeling assumption. -/
theorem subGaussianFixedLambdaEvidence_integrable
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (increment : ℕ → Ω → ℝ) (varianceProxy : ℕ → ℝ≥0)
    (lambda : ℝ)
    (incrementMeasurable : ∀ i,
      StronglyMeasurable[filtration (i + 1)] (increment i))
    (conditionalSubGaussian : ∀ i,
      HasCondSubgaussianMGF (filtration i) (filtration.le i)
        (increment i) (varianceProxy i) μ)
    (n : ℕ) :
    Integrable
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda n) μ := by
  have hPrefix := prefixSum_hasSubgaussianMGF
    increment varianceProxy incrementMeasurable conditionalSubGaussian n
  have hExp : Integrable
      (fun ω => Real.exp
        (lambda * (∑ i ∈ Finset.range n, increment i ω))) μ :=
    hPrefix.integrable_exp_mul lambda
  have hScaled := hExp.const_mul
    (Real.exp
      (-((∑ i ∈ Finset.range n, (varianceProxy i : ℝ)) * lambda ^ 2 / 2)))
  apply hScaled.congr
  filter_upwards with ω
  rw [subGaussianFixedLambdaEvidence_closedForm]
  rw [← Real.exp_add]
  congr 1
  ring

/-- Operational one-sided boundary.  For positive `lambda` and positive
threshold, crossing the e-process is exactly the displayed affine boundary
for the cumulative increment. -/
theorem subGaussianFixedLambda_crossing_iff_sum_ge_boundary
    {Ω : Type*} (increment : ℕ → Ω → ℝ)
    (varianceProxy : ℕ → ℝ≥0) {lambda : ℝ} (lambdaPositive : 0 < lambda)
    {threshold : ℝ} (thresholdPositive : 0 < threshold)
    (n : ℕ) (ω : Ω) :
    threshold ≤
        subGaussianFixedLambdaEvidence increment varianceProxy lambda n ω ↔
      Real.log threshold / lambda +
          lambda * (∑ i ∈ Finset.range n, (varianceProxy i : ℝ)) / 2 ≤
        ∑ i ∈ Finset.range n, increment i ω := by
  rw [subGaussianFixedLambdaEvidence_closedForm]
  rw [← Real.log_le_iff_le_exp thresholdPositive]
  let signal := ∑ i ∈ Finset.range n, increment i ω
  let variance := ∑ i ∈ Finset.range n, (varianceProxy i : ℝ)
  constructor
  · intro h
    have hDiv : Real.log threshold / lambda ≤
        signal - lambda * variance / 2 := by
      apply (div_le_iff₀ lambdaPositive).2
      nlinarith
    nlinarith
  · intro h
    have hDiv : Real.log threshold / lambda ≤
        signal - lambda * variance / 2 := by
      nlinarith
    have hMul := (div_le_iff₀ lambdaPositive).1 hDiv
    nlinarith

/-- The directly executable finite-look boundary event. -/
def finiteSubGaussianBoundaryCrossing
    {Ω : Type*} (increment : ℕ → Ω → ℝ)
    (varianceProxy : ℕ → ℝ≥0) (lambda : ℝ)
    (threshold : ℝ≥0) (horizon : ℕ) : Set Ω :=
  {ω | ∃ n ∈ Finset.range (horizon + 1),
    Real.log (threshold : ℝ) / lambda +
        lambda * (∑ i ∈ Finset.range n, (varianceProxy i : ℝ)) / 2 ≤
      ∑ i ∈ Finset.range n, increment i ω}

/-- Constructive fixed-`lambda` test-supermartingale theorem.  The conditional
sub-Gaussian model discharges every one-step stochastic inequality; only
adaptedness and integrability of the accumulated process remain as explicit
regularity obligations. -/
theorem subGaussianFixedLambdaEvidence_supermartingale
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    {μ : Measure Ω} [IsFiniteMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    {increment : ℕ → Ω → ℝ} {varianceProxy : ℕ → ℝ≥0}
    (lambda : ℝ)
    (conditionalSubGaussian : ∀ n,
      HasCondSubgaussianMGF (filtration n) (filtration.le n)
        (increment n) (varianceProxy n) μ)
    (adapted : StronglyAdapted filtration
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda))
    (integrable : ∀ n, Integrable
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda n) μ) :
    Supermartingale
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda)
      filtration μ := by
  apply multiplicativeEvidence_supermartingale
  · exact fun n => subGaussianExponentialFactor_nonnegative
      (increment n) (varianceProxy n) lambda
  · exact fun n => subGaussianExponentialFactor_integrable
      (filtration.le n) (conditionalSubGaussian n) lambda
  · exact adapted
  · exact integrable
  · exact fun n => condExp_subGaussianExponentialFactor_le_one
      (filtration.le n) (conditionalSubGaussian n) lambda

/-- Assumption-minimized adapter from observable one-step contracts to the
fixed-`lambda` test supermartingale.  Adaptedness and accumulated
integrability are derived, rather than supplied as independent hypotheses. -/
theorem subGaussianFixedLambdaEvidence_supermartingale_of_increment_contract
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    {increment : ℕ → Ω → ℝ} {varianceProxy : ℕ → ℝ≥0}
    (lambda : ℝ)
    (incrementMeasurable : ∀ i,
      StronglyMeasurable[filtration (i + 1)] (increment i))
    (conditionalSubGaussian : ∀ n,
      HasCondSubgaussianMGF (filtration n) (filtration.le n)
        (increment n) (varianceProxy n) μ) :
    Supermartingale
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda)
      filtration μ := by
  apply subGaussianFixedLambdaEvidence_supermartingale lambda
    conditionalSubGaussian
  · exact subGaussianFixedLambdaEvidence_stronglyAdapted
      increment varianceProxy lambda incrementMeasurable
  · exact fun n => subGaussianFixedLambdaEvidence_integrable
      increment varianceProxy lambda incrementMeasurable
      conditionalSubGaussian n

/-- Ville's finite-horizon inequality for a nonnegative test
supermartingale.  Unlike the earlier martingale-specialized theorem, this is
the form needed by strict conditional-MGF bounds. -/
theorem test_supermartingale_finite_crossing_probability
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    {evidence : ℕ → Ω → ℝ}
    (supermartingale : Supermartingale evidence filtration μ)
    (nonnegative : 0 ≤ evidence)
    (initialMeanBound : ∫ ω, evidence 0 ω ∂μ ≤ 1)
    (threshold : ℝ≥0) (horizon : ℕ) :
    μ (finiteEvidenceCrossing evidence threshold horizon) ≤
      ((threshold : ℝ≥0∞)⁻¹) := by
  classical
  let crossingSet : Set ℝ := {y | (threshold : ℝ) ≤ y}
  let tau : Ω → ℕ∞ := fun ω =>
    (hittingBtwn evidence crossingSet 0 horizon ω : ℕ)
  have hTau : IsStoppingTime filtration tau := by
    exact supermartingale.stronglyAdapted.adapted.isStoppingTime_hittingBtwn
      measurableSet_Ici
  have hTauBound : ∀ ω, tau ω ≤ horizon := by
    intro ω
    show ((hittingBtwn evidence crossingSet 0 horizon ω : ℕ) : ℕ∞) ≤
      (horizon : ℕ∞)
    exact_mod_cast (hittingBtwn_le (u := evidence) (s := crossingSet)
      (n := 0) (m := horizon) ω)
  have hStoppedIntegrable : Integrable (stoppedValue evidence tau) μ :=
    integrable_stoppedValue ℕ hTau supermartingale.integrable hTauBound
  have hCrossingMeasurable :
      MeasurableSet (finiteEvidenceCrossing evidence threshold horizon) := by
    exact measurableSet_le measurable_const
      (Finset.measurable_range_sup'' fun n _ =>
        (supermartingale.stronglyMeasurable n).measurable.le
          (filtration.le n))
  have hThresholdLeStopped : ∀ ω,
      ω ∈ finiteEvidenceCrossing evidence threshold horizon →
        (threshold : ℝ) ≤ stoppedValue evidence tau ω := by
    intro ω hω
    simp only [finiteEvidenceCrossing, Set.mem_setOf_eq] at hω
    simp_rw [Finset.le_sup'_iff, Finset.mem_range, Nat.lt_succ_iff] at hω
    change (threshold : ℝ) ≤ stoppedValue evidence
      (fun ω => (hittingBtwn evidence crossingSet 0 horizon ω : ℕ)) ω
    refine stoppedValue_hittingBtwn_mem ?_
    simp only [crossingSet, Set.mem_setOf_eq]
    obtain ⟨index, indexLe, indexCrosses⟩ := hω
    exact ⟨index, ⟨Nat.zero_le index, indexLe⟩, indexCrosses⟩
  have hThresholdMeasureLeSetIntegral :
      threshold • μ (finiteEvidenceCrossing evidence threshold horizon) ≤
        ENNReal.ofReal
          (∫ ω in finiteEvidenceCrossing evidence threshold horizon,
            stoppedValue evidence tau ω ∂μ) := by
    have hReal := setIntegral_ge_of_const_le_real hCrossingMeasurable
      (measure_ne_top _ _) hThresholdLeStopped hStoppedIntegrable.integrableOn
    rw [ENNReal.le_ofReal_iff_toReal_le, ENNReal.toReal_smul]
    · exact hReal
    · exact ENNReal.mul_ne_top (by simp) (measure_ne_top _ _)
    · exact le_trans
        (mul_nonneg threshold.coe_nonneg ENNReal.toReal_nonneg) hReal
  have hSetIntegralLeFull :
      (∫ ω in finiteEvidenceCrossing evidence threshold horizon,
          stoppedValue evidence tau ω ∂μ) ≤
        ∫ ω, stoppedValue evidence tau ω ∂μ := by
    exact setIntegral_le_integral hStoppedIntegrable
      (Filter.Eventually.of_forall fun ω =>
        nonnegative (tau ω).untopA ω)
  have hStoppedMeanLeInitial :
      (∫ ω, stoppedValue evidence tau ω ∂μ) ≤
        ∫ ω, evidence 0 ω ∂μ := by
    have hOptional := supermartingale.neg.expected_stoppedValue_mono
      (isStoppingTime_const filtration 0) hTau
      (fun _ => by simp [tau]) hTauBound
    have hNegStopped :
        stoppedValue (-evidence) tau = -stoppedValue evidence tau := by
      funext ω
      simp [stoppedValue]
    rw [stoppedValue_const, hNegStopped] at hOptional
    simp only [Pi.neg_apply, integral_neg] at hOptional
    exact neg_le_neg_iff.mp hOptional
  have hProductLeOne :
      (threshold : ℝ≥0∞) *
          μ (finiteEvidenceCrossing evidence threshold horizon) ≤ 1 := by
    calc
      (threshold : ℝ≥0∞) *
          μ (finiteEvidenceCrossing evidence threshold horizon) =
          threshold • μ (finiteEvidenceCrossing evidence threshold horizon) := by
            rfl
      _ ≤ ENNReal.ofReal
          (∫ ω in finiteEvidenceCrossing evidence threshold horizon,
            stoppedValue evidence tau ω ∂μ) := hThresholdMeasureLeSetIntegral
      _ ≤ ENNReal.ofReal (∫ ω, stoppedValue evidence tau ω ∂μ) :=
        ENNReal.ofReal_le_ofReal hSetIntegralLeFull
      _ ≤ ENNReal.ofReal (∫ ω, evidence 0 ω ∂μ) :=
        ENNReal.ofReal_le_ofReal hStoppedMeanLeInitial
      _ ≤ ENNReal.ofReal 1 := ENNReal.ofReal_le_ofReal initialMeanBound
      _ = 1 := by simp
  exact ENNReal.le_inv_iff_mul_le.mpr (by
    simpa [mul_comm] using hProductLeOne)

/-- Fully instantiated anytime-valid bound for the fixed-`lambda`
conditionally sub-Gaussian evidence process. -/
theorem subGaussianFixedLambda_finite_crossing_probability
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    {increment : ℕ → Ω → ℝ} {varianceProxy : ℕ → ℝ≥0}
    (lambda : ℝ)
    (conditionalSubGaussian : ∀ n,
      HasCondSubgaussianMGF (filtration n) (filtration.le n)
        (increment n) (varianceProxy n) μ)
    (adapted : StronglyAdapted filtration
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda))
    (integrable : ∀ n, Integrable
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda n) μ)
    (threshold : ℝ≥0) (horizon : ℕ) :
    μ (finiteEvidenceCrossing
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda)
      threshold horizon) ≤ ((threshold : ℝ≥0∞)⁻¹) := by
  apply test_supermartingale_finite_crossing_probability
    (subGaussianFixedLambdaEvidence_supermartingale lambda
      conditionalSubGaussian adapted integrable)
    (subGaussianFixedLambdaEvidence_nonnegative
      increment varianceProxy lambda)
  simp [subGaussianFixedLambdaEvidence, multiplicativeEvidence]

/-- Numerical prediction surface: under the stated conditional sub-Gaussian
model, the probability that any monitored cumulative sum crosses the explicit
affine boundary is at most `1 / threshold`. -/
theorem finiteSubGaussianBoundaryCrossing_probability
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    {increment : ℕ → Ω → ℝ} {varianceProxy : ℕ → ℝ≥0}
    {lambda : ℝ} (lambdaPositive : 0 < lambda)
    (conditionalSubGaussian : ∀ n,
      HasCondSubgaussianMGF (filtration n) (filtration.le n)
        (increment n) (varianceProxy n) μ)
    (adapted : StronglyAdapted filtration
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda))
    (integrable : ∀ n, Integrable
      (subGaussianFixedLambdaEvidence increment varianceProxy lambda n) μ)
    (threshold : ℝ≥0) (thresholdPositive : 0 < threshold)
    (horizon : ℕ) :
    μ (finiteSubGaussianBoundaryCrossing increment varianceProxy
      lambda threshold horizon) ≤ ((threshold : ℝ≥0∞)⁻¹) := by
  have hCrossing := subGaussianFixedLambda_finite_crossing_probability
    lambda conditionalSubGaussian adapted integrable threshold horizon
  have hEvent :
      finiteSubGaussianBoundaryCrossing increment varianceProxy
          lambda threshold horizon =
        finiteEvidenceCrossing
          (subGaussianFixedLambdaEvidence increment varianceProxy lambda)
          threshold horizon := by
    ext ω
    simp only [finiteSubGaussianBoundaryCrossing, Set.mem_setOf_eq,
      finiteEvidenceCrossing]
    rw [Finset.le_sup'_iff]
    constructor
    · rintro ⟨n, nMem, hBoundary⟩
      exact ⟨n, nMem,
        (subGaussianFixedLambda_crossing_iff_sum_ge_boundary
          increment varianceProxy lambdaPositive thresholdPositive n ω).2
          hBoundary⟩
    · rintro ⟨n, nMem, hEvidence⟩
      exact ⟨n, nMem,
        (subGaussianFixedLambda_crossing_iff_sum_ge_boundary
          increment varianceProxy lambdaPositive thresholdPositive n ω).1
          hEvidence⟩
  rw [hEvent]
  exact hCrossing

/-- Executable affine anytime bound with no process-level regularity premises:
lag-one observability and the conditional sub-Gaussian contracts imply them. -/
theorem finiteSubGaussianBoundaryCrossing_probability_of_increment_contract
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    {increment : ℕ → Ω → ℝ} {varianceProxy : ℕ → ℝ≥0}
    {lambda : ℝ} (lambdaPositive : 0 < lambda)
    (incrementMeasurable : ∀ i,
      StronglyMeasurable[filtration (i + 1)] (increment i))
    (conditionalSubGaussian : ∀ n,
      HasCondSubgaussianMGF (filtration n) (filtration.le n)
        (increment n) (varianceProxy n) μ)
    (threshold : ℝ≥0) (thresholdPositive : 0 < threshold)
    (horizon : ℕ) :
    μ (finiteSubGaussianBoundaryCrossing increment varianceProxy
      lambda threshold horizon) ≤ ((threshold : ℝ≥0∞)⁻¹) := by
  apply finiteSubGaussianBoundaryCrossing_probability
    lambdaPositive conditionalSubGaussian
  · exact subGaussianFixedLambdaEvidence_stronglyAdapted
      increment varianceProxy lambda incrementMeasurable
  · exact fun n => subGaussianFixedLambdaEvidence_integrable
      increment varianceProxy lambda incrementMeasurable
      conditionalSubGaussian n
  · exact thresholdPositive

/-- Confidence-sequence inversion for a family of nonnegative test
supermartingales. -/
theorem test_supermartingale_confidence_sequence_exclusion_control
    {Ω Θ : Type*} {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (evidence : Θ → ℕ → Ω → ℝ) (θ : Θ)
    (supermartingale : Supermartingale (evidence θ) filtration μ)
    (nonnegative : 0 ≤ evidence θ)
    (initialMeanBound : ∫ ω, evidence θ 0 ω ∂μ ≤ 1)
    (threshold : ℝ≥0) (horizon : ℕ) :
    μ {ω | ∃ index ∈ Finset.range (horizon + 1),
      θ ∉ eConfidenceSet evidence threshold index ω} ≤
      ((threshold : ℝ≥0∞)⁻¹) := by
  have crossingBound := test_supermartingale_finite_crossing_probability
    supermartingale nonnegative initialMeanBound threshold horizon
  have eventEquality :
      {ω | ∃ index ∈ Finset.range (horizon + 1),
        θ ∉ eConfidenceSet evidence threshold index ω} =
        finiteEvidenceCrossing (evidence θ) threshold horizon := by
    ext ω
    exact eConfidenceSet_failure_iff_crossing
      evidence threshold horizon θ ω
  rw [eventEquality]
  exact crossingBound

/-- A finite nonnegative mixture of evidence processes.  This is the directly
computable approximation layer for continuous mixture boundaries. -/
noncomputable def finiteEvidenceMixture
    {Ω Λ : Type*} (grid : Finset Λ) (weight : Λ → ℝ)
    (evidence : Λ → ℕ → Ω → ℝ) : ℕ → Ω → ℝ :=
  ∑ parameter ∈ grid, weight parameter • evidence parameter

theorem finiteEvidenceMixture_supermartingale
    {Ω Λ : Type*} {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} {filtration : Filtration ℕ measurableSpace}
    (grid : Finset Λ) (weight : Λ → ℝ)
    (evidence : Λ → ℕ → Ω → ℝ)
    (weightNonnegative : ∀ parameter ∈ grid, 0 ≤ weight parameter)
    (componentSupermartingale : ∀ parameter ∈ grid,
      Supermartingale (evidence parameter) filtration μ) :
    Supermartingale (finiteEvidenceMixture grid weight evidence)
      filtration μ := by
  classical
  induction grid using Finset.induction_on with
  | empty =>
      simpa [finiteEvidenceMixture] using
        (martingale_zero ℝ filtration μ).supermartingale
  | @insert parameter grid parameterNotInGrid inductionHypothesis =>
      have hParameter := (componentSupermartingale parameter
        (Finset.mem_insert_self parameter grid)).smul_nonneg
          (weightNonnegative parameter
            (Finset.mem_insert_self parameter grid))
      have hGrid := inductionHypothesis
        (fun candidate candidateInGrid =>
          weightNonnegative candidate
            (Finset.mem_insert_of_mem candidateInGrid))
        (fun candidate candidateInGrid =>
          componentSupermartingale candidate
            (Finset.mem_insert_of_mem candidateInGrid))
      simpa [finiteEvidenceMixture, Finset.sum_insert,
        parameterNotInGrid] using hParameter.add hGrid

theorem finiteEvidenceMixture_nonnegative
    {Ω Λ : Type*} (grid : Finset Λ) (weight : Λ → ℝ)
    (evidence : Λ → ℕ → Ω → ℝ)
    (weightNonnegative : ∀ parameter ∈ grid, 0 ≤ weight parameter)
    (componentNonnegative : ∀ parameter ∈ grid,
      0 ≤ evidence parameter) :
    0 ≤ finiteEvidenceMixture grid weight evidence := by
  intro n ω
  simp only [finiteEvidenceMixture, Finset.sum_apply,
    Pi.smul_apply, smul_eq_mul]
  exact Finset.sum_nonneg fun parameter parameterInGrid =>
    mul_nonneg (weightNonnegative parameter parameterInGrid)
      (componentNonnegative parameter parameterInGrid n ω)

theorem finiteEvidenceMixture_initial_one
    {Ω Λ : Type*} (grid : Finset Λ) (weight : Λ → ℝ)
    (evidence : Λ → ℕ → Ω → ℝ)
    (weightSum : ∑ parameter ∈ grid, weight parameter = 1)
    (componentInitial : ∀ parameter ∈ grid,
      evidence parameter 0 = (1 : Ω → ℝ)) :
    finiteEvidenceMixture grid weight evidence 0 = (1 : Ω → ℝ) := by
  funext ω
  simp only [finiteEvidenceMixture, Finset.sum_apply,
    Pi.smul_apply, smul_eq_mul]
  calc
    (∑ parameter ∈ grid, weight parameter * evidence parameter 0 ω) =
        ∑ parameter ∈ grid, weight parameter := by
      apply Finset.sum_congr rfl
      intro parameter parameterInGrid
      rw [componentInitial parameter parameterInGrid]
      simp
    _ = 1 := weightSum

/-- A computable, pointwise error certificate for a finite mixture.  It turns
component implementation or grid errors into one exact weighted envelope. -/
theorem finiteEvidenceMixture_componentwise_error_bound
    {Ω Λ : Type*} (grid : Finset Λ) (weight error : Λ → ℝ)
    (evidence approximation : Λ → ℕ → Ω → ℝ)
    (weightNonnegative : ∀ parameter ∈ grid, 0 ≤ weight parameter)
    (componentError : ∀ parameter ∈ grid, ∀ n ω,
      |evidence parameter n ω - approximation parameter n ω| ≤
        error parameter)
    (n : ℕ) (ω : Ω) :
    |finiteEvidenceMixture grid weight evidence n ω -
        finiteEvidenceMixture grid weight approximation n ω| ≤
      ∑ parameter ∈ grid, weight parameter * error parameter := by
  classical
  simp only [finiteEvidenceMixture, Finset.sum_apply,
    Pi.smul_apply, smul_eq_mul]
  rw [← Finset.sum_sub_distrib]
  have hRewrite :
      (∑ parameter ∈ grid,
          (weight parameter * evidence parameter n ω -
            weight parameter * approximation parameter n ω)) =
        ∑ parameter ∈ grid,
          weight parameter *
            (evidence parameter n ω - approximation parameter n ω) := by
    apply Finset.sum_congr rfl
    intro parameter parameterInGrid
    ring
  rw [hRewrite]
  calc
    |∑ parameter ∈ grid,
        weight parameter *
          (evidence parameter n ω - approximation parameter n ω)| ≤
        ∑ parameter ∈ grid,
          |weight parameter *
            (evidence parameter n ω - approximation parameter n ω)| :=
      Finset.abs_sum_le_sum_abs _ _
    _ = ∑ parameter ∈ grid,
          weight parameter *
            |evidence parameter n ω - approximation parameter n ω| := by
      apply Finset.sum_congr rfl
      intro parameter parameterInGrid
      rw [abs_mul, abs_of_nonneg
        (weightNonnegative parameter parameterInGrid)]
    _ ≤ ∑ parameter ∈ grid, weight parameter * error parameter := by
      apply Finset.sum_le_sum
      intro parameter parameterInGrid
      exact mul_le_mul_of_nonneg_left
        (componentError parameter parameterInGrid n ω)
        (weightNonnegative parameter parameterInGrid)

end OCKIndividuationMSpaceComposition
