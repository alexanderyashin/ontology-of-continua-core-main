import Mathlib.MeasureTheory.Measure.Portmanteau
import OCMinimalObligationSpine.Q073LogarithmicDiffusionDivergence

/-!
OC Core 1.4 minimal obligation spine: the Q073 Portmanteau/truncation bridge.

This file mechanizes the implication that was previously missing between an
external weak limit theorem and the release-authorized positive logarithmic
lower bound.  It does **not** assume convergence of second moments.

Let `μt` be the laws of the normalized displacements and let `μ∞` be their weak
limit.  A bounded continuous truncation of the squared norm has convergent
expectations by the definition of weak convergence.  If its limiting
expectation is positive and it is pointwise dominated by the normalized second
moment, the latter is eventually bounded below by half that positive
expectation.  The normalization

  `effectiveCoefficient t = normalizedSecondMoment t * log t / 4`

then yields an eventual positive multiple of `log t`, hence divergence and the
nonexistence of a finite ordinary diffusion coefficient.

The external billiard theorem and its hypotheses remain source-bound inputs.
Positivity is no longer an independent source-bound premise: below it is
derived from the explicit nondegeneracy condition that the weak limit assigns
positive mass outside the origin.  No upper moment bound, exact asymptotic
equality, or exact moment coefficient is claimed.
-/

namespace OCMinimalObligationSpine

open Filter MeasureTheory
open scoped BoundedContinuousFunction ENNReal Topology

/-- Portmanteau in the exact nonnegative continuous-function form used by the
Q073 audit.  This theorem is useful when an unbounded observable is handled
directly through `lintegral`; the release bridge below instead uses bounded
continuous truncations, which require fewer moment assumptions. -/
theorem q073_portmanteau_nonnegative_lintegral_lower_bound
    {Ω : Type*}
    [MeasurableSpace Ω] [TopologicalSpace Ω]
    [OpensMeasurableSpace Ω] [HasOuterApproxClosed Ω]
    {μ : ProbabilityMeasure Ω}
    {μs : ℕ → ProbabilityMeasure Ω}
    (hWeak : Tendsto μs atTop (𝓝 μ))
    {f : Ω → ℝ}
    (hfContinuous : Continuous f)
    (hfNonnegative : 0 ≤ f) :
    ∫⁻ x, ENNReal.ofReal (f x) ∂(μ : Measure Ω) ≤
      atTop.liminf
        (fun n ↦ ∫⁻ x, ENNReal.ofReal (f x) ∂(μs n : Measure Ω)) := by
  apply
    lintegral_le_liminf_lintegral_of_forall_isOpen_measure_le_liminf_measure
      hfContinuous hfNonnegative
  intro G hG
  exact ProbabilityMeasure.le_liminf_measure_open_of_tendsto hWeak hG

/-- The canonical bounded continuous truncation of the squared norm used by
the Q073 weak-limit bridge.  Its range is contained in `[0, 1]`, so weak
convergence controls its expectations without assuming convergence or uniform
integrability of the unbounded second moments. -/
def q073_squared_norm_truncation
    (E : Type*) [NormedAddCommGroup E] :
    E →ᵇ ℝ where
  toFun x := min (‖x‖ ^ 2) 1
  continuous_toFun := (continuous_norm.pow 2).min continuous_const
  map_bounded' := by
    refine ⟨1, fun x y ↦ ?_⟩
    rw [Real.dist_eq, abs_le]
    have hx0 : 0 ≤ min (‖x‖ ^ 2) 1 :=
      le_min (sq_nonneg _) zero_le_one
    have hx1 : min (‖x‖ ^ 2) 1 ≤ 1 := min_le_right _ _
    have hy0 : 0 ≤ min (‖y‖ ^ 2) 1 :=
      le_min (sq_nonneg _) zero_le_one
    have hy1 : min (‖y‖ ^ 2) 1 ≤ 1 := min_le_right _ _
    constructor <;> linarith

@[simp]
theorem q073_squared_norm_truncation_apply
    (E : Type*) [NormedAddCommGroup E] (x : E) :
    q073_squared_norm_truncation E x = min (‖x‖ ^ 2) 1 := rfl

/-- Positive mass away from the origin is the exact minimal nondegeneracy
condition needed by the Q073 truncation argument.  It makes the limiting
truncated second moment strictly positive. -/
theorem q073_squared_norm_truncation_integral_pos_of_nondegenerate
    {E : Type*}
    [NormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    (μ : ProbabilityMeasure E)
    (hNondegenerate : 0 < (μ : Measure E) ({0}ᶜ)) :
    0 < ∫ x, q073_squared_norm_truncation E x ∂(μ : Measure E) := by
  rw [integral_pos_iff_support_of_nonneg]
  · have hSupport :
        Function.support (q073_squared_norm_truncation E) =
          ({0}ᶜ : Set E) := by
      ext x
      simp only [Function.mem_support, q073_squared_norm_truncation_apply,
        Set.mem_compl_iff, Set.mem_singleton_iff]
      constructor
      · intro h hx
        subst x
        simp at h
      · intro hx
        exact ne_of_gt <|
          (lt_min_iff).2
            ⟨sq_pos_of_pos (norm_pos_iff.mpr hx), zero_lt_one⟩
    rw [hSupport]
    exact hNondegenerate
  · intro x
    exact le_min (sq_nonneg _) zero_le_one
  · exact (q073_squared_norm_truncation E).integrable _

/-- Weak convergence plus one positive bounded continuous truncation forces an
eventual positive floor for every dominating normalized second-moment
observable.  The index/filter are general; Q073 specializes them to real time
and `atTop`. -/
theorem q073_weak_limit_truncation_yields_eventual_moment_floor
    {Ω ι : Type*}
    [MeasurableSpace Ω] [TopologicalSpace Ω] [OpensMeasurableSpace Ω]
    {L : Filter ι}
    {μi : ι → ProbabilityMeasure Ω}
    {μLimit : ProbabilityMeasure Ω}
    (hWeak : Tendsto μi L (𝓝 μLimit))
    (truncatedSquaredNorm : Ω →ᵇ ℝ)
    (normalizedSecondMoment : ι → ℝ)
    (hLimitPositive :
      0 < ∫ x, truncatedSquaredNorm x ∂(μLimit : Measure Ω))
    (hTruncationDominated :
      ∀ i,
        ∫ x, truncatedSquaredNorm x ∂(μi i : Measure Ω) ≤
          normalizedSecondMoment i) :
    ∀ᶠ i in L,
      (∫ x, truncatedSquaredNorm x ∂(μLimit : Measure Ω)) / 2 ≤
        normalizedSecondMoment i := by
  let limitExpectation : ℝ :=
    ∫ x, truncatedSquaredNorm x ∂(μLimit : Measure Ω)
  have hIntegralTendsto :
      Tendsto
        (fun i ↦ ∫ x, truncatedSquaredNorm x ∂(μi i : Measure Ω))
        L
        (𝓝 limitExpectation) := by
    exact
      (ProbabilityMeasure.tendsto_iff_forall_integral_tendsto.mp hWeak)
        truncatedSquaredNorm
  have hHalfBelow : limitExpectation / 2 < limitExpectation := by
    exact (half_lt_self_iff.mpr hLimitPositive)
  have hEventuallyAboveHalf :
      ∀ᶠ i in L,
        limitExpectation / 2 <
          ∫ x, truncatedSquaredNorm x ∂(μi i : Measure Ω) :=
    tendsto_const_nhds.eventually_lt hIntegralTendsto hHalfBelow
  filter_upwards [hEventuallyAboveHalf] with i hi
  exact hi.le.trans (hTruncationDominated i)

/-- The concrete nondegenerate-limit version of the generic truncation lemma.
Unlike `q073_weak_limit_truncation_yields_eventual_moment_floor`, this theorem
does not ask the caller to supply a positive limiting integral: it derives that
fact from positive weak-limit mass outside the origin. -/
theorem q073_weak_nondegenerate_limit_yields_eventual_moment_floor
    {E ι : Type*}
    [NormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    {L : Filter ι}
    {μi : ι → ProbabilityMeasure E}
    {μLimit : ProbabilityMeasure E}
    (hWeak : Tendsto μi L (𝓝 μLimit))
    (hNondegenerate : 0 < (μLimit : Measure E) ({0}ᶜ))
    (normalizedSecondMoment : ι → ℝ)
    (hTruncationDominated :
      ∀ i,
        ∫ x, q073_squared_norm_truncation E x ∂(μi i : Measure E) ≤
          normalizedSecondMoment i) :
    ∃ c : ℝ,
      0 < c ∧ ∀ᶠ i in L, c ≤ normalizedSecondMoment i := by
  have hLimitPositive :=
    q073_squared_norm_truncation_integral_pos_of_nondegenerate
      μLimit hNondegenerate
  refine
    ⟨(∫ x, q073_squared_norm_truncation E x ∂(μLimit : Measure E)) / 2,
      half_pos hLimitPositive, ?_⟩
  exact
    q073_weak_limit_truncation_yields_eventual_moment_floor
      hWeak (q073_squared_norm_truncation E) normalizedSecondMoment
      hLimitPositive hTruncationDominated

/-- The fully mechanized Q073 weak-limit-to-logarithmic-lower-bound bridge.

The chosen constant is one eighth of the positive limiting truncated
expectation: one factor `1/2` is the safe eventual convergence margin and one
factor `1/4` is the two-dimensional diffusion convention
`D_eff = MSD / (4 t)`.
-/
theorem q073_weak_limit_truncation_yields_positive_log_lower_bound
    {Ω : Type*}
    [MeasurableSpace Ω] [TopologicalSpace Ω] [OpensMeasurableSpace Ω]
    {μt : ℝ → ProbabilityMeasure Ω}
    {μLimit : ProbabilityMeasure Ω}
    (hWeak : Tendsto μt atTop (𝓝 μLimit))
    (truncatedSquaredNorm : Ω →ᵇ ℝ)
    (normalizedSecondMoment effectiveCoefficient : ℝ → ℝ)
    (hLimitPositive :
      0 < ∫ x, truncatedSquaredNorm x ∂(μLimit : Measure Ω))
    (hTruncationDominated :
      ∀ t,
        ∫ x, truncatedSquaredNorm x ∂(μt t : Measure Ω) ≤
          normalizedSecondMoment t)
    (hEffectiveCoefficient :
      ∀ t,
        effectiveCoefficient t =
          normalizedSecondMoment t * Real.log t / 4) :
    ∃ c : ℝ,
      0 < c ∧
        ∀ᶠ t : ℝ in atTop,
          0 < t ∧ c * Real.log t ≤ effectiveCoefficient t := by
  let limitExpectation : ℝ :=
    ∫ x, truncatedSquaredNorm x ∂(μLimit : Measure Ω)
  have hMomentFloor :
      ∀ᶠ t : ℝ in atTop,
        limitExpectation / 2 ≤ normalizedSecondMoment t := by
    exact q073_weak_limit_truncation_yields_eventual_moment_floor
      hWeak truncatedSquaredNorm normalizedSecondMoment hLimitPositive
      hTruncationDominated
  refine ⟨limitExpectation / 8, ?_, ?_⟩
  · exact div_pos hLimitPositive (by norm_num)
  · filter_upwards [hMomentFloor, eventually_gt_atTop (1 : ℝ)]
      with t hFloor ht
    have hLogNonnegative : 0 ≤ Real.log t :=
      Real.log_nonneg ht.le
    have hScaledFloor :
        (limitExpectation / 2) * Real.log t ≤
          normalizedSecondMoment t * Real.log t :=
      mul_le_mul_of_nonneg_right hFloor hLogNonnegative
    constructor
    · exact zero_lt_one.trans ht
    · rw [hEffectiveCoefficient t]
      calc
        (limitExpectation / 8) * Real.log t =
            ((limitExpectation / 2) * Real.log t) / 4 := by ring
        _ ≤ (normalizedSecondMoment t * Real.log t) / 4 :=
          div_le_div_of_nonneg_right hScaledFloor (by norm_num)

/-- The release-facing logarithmic lower bound with positivity discharged from
the explicit nondegeneracy of the weak limit. -/
theorem q073_weak_nondegenerate_limit_yields_positive_log_lower_bound
    {E : Type*}
    [NormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    {μt : ℝ → ProbabilityMeasure E}
    {μLimit : ProbabilityMeasure E}
    (hWeak : Tendsto μt atTop (𝓝 μLimit))
    (hNondegenerate : 0 < (μLimit : Measure E) ({0}ᶜ))
    (normalizedSecondMoment effectiveCoefficient : ℝ → ℝ)
    (hTruncationDominated :
      ∀ t,
        ∫ x, q073_squared_norm_truncation E x ∂(μt t : Measure E) ≤
          normalizedSecondMoment t)
    (hEffectiveCoefficient :
      ∀ t,
        effectiveCoefficient t =
          normalizedSecondMoment t * Real.log t / 4) :
    ∃ c : ℝ,
      0 < c ∧
        ∀ᶠ t : ℝ in atTop,
          0 < t ∧ c * Real.log t ≤ effectiveCoefficient t := by
  exact
    q073_weak_limit_truncation_yields_positive_log_lower_bound
      hWeak (q073_squared_norm_truncation E) normalizedSecondMoment
      effectiveCoefficient
      (q073_squared_norm_truncation_integral_pos_of_nondegenerate
        μLimit hNondegenerate)
      hTruncationDominated hEffectiveCoefficient

/-- The explicit divergence consequence for the nondegenerate source-bound
bridge.  This theorem makes the full proof chain inspectable without asking a
consumer to reconstruct the composition from theorem names. -/
theorem q073_weak_nondegenerate_limit_tends_to_atTop
    {E : Type*}
    [NormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    {μt : ℝ → ProbabilityMeasure E}
    {μLimit : ProbabilityMeasure E}
    (hWeak : Tendsto μt atTop (𝓝 μLimit))
    (hNondegenerate : 0 < (μLimit : Measure E) ({0}ᶜ))
    (normalizedSecondMoment effectiveCoefficient : ℝ → ℝ)
    (hTruncationDominated :
      ∀ t,
        ∫ x, q073_squared_norm_truncation E x ∂(μt t : Measure E) ≤
          normalizedSecondMoment t)
    (hEffectiveCoefficient :
      ∀ t,
        effectiveCoefficient t =
          normalizedSecondMoment t * Real.log t / 4) :
    Tendsto effectiveCoefficient atTop atTop := by
  obtain ⟨c, hc, hLowerBound⟩ :=
    q073_weak_nondegenerate_limit_yields_positive_log_lower_bound
      hWeak hNondegenerate normalizedSecondMoment effectiveCoefficient
      hTruncationDominated hEffectiveCoefficient
  exact
    q073_q012_eventual_positive_log_lower_bound_diverges_atTop
      hc hLowerBound

/-- The release-facing consequence: under the source theorem and the explicit
normalization/dominance bindings above, the effective coefficient cannot have a
finite ordinary limit. -/
theorem
    q073_weak_limit_truncation_rejects_finite_ordinary_diffusion_coefficient
    {Ω : Type*}
    [MeasurableSpace Ω] [TopologicalSpace Ω] [OpensMeasurableSpace Ω]
    {μt : ℝ → ProbabilityMeasure Ω}
    {μLimit : ProbabilityMeasure Ω}
    (hWeak : Tendsto μt atTop (𝓝 μLimit))
    (truncatedSquaredNorm : Ω →ᵇ ℝ)
    (normalizedSecondMoment effectiveCoefficient : ℝ → ℝ)
    (hLimitPositive :
      0 < ∫ x, truncatedSquaredNorm x ∂(μLimit : Measure Ω))
    (hTruncationDominated :
      ∀ t,
        ∫ x, truncatedSquaredNorm x ∂(μt t : Measure Ω) ≤
          normalizedSecondMoment t)
    (hEffectiveCoefficient :
      ∀ t,
        effectiveCoefficient t =
          normalizedSecondMoment t * Real.log t / 4) :
    ¬ ∃ finiteCoefficient : ℝ,
      Tendsto effectiveCoefficient atTop (𝓝 finiteCoefficient) := by
  obtain ⟨c, hc, hLowerBound⟩ :=
    q073_weak_limit_truncation_yields_positive_log_lower_bound
      hWeak truncatedSquaredNorm normalizedSecondMoment effectiveCoefficient
      hLimitPositive hTruncationDominated hEffectiveCoefficient
  exact
    q073_q012_eventual_positive_log_lower_bound_has_no_finite_ordinary_coefficient
      hc hLowerBound

/-- The strongest release-facing Q073 bridge currently available: weak
convergence to a limit with positive mass outside the origin, plus the explicit
normalization and domination bindings, rules out every finite ordinary
diffusion coefficient.  No separate positivity oracle is required. -/
theorem
    q073_weak_nondegenerate_limit_rejects_finite_ordinary_diffusion_coefficient
    {E : Type*}
    [NormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    {μt : ℝ → ProbabilityMeasure E}
    {μLimit : ProbabilityMeasure E}
    (hWeak : Tendsto μt atTop (𝓝 μLimit))
    (hNondegenerate : 0 < (μLimit : Measure E) ({0}ᶜ))
    (normalizedSecondMoment effectiveCoefficient : ℝ → ℝ)
    (hTruncationDominated :
      ∀ t,
        ∫ x, q073_squared_norm_truncation E x ∂(μt t : Measure E) ≤
          normalizedSecondMoment t)
    (hEffectiveCoefficient :
      ∀ t,
        effectiveCoefficient t =
          normalizedSecondMoment t * Real.log t / 4) :
    ¬ ∃ finiteCoefficient : ℝ,
      Tendsto effectiveCoefficient atTop (𝓝 finiteCoefficient) := by
  obtain ⟨c, hc, hLowerBound⟩ :=
    q073_weak_nondegenerate_limit_yields_positive_log_lower_bound
      hWeak hNondegenerate normalizedSecondMoment effectiveCoefficient
      hTruncationDominated hEffectiveCoefficient
  exact
    q073_q012_eventual_positive_log_lower_bound_has_no_finite_ordinary_coefficient
      hc hLowerBound

end OCMinimalObligationSpine
