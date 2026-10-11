import OCKIndividuationMSpaceComposition.FiniteObservationRefinementBudget

namespace OCKIndividuationMSpaceComposition

/-!
# Finite alias-challenge risk

`observationCollisionPairCount` measures how many ordered pairs of registered
worlds remain task-relevantly aliased.  This module turns that structural count
into an algorithm-independent numerical prediction.

The evaluation distribution is explicit: draw an ordered collision pair
uniformly and then draw one of its two endpoints uniformly.  Every predictor
using only the aliased observation has zero-one error at least `1/2` on this
challenge distribution.  Thus the collision count determines whether the
challenge is nonempty, while the half-risk floor determines what no learner can
beat without acquiring information that separates the aliases.
-/

universe uWorld uObservation uOutcome

/-- Natural-valued zero-one error for exact finite counting. -/
def FiniteZeroOneError
    {Outcome : Type uOutcome} [DecidableEq Outcome]
    (predicted actual : Outcome) : Nat :=
  if predicted = actual then 0 else 1

/-- Every task-relevant collision forces at least one endpoint error for any
predictor that factors through the aliased observation. -/
theorem collision_pair_endpoint_error_count_ge_one
    {World : Type uWorld} {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (predict : Observation → Outcome)
    (pair : ObservationCollisionPair observe target) :
    1 ≤ FiniteZeroOneError (predict (observe pair.1.1)) (target pair.1.1) +
      FiniteZeroOneError (predict (observe pair.1.2)) (target pair.1.2) := by
  by_cases firstCorrect : predict (observe pair.1.1) = target pair.1.1
  · have secondWrong : predict (observe pair.1.2) ≠ target pair.1.2 := by
      intro secondCorrect
      apply pair.2.2.2
      calc
        target pair.1.1 = predict (observe pair.1.1) := firstCorrect.symm
        _ = predict (observe pair.1.2) := by rw [pair.2.2.1]
        _ = target pair.1.2 := secondCorrect
    simp [FiniteZeroOneError, firstCorrect, secondWrong]
  · simp [FiniteZeroOneError, firstCorrect]

/-- Sum of endpoint errors over every ordered collision pair. -/
noncomputable def collisionChallengeTotalError
    {World : Type uWorld} {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Observation]
    [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (predict : Observation → Outcome) : Nat := by
  classical
  letI : Fintype (ObservationCollisionPair observe target) :=
    observationCollisionPairFintype observe target
  exact ∑ pair : ObservationCollisionPair observe target,
    (FiniteZeroOneError (predict (observe pair.1.1)) (target pair.1.1) +
      FiniteZeroOneError (predict (observe pair.1.2)) (target pair.1.2))

/-- General finite no-go: total endpoint errors are at least the number of
ordered task-relevant collision pairs. -/
theorem collision_challenge_total_error_ge_collision_count
    {World : Type uWorld} {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Observation]
    [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (predict : Observation → Outcome) :
    observationCollisionPairCount observe target ≤
      collisionChallengeTotalError observe target predict := by
  classical
  letI : Fintype (ObservationCollisionPair observe target) :=
    observationCollisionPairFintype observe target
  change Fintype.card (ObservationCollisionPair observe target) ≤
    ∑ pair : ObservationCollisionPair observe target,
      (FiniteZeroOneError (predict (observe pair.1.1)) (target pair.1.1) +
        FiniteZeroOneError (predict (observe pair.1.2)) (target pair.1.2))
  calc
    Fintype.card (ObservationCollisionPair observe target) =
        ∑ _pair : ObservationCollisionPair observe target, 1 := by simp
    _ ≤ ∑ pair : ObservationCollisionPair observe target,
        (FiniteZeroOneError (predict (observe pair.1.1)) (target pair.1.1) +
          FiniteZeroOneError (predict (observe pair.1.2)) (target pair.1.2)) := by
      exact Finset.sum_le_sum fun pair _ =>
        collision_pair_endpoint_error_count_ge_one observe target predict pair

/-- Zero-one error rate on the explicit collision-pair challenge
distribution.  It is zero only when the challenge set is empty; otherwise it
is the endpoint-error sum divided by twice the collision count. -/
noncomputable def collisionChallengeErrorRate
    {World : Type uWorld} {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Observation]
    [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (predict : Observation → Outcome) : ℝ :=
  if observationCollisionPairCount observe target = 0 then 0
  else
    (collisionChallengeTotalError observe target predict : ℝ) /
      (2 * observationCollisionPairCount observe target : ℝ)

/-- **Sharp universal finite alias floor.** Whenever the registered collision
challenge is nonempty, every observation-only deterministic predictor has
challenge error at least `1/2`. -/
theorem nonempty_collision_challenge_error_rate_ge_half
    {World : Type uWorld} {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Observation]
    [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (predict : Observation → Outcome)
    (positive : 0 < observationCollisionPairCount observe target) :
    (1 : ℝ) / 2 ≤ collisionChallengeErrorRate observe target predict := by
  have countNonzero : observationCollisionPairCount observe target ≠ 0 :=
    Nat.ne_of_gt positive
  rw [collisionChallengeErrorRate, if_neg countNonzero]
  have totalLower :=
    collision_challenge_total_error_ge_collision_count observe target predict
  have totalLowerReal :
      (observationCollisionPairCount observe target : ℝ) ≤
        (collisionChallengeTotalError observe target predict : ℝ) := by
    exact_mod_cast totalLower
  have countPositiveReal :
      (0 : ℝ) < observationCollisionPairCount observe target := by
    exact_mod_cast positive
  apply (le_div_iff₀ (mul_pos (by norm_num) countPositiveReal)).2
  nlinarith

/-- A refinement's normalized structural resolution score. -/
noncomputable def collisionResolutionFraction (coarseCount fineCount : ℝ) : ℝ :=
  1 - fineCount / coarseCount

/-- The normalized structural resolution score lies in `[0,1]` whenever a
positive coarse budget is reduced (or preserved) by a refinement. -/
theorem collision_resolution_fraction_mem_unit_interval
    (coarseCount fineCount : ℝ)
    (coarsePositive : 0 < coarseCount)
    (fineNonnegative : 0 ≤ fineCount)
    (fineNoLarger : fineCount ≤ coarseCount) :
    0 ≤ collisionResolutionFraction coarseCount fineCount ∧
      collisionResolutionFraction coarseCount fineCount ≤ 1 := by
  constructor
  · unfold collisionResolutionFraction
    have ratioAtMostOne : fineCount / coarseCount ≤ 1 :=
      (div_le_one coarsePositive).2 fineNoLarger
    linarith
  · unfold collisionResolutionFraction
    have ratioNonnegative : 0 ≤ fineCount / coarseCount :=
      div_nonneg fineNonnegative (le_of_lt coarsePositive)
    linarith

/-- Direct operational corollary: the measured collision-resolution fraction
of every finite observation refinement lies in `[0,1]`. -/
theorem refinement_collision_resolution_fraction_mem_unit_interval
    {World : Type uWorld} {Coarse Fine : Type*} {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Coarse] [DecidableEq Fine]
    [DecidableEq Outcome]
    (coarse : World → Coarse) (fine : World → Fine) (target : World → Outcome)
    (refines : ObservationRefines coarse fine)
    (positive : 0 < observationCollisionPairCount coarse target) :
    0 ≤ collisionResolutionFraction
        (observationCollisionPairCount coarse target : ℝ)
        (observationCollisionPairCount fine target : ℝ) ∧
      collisionResolutionFraction
        (observationCollisionPairCount coarse target : ℝ)
        (observationCollisionPairCount fine target : ℝ) ≤ 1 := by
  apply collision_resolution_fraction_mem_unit_interval
  · exact_mod_cast positive
  · positivity
  · exact_mod_cast collision_pair_budget_monotone_under_refinement
      coarse fine target refines

/-- Deterministic feature engineering has exactly zero normalized structural
resolution whenever the raw collision challenge is nonempty. -/
theorem derived_feature_collision_resolution_fraction_eq_zero
    {World : Type uWorld} {Raw Derived : Type*} {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Raw] [DecidableEq Derived]
    [DecidableEq Outcome]
    (raw : World → Raw) (derive : Raw → Derived) (target : World → Outcome)
    (positive : 0 < observationCollisionPairCount raw target) :
    collisionResolutionFraction
        (observationCollisionPairCount raw target : ℝ)
        (observationCollisionPairCount
          (fun world => (raw world, derive (raw world))) target : ℝ) = 0 := by
  rw [derived_feature_preserves_collision_pair_budget raw derive target]
  unfold collisionResolutionFraction
  have nonzero : (observationCollisionPairCount raw target : ℝ) ≠ 0 := by
    exact_mod_cast Nat.ne_of_gt positive
  rw [div_self nonzero]
  norm_num

end OCKIndividuationMSpaceComposition
