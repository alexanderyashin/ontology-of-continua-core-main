import OCKIndividuationMSpaceComposition.AnytimeSpendingOptimization
import Mathlib.Probability.Martingale.OptionalStopping

namespace OCKIndividuationMSpaceComposition

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory
open MeasureTheory

/-!
## Test martingales and finite-horizon confidence-sequence inversion

This module separates fixed-time e-values from genuine anytime evidence.  A
nonnegative test martingale with mean at most one satisfies a finite-horizon
Ville bound by Doob's maximal inequality.  Inverting its threshold therefore
produces a confidence-sequence exclusion event with the same time-uniform
error bound.
-/

/-- The event that an evidence process crosses `threshold` by `horizon`. -/
def finiteEvidenceCrossing
    {Ω : Type*} (evidence : ℕ → Ω → ℝ) (threshold : ℝ≥0) (horizon : ℕ) : Set Ω :=
  {ω | (threshold : ℝ) ≤
    (Finset.range (horizon + 1)).sup' Finset.nonempty_range_add_one
      fun index => evidence index ω}

/-- A finite-horizon form of Ville's inequality derived from Mathlib's
formalized Doob maximal inequality.  The mean premise is intentionally
explicit: it is the operational normalization obligation for a proposed test
martingale. -/
theorem test_martingale_finite_crossing_probability
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    {evidence : ℕ → Ω → ℝ}
    (martingale : Martingale evidence filtration μ)
    (nonnegative : 0 ≤ evidence)
    (meanBound : ∀ index, ∫ ω, evidence index ω ∂μ ≤ 1)
    (threshold : ℝ≥0) (horizon : ℕ) :
    μ (finiteEvidenceCrossing evidence threshold horizon) ≤
      ((threshold : ℝ≥0∞)⁻¹) := by
  have maximal := maximal_ineq martingale.submartingale nonnegative
    (ε := threshold) horizon
  have restrictedIntegralLe :
      (∫ ω in finiteEvidenceCrossing evidence threshold horizon,
          evidence horizon ω ∂μ) ≤
        ∫ ω, evidence horizon ω ∂μ := by
    exact setIntegral_le_integral (martingale.integrable horizon)
      (Filter.Eventually.of_forall fun ω => nonnegative horizon ω)
  have restrictedIntegralLeOne :
      (∫ ω in finiteEvidenceCrossing evidence threshold horizon,
          evidence horizon ω ∂μ) ≤ 1 :=
    restrictedIntegralLe.trans (meanBound horizon)
  have productLeOne :
      (threshold : ℝ≥0∞) * μ (finiteEvidenceCrossing evidence threshold horizon) ≤ 1 := by
    calc
      (threshold : ℝ≥0∞) * μ (finiteEvidenceCrossing evidence threshold horizon) =
          threshold • μ (finiteEvidenceCrossing evidence threshold horizon) := by
            rfl
      _ ≤ ENNReal.ofReal
          (∫ ω in finiteEvidenceCrossing evidence threshold horizon,
            evidence horizon ω ∂μ) := maximal
      _ ≤ ENNReal.ofReal 1 := ENNReal.ofReal_le_ofReal restrictedIntegralLeOne
      _ = 1 := by simp
  exact ENNReal.le_inv_iff_mul_le.mpr (by
    simpa [mul_comm] using productLeOne)

/-- Parameter values retained by inversion of a test-martingale threshold. -/
def eConfidenceSet
    {Ω Θ : Type*} (evidence : Θ → ℕ → Ω → ℝ)
    (threshold : ℝ≥0) (index : ℕ) (ω : Ω) : Set Θ :=
  {θ | evidence θ index ω < (threshold : ℝ)}

/-- Excluding the true parameter at any look up to `horizon` is exactly a
threshold crossing of its evidence process. -/
theorem eConfidenceSet_failure_iff_crossing
    {Ω Θ : Type*} (evidence : Θ → ℕ → Ω → ℝ)
    (threshold : ℝ≥0) (horizon : ℕ) (θ : Θ) (ω : Ω) :
    (∃ index ∈ Finset.range (horizon + 1),
      θ ∉ eConfidenceSet evidence threshold index ω) ↔
      ω ∈ finiteEvidenceCrossing (evidence θ) threshold horizon := by
  classical
  simp only [eConfidenceSet, Set.mem_setOf_eq, not_lt,
    finiteEvidenceCrossing]
  constructor
  · rintro ⟨index, indexMem, crossing⟩
    exact crossing.trans
      (Finset.le_sup' (f := fun k => evidence θ k ω) indexMem)
  · intro crossing
    obtain ⟨index, indexMem, indexMax⟩ :=
      Finset.exists_mem_eq_sup' Finset.nonempty_range_add_one
        (fun k => evidence θ k ω)
    exact ⟨index, indexMem, indexMax ▸ crossing⟩

/-- Positive confidence-sequence theorem: inversion of a normalized
nonnegative test martingale controls exclusion of the true parameter at any
finite monitoring look. -/
theorem test_martingale_confidence_sequence_exclusion_control
    {Ω Θ : Type*} {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (evidence : Θ → ℕ → Ω → ℝ) (θ : Θ)
    (martingale : Martingale (evidence θ) filtration μ)
    (nonnegative : 0 ≤ evidence θ)
    (meanBound : ∀ index, ∫ ω, evidence θ index ω ∂μ ≤ 1)
    (threshold : ℝ≥0) (horizon : ℕ) :
    μ {ω | ∃ index ∈ Finset.range (horizon + 1),
      θ ∉ eConfidenceSet evidence threshold index ω} ≤
      ((threshold : ℝ≥0∞)⁻¹) := by
  have crossingBound := test_martingale_finite_crossing_probability
    martingale nonnegative meanBound threshold horizon
  have eventEquality :
      {ω | ∃ index ∈ Finset.range (horizon + 1),
        θ ∉ eConfidenceSet evidence threshold index ω} =
        finiteEvidenceCrossing (evidence θ) threshold horizon := by
    ext ω
    exact eConfidenceSet_failure_iff_crossing evidence threshold horizon θ ω
  rw [eventEquality]
  exact crossingBound

/-- Fixed-time calibration does not compose into an anytime guarantee.  If
two disjoint monitoring looks each cross with mass `alpha`, the union crosses
with mass `2*alpha`, strictly exceeding the fixed-time report. -/
theorem disjoint_fixed_time_crossings_exceed_single_look_report
    {Ω : Type*} {measurableSpace : MeasurableSpace Ω}
    {μ : Measure Ω} {first second : Set Ω} (alpha : ℝ≥0∞)
    (alphaPositive : 0 < alpha) (alphaFinite : alpha ≠ ∞)
    (firstMeasurable : MeasurableSet first)
    (disjointCrossings : Disjoint first second)
    (firstMass : μ first = alpha) (secondMass : μ second = alpha) :
    alpha < μ (first ∪ second) := by
  rw [measure_union' disjointCrossings firstMeasurable, firstMass, secondMass]
  exact ENNReal.lt_add_right alphaFinite (ne_of_gt alphaPositive)

end OCKIndividuationMSpaceComposition
