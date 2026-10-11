import OCKIndividuationMSpaceComposition.ExperimentalEpistemology

namespace OCKIndividuationMSpaceComposition

/-!
Domain-neutral squared-loss safety envelope for a proposed predictive adapter.

`base + w * delta` is the deployed prediction.  The envelope is the largest
one-step excess squared loss over the two binary outcomes.  A risk-capital
account that pays this envelope therefore remains nonnegative after either
outcome.  This is a loss guarantee, not a claim that the proposal is accurate.
-/

def binarySquaredLoss (outcome prediction : ℝ) : ℝ :=
  (outcome - prediction) ^ 2

def binaryRiskEnvelope (base delta weight : ℝ) : ℝ :=
  weight ^ 2 * delta ^ 2
    + 2 * weight * max (base * delta) (-(1 - base) * delta)

theorem binary_excess_le_riskEnvelope
    (base delta weight outcome : ℝ)
    (hweight : 0 ≤ weight)
    (houtcome : outcome = 0 ∨ outcome = 1) :
    binarySquaredLoss outcome (base + weight * delta)
        - binarySquaredLoss outcome base
      ≤ binaryRiskEnvelope base delta weight := by
  rcases houtcome with rfl | rfl
  · have hmax : base * delta
        ≤ max (base * delta) (-(1 - base) * delta) := le_max_left _ _
    have hscale : 2 * weight * (base * delta)
        ≤ 2 * weight * max (base * delta) (-(1 - base) * delta) := by
      exact mul_le_mul_of_nonneg_left hmax (by positivity)
    dsimp [binarySquaredLoss, binaryRiskEnvelope]
    nlinarith [sq_nonneg (weight * delta)]
  · have hmax : -(1 - base) * delta
        ≤ max (base * delta) (-(1 - base) * delta) := le_max_right _ _
    have hscale : 2 * weight * (-(1 - base) * delta)
        ≤ 2 * weight * max (base * delta) (-(1 - base) * delta) := by
      exact mul_le_mul_of_nonneg_left hmax (by positivity)
    dsimp [binarySquaredLoss, binaryRiskEnvelope]
    nlinarith [sq_nonneg (weight * delta)]

theorem riskCapital_preserved_after_binary_reveal
    (capital base delta weight outcome : ℝ)
    (hweight : 0 ≤ weight)
    (houtcome : outcome = 0 ∨ outcome = 1)
    (hcertificate : binaryRiskEnvelope base delta weight ≤ capital) :
    0 ≤ capital
      + binarySquaredLoss outcome base
      - binarySquaredLoss outcome (base + weight * delta) := by
  have hexcess := binary_excess_le_riskEnvelope
    base delta weight outcome hweight houtcome
  linarith

theorem no_uniform_strict_binary_squaredLoss_improvement
    (base proposal : ℝ)
    (hbaseLower : 0 ≤ base)
    (hbaseUpper : base ≤ 1)
    (hproposalLower : 0 ≤ proposal)
    (hproposalUpper : proposal ≤ 1) :
    ¬ (binarySquaredLoss 0 proposal < binarySquaredLoss 0 base
      ∧ binarySquaredLoss 1 proposal < binarySquaredLoss 1 base) := by
  intro h
  rcases h with ⟨hzero, hone⟩
  dsimp [binarySquaredLoss] at hzero hone
  have hzero' : proposal ^ 2 < base ^ 2 := by
    simpa using hzero
  have hproposal_lt_base : proposal < base :=
    (sq_lt_sq₀ hproposalLower hbaseLower).mp hzero'
  have hOneProposal : 0 ≤ 1 - proposal := sub_nonneg.mpr hproposalUpper
  have hOneBase : 0 ≤ 1 - base := sub_nonneg.mpr hbaseUpper
  have hone' : 1 - proposal < 1 - base :=
    (sq_lt_sq₀ hOneProposal hOneBase).mp hone
  linarith

theorem registeredBlock_excessLoss_le_budget
    (budget realizedExcessLoss : ℝ)
    (haccount : 0 ≤ budget - realizedExcessLoss) :
    realizedExcessLoss ≤ budget := by
  linarith

end OCKIndividuationMSpaceComposition
