import OCMaturityCompletionCycle.CrossContextCoupling
import Mathlib.Tactic.Ring

/-!
# Binary coupling-coordinate prediction, proof revision 2

This additive revision preserves the frozen first attempt and corrects only its
formal proof surface.  The mathematical result is a finite binary conditional
Brier decomposition; it contains no measurability claim.  Whether a real
pre-outcome coordinate separates conditional laws remains an empirical
hypothesis and is not established here.
-/

namespace OCMaturityCompletionCycle

/-- A rational number lies in the closed unit interval. -/
def IsProbabilityR2 (value : ℚ) : Prop :=
  0 ≤ value ∧ value ≤ 1

/-- Population Brier risk of a rational Bernoulli forecast. -/
def BernoulliBrierRiskR2 (truth forecast : ℚ) : ℚ :=
  truth * (1 - forecast) ^ 2 + (1 - truth) * forecast ^ 2

/-- Exact finite Bernoulli Brier decomposition. -/
theorem bernoulliBrierRiskR2_decomposition (truth forecast : ℚ) :
    BernoulliBrierRiskR2 truth forecast =
      BernoulliBrierRiskR2 truth truth + (forecast - truth) ^ 2 := by
  simp only [BernoulliBrierRiskR2]
  ring

/-- Bayes report after forgetting a binary coupling coordinate. -/
def LocalMixtureMeanR2 (weightHigh probabilityLow probabilityHigh : ℚ) : ℚ :=
  (1 - weightHigh) * probabilityLow + weightHigh * probabilityHigh

/-- Brier risk of one report shared by both coupling regimes. -/
def LocalOnlyBrierRiskR2
    (weightHigh probabilityLow probabilityHigh forecast : ℚ) : ℚ :=
  (1 - weightHigh) * BernoulliBrierRiskR2 probabilityLow forecast +
    weightHigh * BernoulliBrierRiskR2 probabilityHigh forecast

/-- Brier risk of the two conditional Bayes reports. -/
def CouplingAwareBrierRiskR2
    (weightHigh probabilityLow probabilityHigh : ℚ) : ℚ :=
  (1 - weightHigh) * BernoulliBrierRiskR2 probabilityLow probabilityLow +
    weightHigh * BernoulliBrierRiskR2 probabilityHigh probabilityHigh

/-- Exact binary conditional-variance term. -/
def CouplingBrierGainR2
    (weightHigh probabilityLow probabilityHigh : ℚ) : ℚ :=
  weightHigh * (1 - weightHigh) *
    (probabilityHigh - probabilityLow) ^ 2

/-- Every shared report pays calibration error plus the exact coupling term. -/
theorem localOnlyBrierRiskR2_exact_decomposition
    (weightHigh probabilityLow probabilityHigh forecast : ℚ) :
    LocalOnlyBrierRiskR2 weightHigh probabilityLow probabilityHigh forecast =
      CouplingAwareBrierRiskR2 weightHigh probabilityLow probabilityHigh +
        (forecast - LocalMixtureMeanR2 weightHigh probabilityLow probabilityHigh) ^ 2 +
        CouplingBrierGainR2 weightHigh probabilityLow probabilityHigh := by
  simp only [LocalOnlyBrierRiskR2, CouplingAwareBrierRiskR2,
    LocalMixtureMeanR2, CouplingBrierGainR2, BernoulliBrierRiskR2]
  ring

/-- The best shared report pays exactly the conditional-variance term. -/
theorem bestLocalOnlyBrierRiskR2_gap
    (weightHigh probabilityLow probabilityHigh : ℚ) :
    LocalOnlyBrierRiskR2 weightHigh probabilityLow probabilityHigh
        (LocalMixtureMeanR2 weightHigh probabilityLow probabilityHigh) =
      CouplingAwareBrierRiskR2 weightHigh probabilityLow probabilityHigh +
        CouplingBrierGainR2 weightHigh probabilityLow probabilityHigh := by
  rw [localOnlyBrierRiskR2_exact_decomposition]
  ring

/--
If both regimes occur and their conditional laws differ, observing the binary
regime strictly improves population Brier risk over every regime-blind report.
-/
theorem binaryCoupling_strictlyImprovesBrier
    (weightHigh probabilityLow probabilityHigh forecast : ℚ)
    (weightPositive : 0 < weightHigh)
    (weightBelowOne : weightHigh < 1)
    (conditionalSeparation : probabilityLow ≠ probabilityHigh) :
    CouplingAwareBrierRiskR2 weightHigh probabilityLow probabilityHigh <
      LocalOnlyBrierRiskR2 weightHigh probabilityLow probabilityHigh forecast := by
  rw [localOnlyBrierRiskR2_exact_decomposition]
  have remainingWeightPositive : 0 < 1 - weightHigh := sub_pos.mpr weightBelowOne
  have probabilityDifferenceNonzero : probabilityHigh - probabilityLow ≠ 0 :=
    sub_ne_zero.mpr conditionalSeparation.symm
  have squaredDifferencePositive :
      0 < (probabilityHigh - probabilityLow) ^ 2 :=
    sq_pos_of_ne_zero probabilityDifferenceNonzero
  have gainPositive :
      0 < CouplingBrierGainR2 weightHigh probabilityLow probabilityHigh := by
    exact mul_pos (mul_pos weightPositive remainingWeightPositive)
      squaredDifferencePositive
  have calibrationNonnegative :
      0 ≤ (forecast -
        LocalMixtureMeanR2 weightHigh probabilityLow probabilityHigh) ^ 2 :=
    sq_nonneg _
  have baseWithCalibration :
      CouplingAwareBrierRiskR2 weightHigh probabilityLow probabilityHigh ≤
        CouplingAwareBrierRiskR2 weightHigh probabilityLow probabilityHigh +
          (forecast - LocalMixtureMeanR2
            weightHigh probabilityLow probabilityHigh) ^ 2 :=
    le_add_of_nonneg_right calibrationNonnegative
  calc
    CouplingAwareBrierRiskR2 weightHigh probabilityLow probabilityHigh <
        CouplingAwareBrierRiskR2 weightHigh probabilityLow probabilityHigh +
          CouplingBrierGainR2 weightHigh probabilityLow probabilityHigh :=
      lt_add_of_pos_right _ gainPositive
    _ ≤ CouplingAwareBrierRiskR2 weightHigh probabilityLow probabilityHigh +
          (forecast - LocalMixtureMeanR2 weightHigh probabilityLow probabilityHigh) ^ 2 +
          CouplingBrierGainR2 weightHigh probabilityLow probabilityHigh := by
      exact add_le_add_left baseWithCalibration _

/-- Conditional target selected by the binary coupling regime. -/
def TwoRegimeFutureProbabilityR2
    (probabilityLow probabilityHigh : ℚ) : Bool → ℚ
  | false => probabilityLow
  | true => probabilityHigh

/-- The incumbent signature forgets the binary regime. -/
def CouplingBlindLocalSignatureR2 : Bool → Unit := fun _ => ()

/-- The repaired signature retains the binary regime. -/
def CouplingAugmentedSignatureR2 : Bool → Unit × Bool :=
  fun regime => ((), regime)

/-- Distinct conditional laws obstruct an exact regime-blind stitcher. -/
theorem couplingBlindSignatureR2_no_exactPredictiveStitcher
    (probabilityLow probabilityHigh : ℚ)
    (conditionalSeparation : probabilityLow ≠ probabilityHigh) :
    ¬ ExactLocalTargetStitcher CouplingBlindLocalSignatureR2
      (TwoRegimeFutureProbabilityR2 probabilityLow probabilityHigh) := by
  rw [exactLocalTargetStitcher_iff_kernelInclusion]
  intro included
  have impossible := included (source := false) (target := true) rfl
  exact conditionalSeparation impossible

/-- Retaining the binary regime restores exact target stitching. -/
theorem couplingAugmentedSignatureR2_restores_exactPredictiveStitching
    (probabilityLow probabilityHigh : ℚ) :
    ExactLocalTargetStitcher CouplingAugmentedSignatureR2
      (TwoRegimeFutureProbabilityR2 probabilityLow probabilityHigh) := by
  rw [exactLocalTargetStitcher_iff_kernelInclusion]
  intro source target sameSignature
  have sameRegime : source = target := congrArg Prod.snd sameSignature
  exact congrArg (TwoRegimeFutureProbabilityR2 probabilityLow probabilityHigh)
    sameRegime

/--
Scoped conjunction of the obstruction, its typed repair, and the population
score implication.  Conditional separation remains an explicit premise.
-/
theorem stitchingObstructionR2_yields_strictBrierPrediction
    (weightHigh probabilityLow probabilityHigh : ℚ)
    (weightPositive : 0 < weightHigh)
    (weightBelowOne : weightHigh < 1)
    (conditionalSeparation : probabilityLow ≠ probabilityHigh) :
    (¬ ExactLocalTargetStitcher CouplingBlindLocalSignatureR2
      (TwoRegimeFutureProbabilityR2 probabilityLow probabilityHigh)) ∧
    ExactLocalTargetStitcher CouplingAugmentedSignatureR2
      (TwoRegimeFutureProbabilityR2 probabilityLow probabilityHigh) ∧
    ∀ forecast,
      CouplingAwareBrierRiskR2 weightHigh probabilityLow probabilityHigh <
        LocalOnlyBrierRiskR2 weightHigh probabilityLow probabilityHigh forecast := by
  refine ⟨couplingBlindSignatureR2_no_exactPredictiveStitcher
      probabilityLow probabilityHigh conditionalSeparation,
    couplingAugmentedSignatureR2_restores_exactPredictiveStitching
      probabilityLow probabilityHigh, ?_⟩
  intro forecast
  exact binaryCoupling_strictlyImprovesBrier
    weightHigh probabilityLow probabilityHigh forecast
    weightPositive weightBelowOne conditionalSeparation

/-- A nondegenerate quarter/three-quarter exact arithmetic canary. -/
theorem quarter_threeQuarter_exactBrierPredictionR2 :
    LocalMixtureMeanR2 (1 / 2 : ℚ) (1 / 4) (3 / 4) = 1 / 2 ∧
    CouplingBrierGainR2 (1 / 2 : ℚ) (1 / 4) (3 / 4) = 1 / 16 ∧
    CouplingAwareBrierRiskR2 (1 / 2 : ℚ) (1 / 4) (3 / 4) = 3 / 16 ∧
    LocalOnlyBrierRiskR2 (1 / 2 : ℚ) (1 / 4) (3 / 4) (1 / 2) = 1 / 4 := by
  norm_num [LocalMixtureMeanR2, CouplingBrierGainR2,
    CouplingAwareBrierRiskR2, LocalOnlyBrierRiskR2, BernoulliBrierRiskR2]

/-- A second exact arithmetic canary for unequal conditional risks. -/
theorem clear_ambiguous_exactBrierPredictionR2 :
    LocalMixtureMeanR2 (1 / 2 : ℚ) 1 (1 / 2) = 3 / 4 ∧
    CouplingBrierGainR2 (1 / 2 : ℚ) 1 (1 / 2) = 1 / 16 ∧
    CouplingAwareBrierRiskR2 (1 / 2 : ℚ) 1 (1 / 2) = 1 / 8 ∧
    LocalOnlyBrierRiskR2 (1 / 2 : ℚ) 1 (1 / 2) (3 / 4) = 3 / 16 := by
  norm_num [LocalMixtureMeanR2, CouplingBrierGainR2,
    CouplingAwareBrierRiskR2, LocalOnlyBrierRiskR2, BernoulliBrierRiskR2]

/-- Coincident conditional laws carry no binary coupling Brier gain. -/
theorem noConditionalSeparationR2_noBrierGain
    (weightHigh probability : ℚ) :
    CouplingBrierGainR2 weightHigh probability probability = 0 ∧
      LocalOnlyBrierRiskR2 weightHigh probability probability probability =
        CouplingAwareBrierRiskR2 weightHigh probability probability := by
  constructor <;>
    simp [CouplingBrierGainR2, LocalOnlyBrierRiskR2,
      CouplingAwareBrierRiskR2]

/-- A missing regime makes the binary contrast degenerate and its gain zero. -/
theorem degenerateRegimeWeightR2_noBrierGain
    (probabilityLow probabilityHigh : ℚ) :
    CouplingBrierGainR2 0 probabilityLow probabilityHigh = 0 ∧
      CouplingBrierGainR2 1 probabilityLow probabilityHigh = 0 := by
  simp [CouplingBrierGainR2]

end OCMaturityCompletionCycle
