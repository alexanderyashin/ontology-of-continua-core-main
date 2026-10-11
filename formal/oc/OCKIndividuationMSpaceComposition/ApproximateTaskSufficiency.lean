import OCKIndividuationMSpaceComposition.TaskConditionedOptics

namespace OCKIndividuationMSpaceComposition

/-!
# Approximate task sufficiency

This module uses a decision-deficiency contract: every decision available to a
coarse optic can be simulated by a decision on the fine optic with at most
`epsilon` additional task risk.  It is a task-relative risk statement, not a
metric on physical reality and not a causal-sufficiency claim.
-/

/-- One-way approximate decision simulation, in the direction coarse to fine. -/
def ApproximateDecisionSimulation
    {CoarseObservation FineObservation Action : Type*}
    (coarseRisk : (CoarseObservation → Action) → ℝ)
    (fineRisk : (FineObservation → Action) → ℝ)
    (epsilon : ℝ) : Prop :=
  ∀ coarseDecision, ∃ fineDecision,
    fineRisk fineDecision ≤ coarseRisk coarseDecision + epsilon

/-- An epsilon decision simulation yields an epsilon oracle-risk bound. -/
theorem oracle_risk_le_of_approximate_task_simulation
    {CoarseObservation FineObservation Action : Type*}
    (coarseRisk : (CoarseObservation → Action) → ℝ)
    (fineRisk : (FineObservation → Action) → ℝ)
    (epsilon : ℝ)
    (coarseOracle : OracleDecisionCertificate coarseRisk)
    (fineOracle : OracleDecisionCertificate fineRisk)
    (simulation : ApproximateDecisionSimulation coarseRisk fineRisk epsilon) :
    fineOracle.value ≤ coarseOracle.value + epsilon := by
  obtain ⟨fineDecision, simulated⟩ := simulation coarseOracle.rule
  calc
    fineOracle.value ≤ fineRisk fineDecision := fineOracle.optimal fineDecision
    _ ≤ coarseRisk coarseOracle.rule + epsilon := simulated
    _ = coarseOracle.value + epsilon := by rw [← coarseOracle.value_eq]

/-- Bidirectional approximate sufficiency bounds the absolute oracle-risk gap
by the larger directional deficiency. -/
theorem bidirectional_approximate_sufficiency_bounds_oracle_gap
    {FirstObservation SecondObservation Action : Type*}
    (firstRisk : (FirstObservation → Action) → ℝ)
    (secondRisk : (SecondObservation → Action) → ℝ)
    (firstToSecond secondToFirst : ℝ)
    (firstOracle : OracleDecisionCertificate firstRisk)
    (secondOracle : OracleDecisionCertificate secondRisk)
    (forward : ApproximateDecisionSimulation
      firstRisk secondRisk firstToSecond)
    (backward : ApproximateDecisionSimulation
      secondRisk firstRisk secondToFirst) :
    |secondOracle.value - firstOracle.value| ≤
      max firstToSecond secondToFirst := by
  have forwardBound := oracle_risk_le_of_approximate_task_simulation
    firstRisk secondRisk firstToSecond firstOracle secondOracle forward
  have backwardBound := oracle_risk_le_of_approximate_task_simulation
    secondRisk firstRisk secondToFirst secondOracle firstOracle backward
  apply abs_le.mpr
  constructor
  · have secondToFirstLe : secondToFirst ≤ max firstToSecond secondToFirst :=
      le_max_right _ _
    linarith
  · have firstToSecondLe : firstToSecond ≤ max firstToSecond secondToFirst :=
      le_max_left _ _
    linarith

/-- Direction matters: exact simulation from a high-risk coarse experiment to
a lower-risk fine experiment does not imply exact reverse simulation. -/
theorem one_way_task_sufficiency_does_not_imply_reverse :
    ∃ (coarseRisk fineRisk : (Unit → Unit) → ℝ),
      ApproximateDecisionSimulation coarseRisk fineRisk 0 ∧
        ¬ ApproximateDecisionSimulation fineRisk coarseRisk 0 := by
  let coarseRisk : (Unit → Unit) → ℝ := fun _ => 1
  let fineRisk : (Unit → Unit) → ℝ := fun _ => 0
  refine ⟨coarseRisk, fineRisk, ?_, ?_⟩
  · intro coarseDecision
    exact ⟨coarseDecision, by simp [coarseRisk, fineRisk]⟩
  · intro reverse
    obtain ⟨coarseDecision, impossible⟩ := reverse (fun _ => Unit.unit)
    norm_num [coarseRisk, fineRisk] at impossible

end OCKIndividuationMSpaceComposition
