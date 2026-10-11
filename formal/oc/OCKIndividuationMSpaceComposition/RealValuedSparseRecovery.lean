import OCKIndividuationMSpaceComposition.SparseDesignRecoveryGeometry
import Mathlib.Analysis.Normed.Module.Basic

namespace OCKIndividuationMSpaceComposition

section RestrictedNorm

variable {Parameter Observation : Type*}
  [NormedAddCommGroup Parameter] [NormedSpace ℝ Parameter]
  [NormedAddCommGroup Observation] [NormedSpace ℝ Observation]

/-- Lower restricted singular-value contract on a declared difference class. -/
def RestrictedNormLowerBound
    (design : Parameter →ₗ[ℝ] Observation)
    (differenceClass : Parameter → Prop) (alpha : ℝ) : Prop :=
  ∀ difference, differenceClass difference →
    alpha * ‖difference‖ ≤ ‖design difference‖

/-- Two admissible `s`-sparse states differ inside the declared `2s` class. -/
def DifferenceClosed
    (admissible differenceClass : Parameter → Prop) : Prop :=
  ∀ ⦃first second⦄,
    admissible first → admissible second → differenceClass (first - second)

/-- A lower restricted singular value on differences induces the metric lower
bound consumed by the generic recovery geometry. -/
theorem restrictedNormLowerBound_yields_pairGeometry
    (design : Parameter →ₗ[ℝ] Observation)
    (admissible differenceClass : Parameter → Prop) (alpha : ℝ)
    (lowerBound : RestrictedNormLowerBound design differenceClass alpha)
    (differenceClosed : DifferenceClosed admissible differenceClass) :
    RestrictedSeparationLowerBound design admissible alpha := by
  intro first second firstAdmissible secondAdmissible
  simpa [dist_eq_norm] using
    lowerBound (first - second)
      (differenceClosed firstAdmissible secondAdmissible)

/-- Real-valued sparse recovery: restricted singular value, beta-min separation,
and bounded observation noise imply exact decoding. -/
theorem realSparse_boundedNoise_exact
    (design : Parameter →ₗ[ℝ] Observation)
    (admissible differenceClass : Parameter → Prop)
    (alpha betaMin radius : ℝ)
    (alphaNonnegative : 0 ≤ alpha)
    (lowerBound : RestrictedNormLowerBound design differenceClass alpha)
    (differenceClosed : DifferenceClosed admissible differenceClass)
    (betaSeparated :
      ∀ ⦃first second⦄,
        admissible first → admissible second → first ≠ second →
        betaMin ≤ dist first second)
    (noiseMargin : 2 * radius < alpha * betaMin)
    (decoder : Observation → Parameter)
    (observed : Observation) (truth : Parameter)
    (truthAdmissible : admissible truth)
    (decodedAdmissible : admissible (decoder observed))
    (truthClose : dist observed (design truth) ≤ radius)
    (decoderConsistent : dist observed (design (decoder observed)) ≤ radius) :
    decoder observed = truth := by
  apply bounded_noise_sparse_decoder_exact design admissible alpha radius
    (restrictedNormLowerBound_yields_pairGeometry design admissible
      differenceClass alpha lowerBound differenceClosed)
  · intro first second firstAdmissible secondAdmissible distinct
    exact noiseMargin.trans_le
      (mul_le_mul_of_nonneg_left
        (betaSeparated firstAdmissible secondAdmissible distinct)
        alphaNonnegative)
  · exact truthAdmissible
  · exact decodedAdmissible
  · exact truthClose
  · exact decoderConsistent

/-- When the declared lower factor is nonpositive, even the zero design
satisfies the restricted inequality. -/
theorem zeroDesign_satisfies_nonpositive_restrictedNormLowerBound
    (differenceClass : Parameter → Prop) (alpha : ℝ)
    (alphaNonpositive : alpha ≤ 0) :
    RestrictedNormLowerBound
      (0 : Parameter →ₗ[ℝ] Observation) differenceClass alpha := by
  intro difference _
  have : alpha * ‖difference‖ ≤ 0 :=
    mul_nonpos_of_nonpos_of_nonneg alphaNonpositive (norm_nonneg difference)
  simpa using this

/-- No-go: a nonpositive restricted factor cannot certify injectivity; the zero
design is a countermodel for every declared difference class. -/
theorem nonpositive_restrictedFactor_allows_noninjective_design
    (differenceClass : Parameter → Prop) (alpha : ℝ)
    (alphaNonpositive : alpha ≤ 0)
    (first second : Parameter) (distinct : first ≠ second) :
    ∃ design : Parameter →ₗ[ℝ] Observation,
      RestrictedNormLowerBound design differenceClass alpha ∧
      ¬ Function.Injective design := by
  refine ⟨0,
    zeroDesign_satisfies_nonpositive_restrictedNormLowerBound
      differenceClass alpha alphaNonpositive, ?_⟩
  intro injectiveZero
  apply distinct
  apply injectiveZero
  simp

/-- RIP no-go: `delta ≥ 1` makes `1-delta ≤ 0`, so the lower RIP inequality
alone admits a completely uninformative zero design. -/
theorem ripDelta_ge_one_allows_zeroDesign
    (differenceClass : Parameter → Prop) (delta : ℝ)
    (deltaAtLeastOne : 1 ≤ delta)
    (first second : Parameter) (distinct : first ≠ second) :
    ∃ design : Parameter →ₗ[ℝ] Observation,
      RestrictedNormLowerBound design differenceClass (1 - delta) ∧
      ¬ Function.Injective design := by
  exact nonpositive_restrictedFactor_allows_noninjective_design
    differenceClass (1 - delta) (sub_nonpos.mpr deltaAtLeastOne)
    first second distinct

end RestrictedNorm

end OCKIndividuationMSpaceComposition
