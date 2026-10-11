import OCKIndividuationMSpaceComposition.TemporalDependenceEnvelope

namespace OCKIndividuationMSpaceComposition

/-!
## Hierarchical pooling: exact reductions, controlled bias and collision limits

A population partition saves observations only when the prediction target
factors through the registered group map, or when the resulting approximation
bias is explicitly bounded.  The results below make both cases quantitative.
They also prove the sharp two-point obstruction: collapsing two targets whose
separation is `gap` forces at least `gap / 2` error at one of them.
-/

/-- The target is exactly constant on every fiber of a registered grouping. -/
def OutcomeFactorsThrough
    {Cell Group Outcome : Type*}
    (group : Cell → Group) (outcome : Cell → Outcome) : Prop :=
  ∃ groupOutcome : Group → Outcome, ∀ cell, outcome cell = groupOutcome (group cell)

/-- An exact factorization supplies a group-level predictor that is exact on
every cell, including cells not separately estimated. -/
theorem exact_group_factorization_predicts_every_cell
    {Cell Group Outcome : Type*}
    (group : Cell → Group) (outcome : Cell → Outcome)
    (factors : OutcomeFactorsThrough group outcome) :
    ∃ groupOutcome : Group → Outcome,
      ∀ cell, groupOutcome (group cell) = outcome cell := by
  rcases factors with ⟨groupOutcome, exact⟩
  exact ⟨groupOutcome, fun cell => (exact cell).symm⟩

/-- If two cells collide under the grouping but have different targets, exact
group factorization is impossible. -/
theorem group_collision_refutes_exact_factorization
    {Cell Group Outcome : Type*}
    (group : Cell → Group) (outcome : Cell → Outcome)
    (first second : Cell)
    (sameGroup : group first = group second)
    (differentOutcome : outcome first ≠ outcome second) :
    ¬ OutcomeFactorsThrough group outcome := by
  rintro ⟨groupOutcome, exact⟩
  apply differentOutcome
  calc
    outcome first = groupOutcome (group first) := exact first
    _ = groupOutcome (group second) := by rw [sameGroup]
    _ = outcome second := (exact second).symm

/-- Approximation bias and estimation error add.  This is the basic error
accounting law for every controlled pooling contract. -/
theorem pooled_bias_and_estimation_error_add
    {Hypothesis : Type*}
    (trueScore pooledScore estimatedScore : Hypothesis → ℝ)
    (hypothesis : Hypothesis) (bias estimationError : ℝ)
    (poolingBias : |pooledScore hypothesis - trueScore hypothesis| ≤ bias)
    (estimationBound :
      |estimatedScore hypothesis - pooledScore hypothesis| ≤ estimationError) :
    |estimatedScore hypothesis - trueScore hypothesis| ≤
      estimationError + bias := by
  calc
    |estimatedScore hypothesis - trueScore hypothesis| =
        |(estimatedScore hypothesis - pooledScore hypothesis) +
          (pooledScore hypothesis - trueScore hypothesis)| := by ring_nf
    _ ≤ |estimatedScore hypothesis - pooledScore hypothesis| +
        |pooledScore hypothesis - trueScore hypothesis| := abs_add_le _ _
    _ ≤ estimationError + bias := add_le_add estimationBound poolingBias

/-- A total-error target remains valid when the estimation budget is the
residual `target - bias`. -/
theorem residual_estimation_budget_guarantees_total_target
    {Hypothesis : Type*}
    (trueScore pooledScore estimatedScore : Hypothesis → ℝ)
    (hypothesis : Hypothesis) (bias target : ℝ)
    (poolingBias : |pooledScore hypothesis - trueScore hypothesis| ≤ bias)
    (estimationBound :
      |estimatedScore hypothesis - pooledScore hypothesis| ≤ target - bias) :
    |estimatedScore hypothesis - trueScore hypothesis| ≤ target := by
  have combined := pooled_bias_and_estimation_error_add
    trueScore pooledScore estimatedScore hypothesis bias (target - bias)
    poolingBias estimationBound
  linarith

/-- Pairwise model selection is stable when the true margin exceeds twice the
sum of pooling bias and estimation error. -/
theorem pooled_argmax_pair_stable
    {Hypothesis : Type*}
    (trueScore pooledScore estimatedScore : Hypothesis → ℝ)
    (best competitor : Hypothesis) (bias estimationError : ℝ)
    (bestBias : |pooledScore best - trueScore best| ≤ bias)
    (competitorBias : |pooledScore competitor - trueScore competitor| ≤ bias)
    (bestEstimation :
      |estimatedScore best - pooledScore best| ≤ estimationError)
    (competitorEstimation :
      |estimatedScore competitor - pooledScore competitor| ≤ estimationError)
    (margin :
      trueScore competitor + 2 * (estimationError + bias) < trueScore best) :
    estimatedScore competitor < estimatedScore best := by
  exact argmax_pair_stable_of_uniform_error
    trueScore estimatedScore best competitor (estimationError + bias)
    (pooled_bias_and_estimation_error_add trueScore pooledScore estimatedScore
      best bias estimationError bestBias bestEstimation)
    (pooled_bias_and_estimation_error_add trueScore pooledScore estimatedScore
      competitor bias estimationError competitorBias competitorEstimation)
    margin

/-- Sharp two-point minimax lower bound for a scalar predictor shared by two
collapsed cells. -/
theorem pooled_scalar_collision_minimax_lower_bound
    (first second pooled gap : ℝ)
    (separation : gap ≤ |first - second|) :
    gap / 2 ≤ max |pooled - first| |pooled - second| := by
  have triangle :
      |first - second| ≤ |pooled - first| + |pooled - second| := by
    calc
      |first - second| = |(first - pooled) + (pooled - second)| := by ring_nf
      _ ≤ |first - pooled| + |pooled - second| := abs_add_le _ _
      _ = |pooled - first| + |pooled - second| := by rw [abs_sub_comm first pooled]
  have firstLe : |pooled - first| ≤ max |pooled - first| |pooled - second| :=
    le_max_left _ _
  have secondLe : |pooled - second| ≤ max |pooled - first| |pooled - second| :=
    le_max_right _ _
  linarith

/-- No shared prediction can keep both errors below a target strictly smaller
than half the registered within-group separation. -/
theorem no_pooled_scalar_reaches_target_below_half_gap
    (first second pooled gap target : ℝ)
    (separation : gap ≤ |first - second|)
    (targetBelowHalfGap : target < gap / 2) :
    ¬ (|pooled - first| ≤ target ∧ |pooled - second| ≤ target) := by
  intro both
  have lower := pooled_scalar_collision_minimax_lower_bound
    first second pooled gap separation
  have upper : max |pooled - first| |pooled - second| ≤ target :=
    max_le both.1 both.2
  linarith

/-- Number of group/outcome hypotheses in the elementary factored population
surface. -/
def pooledHypothesisCount (groupCount outcomeClassCount : ℕ) : ℕ :=
  groupCount * outcomeClassCount

/-- End-to-end sample bridge: after a valid pooling contract has reduced the
hypothesis family to group/outcome pairs, the ordinary dependence-corrected
population quota applies to that reduced family. -/
theorem pooled_designEffect_threshold_guarantees_population_budget
    (groupCount outcomeClassCount : ℕ)
    (epsilon delta raw designEffect : ℝ)
    (groupCountPositive : 0 < groupCount)
    (outcomeClassCountPositive : 0 < outcomeClassCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (designEffectPositive : 0 < designEffect)
    (enoughRaw :
      designEffect * populationRequiredEffectiveObservations
          (pooledHypothesisCount groupCount outcomeClassCount)
          epsilon delta ≤ raw) :
    designEffectPopulationBudget
        (pooledHypothesisCount groupCount outcomeClassCount)
        raw designEffect epsilon ≤ delta := by
  apply designEffect_raw_threshold_guarantees_population_budget
    (pooledHypothesisCount groupCount outcomeClassCount)
    epsilon delta raw designEffect
  · exact Nat.mul_pos groupCountPositive outcomeClassCountPositive
  · exact epsilonPositive
  · exact deltaPositive
  · exact designEffectPositive
  · exact enoughRaw

end OCKIndividuationMSpaceComposition
