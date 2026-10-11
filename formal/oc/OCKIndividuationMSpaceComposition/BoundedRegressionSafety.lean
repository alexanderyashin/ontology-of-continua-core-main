import OCKIndividuationMSpaceComposition.BudgetedPredictiveSafety

namespace OCKIndividuationMSpaceComposition

/-!
Squared-loss safety for continuous predictions.

The first theorem is the exact one-step excess-loss identity.  It yields a
no-go result on an unbounded outcome space: every nontrivial departure from the
fallback can be made to exceed any finite budget.  A declared outcome interval
restores a finite exact endpoint envelope.  This is the formal boundary needed
before the binary budgeted-safety wrapper can be adapted to hydraulic or other
continuous tasks.
-/

def squaredLossExcess
    (outcome baseline proposal mix : ℝ) : ℝ :=
  binarySquaredLoss outcome (baseline + mix * (proposal - baseline))
    - binarySquaredLoss outcome baseline

theorem squaredLossExcess_identity
    (outcome baseline proposal mix : ℝ) :
    squaredLossExcess outcome baseline proposal mix
      = (mix * (proposal - baseline)) ^ 2
        + 2 * (mix * (proposal - baseline)) * (baseline - outcome) := by
  dsimp [squaredLossExcess, binarySquaredLoss]
  ring

theorem unbounded_squaredLoss_no_finite_uniform_budget
    (baseline proposal mix budget : ℝ)
    (hnontrivial : mix * (proposal - baseline) ≠ 0) :
    ∃ outcome : ℝ, budget < squaredLossExcess outcome baseline proposal mix := by
  let departure := mix * (proposal - baseline)
  have hdeparture : departure ≠ 0 := by
    simpa [departure] using hnontrivial
  let outcome := baseline - (budget + 1 - departure ^ 2) / (2 * departure)
  refine ⟨outcome, ?_⟩
  have hexact : squaredLossExcess outcome baseline proposal mix = budget + 1 := by
    rw [squaredLossExcess_identity]
    change departure ^ 2 + 2 * departure * (baseline - outcome) = budget + 1
    dsimp [outcome]
    field_simp [hdeparture]
    ring
  rw [hexact]
  linarith

theorem squaredLossExcess_zero_of_zero_departure
    (outcome baseline proposal mix : ℝ)
    (hzero : mix * (proposal - baseline) = 0) :
    squaredLossExcess outcome baseline proposal mix = 0 := by
  rw [squaredLossExcess_identity, hzero]
  norm_num

theorem squaredLossExcess_le_endpointEnvelope
    (lower upper outcome baseline proposal mix : ℝ)
    (hlower : lower ≤ outcome)
    (hupper : outcome ≤ upper) :
    squaredLossExcess outcome baseline proposal mix
      ≤ (mix * (proposal - baseline)) ^ 2
        + 2 * max
          ((mix * (proposal - baseline)) * (baseline - lower))
          ((mix * (proposal - baseline)) * (baseline - upper)) := by
  let departure := mix * (proposal - baseline)
  have hproduct :
      departure * (baseline - outcome)
        ≤ max (departure * (baseline - lower))
          (departure * (baseline - upper)) := by
    rcases le_total 0 departure with hnonneg | hnonpos
    · have hbase : baseline - outcome ≤ baseline - lower := by linarith
      exact (mul_le_mul_of_nonneg_left hbase hnonneg).trans (le_max_left _ _)
    · have hbase : baseline - upper ≤ baseline - outcome := by linarith
      exact (mul_le_mul_of_nonpos_left hbase hnonpos).trans (le_max_right _ _)
  rw [squaredLossExcess_identity]
  change departure ^ 2 + 2 * departure * (baseline - outcome)
    ≤ departure ^ 2 + 2 * max
      (departure * (baseline - lower)) (departure * (baseline - upper))
  linarith

end OCKIndividuationMSpaceComposition
