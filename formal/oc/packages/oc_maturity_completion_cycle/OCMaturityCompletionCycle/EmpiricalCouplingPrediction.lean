import OCMaturityCompletionCycle.CrossContextCoupling
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

/-!
# A falsifiable coupling-coordinate prediction

This module separates a mathematical implication from the empirical hypothesis
that activates it.  The implication is a standard strictly-proper-score
decomposition: within one fixed local-signature stratum, a pre-outcome binary
coupling coordinate with different conditional Bernoulli laws yields a strictly
positive, exactly quantified Brier-score advantage over every local-only
forecast.  The empirical claim that such a separation exists is not proved
here; it is frozen for a held-out test.

The module also binds the score result to the existing stitching vocabulary.
If the two coupling regimes have the same local signature but different future
probabilities, the local signature cannot exactly stitch the predictive target.
Adding the independently measured coupling coordinate restores exact stitching
for this two-regime family.
-/

namespace OCMaturityCompletionCycle

/-! ## Probability-valid parameters and Brier risk -/

/-- A rational number has the declared interpretation of a probability. -/
def IsProbability (value : ℚ) : Prop :=
  0 ≤ value ∧ value ≤ 1

/-- Population Brier risk of reporting `forecast` for a Bernoulli(`truth`) outcome. -/
def BernoulliBrierRisk (truth forecast : ℚ) : ℚ :=
  truth * (1 - forecast) ^ 2 + (1 - truth) * forecast ^ 2

/-- Exact strict-propriety decomposition for the Bernoulli Brier score. -/
theorem bernoulliBrierRisk_decomposition (truth forecast : ℚ) :
    BernoulliBrierRisk truth forecast =
      BernoulliBrierRisk truth truth + (forecast - truth) ^ 2 := by
  simp only [BernoulliBrierRisk]
  ring

/-- The local-only Bayes forecast after forgetting a binary coupling coordinate. -/
def LocalMixtureMean (weightHigh probabilityLow probabilityHigh : ℚ) : ℚ :=
  (1 - weightHigh) * probabilityLow + weightHigh * probabilityHigh

/-- Brier risk of one report shared by both coupling regimes. -/
def LocalOnlyBrierRisk
    (weightHigh probabilityLow probabilityHigh forecast : ℚ) : ℚ :=
  (1 - weightHigh) * BernoulliBrierRisk probabilityLow forecast +
    weightHigh * BernoulliBrierRisk probabilityHigh forecast

/-- Brier risk when the coupling coordinate selects the true conditional report. -/
def CouplingAwareBrierRisk
    (weightHigh probabilityLow probabilityHigh : ℚ) : ℚ :=
  (1 - weightHigh) * BernoulliBrierRisk probabilityLow probabilityLow +
    weightHigh * BernoulliBrierRisk probabilityHigh probabilityHigh

/-- Irreducible Brier gain carried by a nondegenerate binary coupling coordinate. -/
def CouplingBrierGain
    (weightHigh probabilityLow probabilityHigh : ℚ) : ℚ :=
  weightHigh * (1 - weightHigh) *
    (probabilityHigh - probabilityLow) ^ 2

/--
Every local-only report pays its own calibration error plus the exact coupling
gain.  This equality does not assume probability bounds; those bounds enter the
scientific interpretation and the strict prediction below.
-/
theorem localOnlyBrierRisk_exact_decomposition
    (weightHigh probabilityLow probabilityHigh forecast : ℚ) :
    LocalOnlyBrierRisk weightHigh probabilityLow probabilityHigh forecast =
      CouplingAwareBrierRisk weightHigh probabilityLow probabilityHigh +
        (forecast - LocalMixtureMean weightHigh probabilityLow probabilityHigh) ^ 2 +
        CouplingBrierGain weightHigh probabilityLow probabilityHigh := by
  simp only [LocalOnlyBrierRisk, CouplingAwareBrierRisk, LocalMixtureMean,
    CouplingBrierGain, BernoulliBrierRisk]
  ring

/-- The best local-only report has exactly the coupling-information penalty. -/
theorem bestLocalOnlyBrierRisk_gap
    (weightHigh probabilityLow probabilityHigh : ℚ) :
    LocalOnlyBrierRisk weightHigh probabilityLow probabilityHigh
        (LocalMixtureMean weightHigh probabilityLow probabilityHigh) =
      CouplingAwareBrierRisk weightHigh probabilityLow probabilityHigh +
        CouplingBrierGain weightHigh probabilityLow probabilityHigh := by
  rw [localOnlyBrierRisk_exact_decomposition]
  ring

/--
The frozen quantitative prediction.  When both regimes occur and their future
laws differ, the coupling-aware forecast strictly beats every forecast that is
constant within the local-signature stratum.
-/
theorem measurableCoupling_strictlyImprovesBrier
    (weightHigh probabilityLow probabilityHigh forecast : ℚ)
    (_probabilityLowValid : IsProbability probabilityLow)
    (_probabilityHighValid : IsProbability probabilityHigh)
    (weightPositive : 0 < weightHigh)
    (weightBelowOne : weightHigh < 1)
    (conditionalSeparation : probabilityLow ≠ probabilityHigh) :
    CouplingAwareBrierRisk weightHigh probabilityLow probabilityHigh <
      LocalOnlyBrierRisk weightHigh probabilityLow probabilityHigh forecast := by
  rw [localOnlyBrierRisk_exact_decomposition]
  have remainingWeightPositive : 0 < 1 - weightHigh := sub_pos.mpr weightBelowOne
  have probabilityDifferenceNonzero : probabilityHigh - probabilityLow ≠ 0 :=
    sub_ne_zero.mpr conditionalSeparation.symm
  have squaredDifferencePositive :
      0 < (probabilityHigh - probabilityLow) ^ 2 :=
    sq_pos_of_ne_zero probabilityDifferenceNonzero
  have gainPositive :
      0 < CouplingBrierGain weightHigh probabilityLow probabilityHigh := by
    exact mul_pos (mul_pos weightPositive remainingWeightPositive)
      squaredDifferencePositive
  have calibrationNonnegative :
      0 ≤ (forecast -
        LocalMixtureMean weightHigh probabilityLow probabilityHigh) ^ 2 :=
    sq_nonneg _
  linarith

/-! ## Exact stitching obstruction and repair -/

/-- Conditional future probability selected by the measured coupling regime. -/
def TwoRegimeFutureProbability
    (probabilityLow probabilityHigh : ℚ) : Bool → ℚ
  | false => probabilityLow
  | true => probabilityHigh

/-- The incumbent local signature deliberately omits the coupling coordinate. -/
def CouplingBlindLocalSignature : Bool → Unit := fun _ => ()

/-- The repaired signature adds exactly one pre-outcome coupling coordinate. -/
def CouplingAugmentedSignature : Bool → Unit × Bool := fun regime => ((), regime)

/-- Distinct conditional laws are an exact local-signature stitching obstruction. -/
theorem couplingBlindSignature_no_exactPredictiveStitcher
    (probabilityLow probabilityHigh : ℚ)
    (conditionalSeparation : probabilityLow ≠ probabilityHigh) :
    ¬ ExactLocalTargetStitcher CouplingBlindLocalSignature
      (TwoRegimeFutureProbability probabilityLow probabilityHigh) := by
  rw [exactLocalTargetStitcher_iff_kernelInclusion]
  intro included
  have impossible := included (source := false) (target := true) rfl
  exact conditionalSeparation impossible

/-- The independently measured coupling coordinate restores exact target stitching. -/
theorem couplingAugmentedSignature_restores_exactPredictiveStitching
    (probabilityLow probabilityHigh : ℚ) :
    ExactLocalTargetStitcher CouplingAugmentedSignature
      (TwoRegimeFutureProbability probabilityLow probabilityHigh) := by
  rw [exactLocalTargetStitcher_iff_kernelInclusion]
  intro first second sameSignature
  have sameRegime : first = second := congrArg Prod.snd sameSignature
  exact congrArg (TwoRegimeFutureProbability probabilityLow probabilityHigh)
    sameRegime

/--
One scoped theorem joins the formal obstruction, its typed repair, and the
quantitative score prediction.  Its empirical premise is the conditional-law
separation; no formal proof may manufacture that premise for a real dataset.
-/
theorem stitchingObstruction_yields_strictBrierPrediction
    (weightHigh probabilityLow probabilityHigh : ℚ)
    (probabilityLowValid : IsProbability probabilityLow)
    (probabilityHighValid : IsProbability probabilityHigh)
    (weightPositive : 0 < weightHigh)
    (weightBelowOne : weightHigh < 1)
    (conditionalSeparation : probabilityLow ≠ probabilityHigh) :
    (¬ ExactLocalTargetStitcher CouplingBlindLocalSignature
      (TwoRegimeFutureProbability probabilityLow probabilityHigh)) ∧
    ExactLocalTargetStitcher CouplingAugmentedSignature
      (TwoRegimeFutureProbability probabilityLow probabilityHigh) ∧
    ∀ forecast,
      CouplingAwareBrierRisk weightHigh probabilityLow probabilityHigh <
        LocalOnlyBrierRisk weightHigh probabilityLow probabilityHigh forecast := by
  refine ⟨couplingBlindSignature_no_exactPredictiveStitcher
      probabilityLow probabilityHigh conditionalSeparation,
    couplingAugmentedSignature_restores_exactPredictiveStitching
      probabilityLow probabilityHigh, ?_⟩
  intro forecast
  exact measurableCoupling_strictlyImprovesBrier
    weightHigh probabilityLow probabilityHigh forecast
    probabilityLowValid probabilityHighValid weightPositive weightBelowOne
    conditionalSeparation

/-! ## Scoped finite canaries -/

/-- A concrete, nondegenerate population: equal regime weights and 1/4 versus 3/4. -/
theorem quarter_threeQuarter_exactBrierPrediction :
    LocalMixtureMean (1 / 2 : ℚ) (1 / 4) (3 / 4) = 1 / 2 ∧
    CouplingBrierGain (1 / 2 : ℚ) (1 / 4) (3 / 4) = 1 / 16 ∧
    CouplingAwareBrierRisk (1 / 2 : ℚ) (1 / 4) (3 / 4) = 3 / 16 ∧
    LocalOnlyBrierRisk (1 / 2 : ℚ) (1 / 4) (3 / 4) (1 / 2) = 1 / 4 := by
  norm_num [LocalMixtureMean, CouplingBrierGain, CouplingAwareBrierRisk,
    LocalOnlyBrierRisk, BernoulliBrierRisk]

/--
The directional edge-adjudication fixture frozen for the physical test: a clear
regime has probability one, an ambiguous two-matching regime has probability
one half, and equal regime prevalence produces an exact Brier gain of 1/16.
The numbers are a scoped canary, not asserted values for an unseen dataset.
-/
theorem clear_ambiguous_exactBrierPrediction :
    LocalMixtureMean (1 / 2 : ℚ) 1 (1 / 2) = 3 / 4 ∧
    CouplingBrierGain (1 / 2 : ℚ) 1 (1 / 2) = 1 / 16 ∧
    CouplingAwareBrierRisk (1 / 2 : ℚ) 1 (1 / 2) = 1 / 8 ∧
    LocalOnlyBrierRisk (1 / 2 : ℚ) 1 (1 / 2) (3 / 4) = 3 / 16 := by
  norm_num [LocalMixtureMean, CouplingBrierGain, CouplingAwareBrierRisk,
    LocalOnlyBrierRisk, BernoulliBrierRisk]

/-- If the conditional laws coincide, the coupling coordinate has zero Brier value. -/
theorem noConditionalSeparation_noBrierGain
    (weightHigh probability : ℚ) :
    CouplingBrierGain weightHigh probability probability = 0 ∧
      LocalOnlyBrierRisk weightHigh probability probability probability =
        CouplingAwareBrierRisk weightHigh probability probability := by
  constructor <;>
    simp [CouplingBrierGain, LocalOnlyBrierRisk, CouplingAwareBrierRisk]

/-- If only one regime occurs, the proposed coupling contrast is untestable and has zero gain. -/
theorem degenerateRegimeWeight_noBrierGain
    (probabilityLow probabilityHigh : ℚ) :
    CouplingBrierGain 0 probabilityLow probabilityHigh = 0 ∧
      CouplingBrierGain 1 probabilityLow probabilityHigh = 0 := by
  simp [CouplingBrierGain]

end OCMaturityCompletionCycle
