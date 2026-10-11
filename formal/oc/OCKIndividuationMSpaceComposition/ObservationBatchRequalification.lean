import OCKIndividuationMSpaceComposition.BoundedRegressionSafety

namespace OCKIndividuationMSpaceComposition

/-!
Observation-batch requalification.

The positive result says that a completed negative-gain trigger can force the
next prediction back to its baseline, giving exactly zero excess loss on that
next block.  The obstruction result isolates the first unannounced shift: a
deterministic policy cannot satisfy opposite decision requirements in two
worlds whose available histories are equal.
-/

def requalifiedPrediction
    (trigger : Prop) [Decidable trigger] (baseline proposal : ℝ) : ℝ :=
  if trigger then baseline else proposal

theorem latestNegative_forces_baseline
    (latestCompletedGain baseline proposal : ℝ)
    (hnegative : latestCompletedGain < 0) :
    requalifiedPrediction (latestCompletedGain < 0) baseline proposal
      = baseline := by
  simp [requalifiedPrediction, hnegative]

theorem latestNegative_requalification_zero_excess
    (latestCompletedGain outcome baseline proposal : ℝ)
    (hnegative : latestCompletedGain < 0) :
    squaredLossExcess outcome baseline
      (requalifiedPrediction
        (latestCompletedGain < 0) baseline proposal) 1 = 0 := by
  rw [latestNegative_forces_baseline _ _ _ hnegative]
  apply squaredLossExcess_zero_of_zero_departure
  ring

theorem observational_aliasing_obstruction
    {Observation : Type}
    (policy : List Observation → Bool)
    (historyA historyB : List Observation)
    (requiredA requiredB : Bool)
    (hsame : historyA = historyB)
    (hopposite : requiredA ≠ requiredB) :
    ¬ (policy historyA = requiredA ∧ policy historyB = requiredB) := by
  intro hsatisfied
  apply hopposite
  calc
    requiredA = policy historyA := hsatisfied.1.symm
    _ = policy historyB := by rw [hsame]
    _ = requiredB := hsatisfied.2

theorem first_unannounced_shift_cannot_be_preempted_in_both_worlds
    {Observation : Type}
    (policy : List Observation → Bool)
    (sharedHistory : List Observation) :
    ¬ (policy sharedHistory = true ∧ policy sharedHistory = false) := by
  exact observational_aliasing_obstruction
    policy sharedHistory sharedHistory true false rfl (by decide)

end OCKIndividuationMSpaceComposition
