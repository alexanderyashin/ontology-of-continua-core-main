import OCKIndividuationMSpaceComposition.BoundedNoiseModelCompetition
import OCKIndividuationMSpaceComposition.GovernanceBarrierHazard
import OCKIndividuationMSpaceComposition.TimeVaryingCoupledPropagation

namespace OCKIndividuationMSpaceComposition

universe uSmall uLarge

/-!
# Odds, proportional-hazard and interaction models under bounded error

This module instantiates the exact `2 * epsilon` model-competition boundary for
three response families used by domain projections.  The mature probability and
survival algebra is reused; the new result is the exact experimental-design
contract that says which registered coordinates make parameters distinguishable.
-/

/-! ## Rational odds-to-probability adapter and saturation -/

/-- Probability represented by nonnegative rational odds. -/
def oddsProbability (odds : ℚ) : ℚ := odds / (1 + odds)

theorem oddsProbability_nonnegative
    (odds : ℚ) (nonnegative : 0 ≤ odds) :
    0 ≤ oddsProbability odds := by
  unfold oddsProbability
  exact div_nonneg nonnegative (by linarith)

theorem oddsProbability_lt_one
    (odds : ℚ) (nonnegative : 0 ≤ odds) :
    oddsProbability odds < 1 := by
  unfold oddsProbability
  apply (div_lt_one (by linarith)).2
  linarith

theorem oddsProbability_le_one
    (odds : ℚ) (nonnegative : 0 ≤ odds) :
    oddsProbability odds ≤ 1 :=
  le_of_lt (oddsProbability_lt_one odds nonnegative)

/-- Exact probability gap induced by two odds values. -/
theorem oddsProbability_sub_exact
    (first second : ℚ) (firstDomain : -1 < first)
    (secondDomain : -1 < second) :
    oddsProbability second - oddsProbability first =
      (second - first) / ((1 + first) * (1 + second)) := by
  unfold oddsProbability
  field_simp [ne_of_gt (by linarith : 0 < 1 + first),
    ne_of_gt (by linarith : 0 < 1 + second)]
  ring

theorem abs_oddsProbability_sub_exact
    (first second : ℚ) (firstDomain : -1 < first)
    (secondDomain : -1 < second) :
    |oddsProbability second - oddsProbability first| =
      |second - first| / ((1 + first) * (1 + second)) := by
  rw [oddsProbability_sub_exact first second firstDomain secondDomain,
    abs_div]
  have denominatorPositive : 0 < (1 + first) * (1 + second) :=
    mul_pos (by linarith) (by linarith)
  rw [abs_of_pos denominatorPositive]

/-- Odds are identifiable from their probabilities on the nonnegative domain. -/
theorem oddsProbability_injective_nonnegative
    {first second : ℚ} (firstNonnegative : 0 ≤ first)
    (secondNonnegative : 0 ≤ second)
    (equalProbability : oddsProbability first = oddsProbability second) :
    first = second := by
  have firstDomain : -1 < first := by linarith
  have secondDomain : -1 < second := by linarith
  have zeroGap : oddsProbability second - oddsProbability first = 0 := by
    rw [equalProbability]
    ring
  rw [oddsProbability_sub_exact first second firstDomain secondDomain] at zeroGap
  have denominatorNonzero : (1 + first) * (1 + second) ≠ 0 :=
    mul_ne_zero (ne_of_gt (by linarith)) (ne_of_gt (by linarith))
  exact (sub_eq_zero.mp
    ((div_eq_zero_iff).mp zeroGap |>.resolve_right denominatorNonzero)).symm

/-- The exact attenuation denominator grows at least quadratically above a floor. -/
theorem odds_saturation_denominator_lower_bound
    (lower first second : ℚ)
    (lowerNonnegative : 0 ≤ lower)
    (firstAbove : lower ≤ first) (secondAbove : lower ≤ second) :
    (1 + lower) ^ 2 ≤ (1 + first) * (1 + second) := by
  have firstFactor : 0 ≤ 1 + first := by linarith
  have lowerFactor : 0 ≤ 1 + lower := by linarith
  calc
    (1 + lower) ^ 2 = (1 + lower) * (1 + lower) := by ring
    _ ≤ (1 + first) * (1 + lower) :=
      mul_le_mul_of_nonneg_right (by linarith) lowerFactor
    _ ≤ (1 + first) * (1 + second) :=
      mul_le_mul_of_nonneg_left (by linarith) firstFactor

/-- Exact bounded-error separation test for two odds models at one coordinate. -/
theorem odds_models_separated_of_probability_gap
    (first second epsilon : ℚ)
    (gap : 2 * epsilon < |oddsProbability first - oddsProbability second|) :
    ModelsSeparatedBeyondError (fun odds : ℚ => fun _ : Unit => oddsProbability odds)
      first second epsilon := by
  exact ⟨(), gap⟩

/-! ## Proportional hazards as a declared domain adapter -/

/-- A proportional-hazard rate before any link or clipping operation. -/
def proportionalHazardRate (baseline multiplier : ℚ) : ℚ :=
  baseline * multiplier

theorem proportionalHazardRate_valid
    (baseline multiplier : ℚ)
    (baselineNonnegative : 0 ≤ baseline)
    (multiplierNonnegative : 0 ≤ multiplier)
    (bounded : baseline * multiplier ≤ 1) :
    0 ≤ proportionalHazardRate baseline multiplier ∧
      proportionalHazardRate baseline multiplier ≤ 1 := by
  exact ⟨mul_nonneg baselineNonnegative multiplierNonnegative, bounded⟩

theorem proportionalHazard_multiplier_gap_exact
    (baseline first second : ℚ) :
    |proportionalHazardRate baseline first -
        proportionalHazardRate baseline second| =
      |baseline| * |first - second| := by
  unfold proportionalHazardRate
  rw [← mul_sub, abs_mul]

theorem proportionalHazard_models_separated
    (baseline first second epsilon : ℚ)
    (gap : 2 * epsilon < |baseline| * |first - second|) :
    ModelsSeparatedBeyondError
      (fun multiplier : ℚ => fun _ : Unit =>
        proportionalHazardRate baseline multiplier)
      first second epsilon := by
  refine ⟨(), ?_⟩
  simpa [proportionalHazard_multiplier_gap_exact]

theorem proportionalHazard_constant_survival_exact
    (baseline multiplier : ℚ) (horizon : ℕ) :
    barrierSurvival
        (constantBarrierHazard (proportionalHazardRate baseline multiplier)) horizon =
      (1 - baseline * multiplier) ^ horizon := by
  simpa [proportionalHazardRate] using
    constantBarrierHazard_survival
      (proportionalHazardRate baseline multiplier) horizon

/-! ## Context and time interaction design -/

/-- Additive response plus a bilinear interaction coefficient. -/
def bilinearInteractionResponse
    (baseline firstSlope secondSlope interaction first second : ℚ) : ℚ :=
  baseline + firstSlope * first + secondSlope * second +
    interaction * first * second

/-- Context interaction is the bilinear family with context as the second axis. -/
abbrev contextInteractionResponse := bilinearInteractionResponse

/-- Time-varying interaction is the same family with time as the second axis. -/
abbrev timeInteractionResponse := bilinearInteractionResponse

theorem bilinearInteraction_parameter_gap_exact
    (baseline firstSlope secondSlope firstInteraction secondInteraction
      first second : ℚ) :
    |bilinearInteractionResponse baseline firstSlope secondSlope
        firstInteraction first second -
      bilinearInteractionResponse baseline firstSlope secondSlope
        secondInteraction first second| =
      |firstInteraction - secondInteraction| * |first| * |second| := by
  unfold bilinearInteractionResponse
  rw [show baseline + firstSlope * first + secondSlope * second +
        firstInteraction * first * second -
        (baseline + firstSlope * first + secondSlope * second +
          secondInteraction * first * second) =
        (firstInteraction - secondInteraction) * first * second by ring,
    abs_mul, abs_mul]

/-- A registered context/time coordinate separates two interaction parameters. -/
theorem bilinearInteraction_models_separated_at
    (baseline firstSlope secondSlope firstInteraction secondInteraction
      first second epsilon : ℚ)
    (gap : 2 * epsilon <
      |firstInteraction - secondInteraction| * |first| * |second|) :
    ModelsSeparatedBeyondError
      (fun interaction : ℚ => fun test : ℚ × ℚ =>
        bilinearInteractionResponse baseline firstSlope secondSlope
          interaction test.1 test.2)
      firstInteraction secondInteraction epsilon := by
  refine ⟨(first, second), ?_⟩
  simpa [bilinearInteraction_parameter_gap_exact]

/-- The normalized corner `(1,1)` exposes the entire interaction-coefficient gap. -/
theorem normalized_corner_separates_interactions
    (baseline firstSlope secondSlope firstInteraction secondInteraction
      epsilon : ℚ)
    (gap : 2 * epsilon < |firstInteraction - secondInteraction|) :
    ModelsSeparatedBeyondError
      (fun interaction : ℚ => fun test : ℚ × ℚ =>
        bilinearInteractionResponse baseline firstSlope secondSlope
          interaction test.1 test.2)
      firstInteraction secondInteraction epsilon := by
  apply bilinearInteraction_models_separated_at
    baseline firstSlope secondSlope firstInteraction secondInteraction 1 1 epsilon
  simpa using gap

/-- No normalized test can amplify a bilinear interaction beyond its coefficient. -/
theorem normalized_bilinear_signal_le_coefficient
    (interaction first second : ℚ)
    (firstBound : |first| ≤ 1) (secondBound : |second| ≤ 1) :
    |interaction * first * second| ≤ |interaction| := by
  rw [abs_mul, abs_mul]
  have interactionNonnegative : 0 ≤ |interaction| := abs_nonneg _
  have firstNonnegative : 0 ≤ |first| := abs_nonneg _
  calc
    |interaction| * |first| * |second| ≤
        |interaction| * |first| * 1 :=
      mul_le_mul_of_nonneg_left secondBound
        (mul_nonneg interactionNonnegative firstNonnegative)
    _ ≤ |interaction| * 1 * 1 := by
      gcongr
    _ = |interaction| := by ring

/--
If every registered coordinate kills the product, every interaction coefficient
has exactly the same signature; a common zero-error observation is explicit.
-/
theorem zero_product_design_cannot_identify_interaction
    {Test : Type*} (first second : Test → ℚ)
    (zeroProduct : ∀ test, first test * second test = 0)
    (baseline firstSlope secondSlope firstInteraction secondInteraction epsilon : ℚ)
    (epsilonNonnegative : 0 ≤ epsilon) :
    ∃ observed : Test → ℚ,
      ModelWithinLInfError
          (fun interaction : ℚ => fun test =>
            bilinearInteractionResponse baseline firstSlope secondSlope
              interaction (first test) (second test))
          firstInteraction observed epsilon ∧
      ModelWithinLInfError
          (fun interaction : ℚ => fun test =>
            bilinearInteractionResponse baseline firstSlope secondSlope
              interaction (first test) (second test))
          secondInteraction observed epsilon := by
  let observed : Test → ℚ := fun test =>
    bilinearInteractionResponse baseline firstSlope secondSlope
      firstInteraction (first test) (second test)
  refine ⟨observed, ?_, ?_⟩
  · intro test
    simp [observed]
    exact epsilonNonnegative
  · intro test
    have equalPredictions :
        bilinearInteractionResponse baseline firstSlope secondSlope
            firstInteraction (first test) (second test) =
          bilinearInteractionResponse baseline firstSlope secondSlope
            secondInteraction (first test) (second test) := by
      unfold bilinearInteractionResponse
      rw [show firstInteraction * first test * second test =
          firstInteraction * (first test * second test) by ring,
        show secondInteraction * first test * second test =
          secondInteraction * (first test * second test) by ring,
        zeroProduct]
      ring
    simp [observed, equalPredictions]
    exact epsilonNonnegative

/-! ## Registered-design refinement -/

/-- Adding registered coordinates preserves every already witnessed separation. -/
theorem design_refinement_preserves_separation
    {Model : Type*} {SmallTest : Type uSmall} {LargeTest : Type uLarge}
    (smallPredict : Model → SmallTest → ℚ)
    (largePredict : Model → LargeTest → ℚ)
    (embed : SmallTest → LargeTest)
    (preserves : ∀ model test,
      largePredict model (embed test) = smallPredict model test)
    (left right : Model) (epsilon : ℚ)
    (separated : ModelsSeparatedBeyondError smallPredict left right epsilon) :
    ModelsSeparatedBeyondError largePredict left right epsilon := by
  obtain ⟨test, gap⟩ := separated
  refine ⟨embed test, ?_⟩
  simpa [preserves left test, preserves right test] using gap

end OCKIndividuationMSpaceComposition
