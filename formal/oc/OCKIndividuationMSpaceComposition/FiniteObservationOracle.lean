import OCKIndividuationMSpaceComposition.FiniteObservationLearning

namespace OCKIndividuationMSpaceComposition

/-!
## Exact finite-sample oracle for a fixed observation channel

This module separates algorithm error from observation-channel error.  Once a
finite frozen dataset and an observation signature are fixed, every predictor
that sees only that signature is bounded by the largest outcome multiplicity
inside each observation cell.  The theorem ranges over all functions from the
observation type to the outcome type, not over one fitted model class.
-/

/-- A finite prediction problem with an explicitly registered observation
channel. -/
structure FiniteObservationDataset
    (Index Observation Outcome : Type*) where
  observation : Index → Observation
  outcome : Index → Outcome

namespace FiniteObservationDataset

variable {Index Observation Outcome FineObservation : Type*}
variable [Fintype Index] [Fintype Observation]
variable [DecidableEq Observation] [DecidableEq Outcome]

/-- Number of frozen rows in one observation/outcome cell. -/
def outcomeMultiplicity
    (dataset : FiniteObservationDataset Index Observation Outcome)
    (observed : Observation) (label : Outcome) : ℕ :=
  ∑ index : Index,
    if dataset.observation index = observed ∧ dataset.outcome index = label
      then 1 else 0

/-- Number of correct rows for an arbitrary deterministic predictor that sees
only the registered observation. -/
def correctCount
    (dataset : FiniteObservationDataset Index Observation Outcome)
    (predictor : Observation → Outcome) : ℕ :=
  ∑ index : Index,
    if predictor (dataset.observation index) = dataset.outcome index
      then 1 else 0

/-- The total correct count partitions exactly over observation cells. -/
theorem correctCount_eq_sum_outcomeMultiplicity
    (dataset : FiniteObservationDataset Index Observation Outcome)
    (predictor : Observation → Outcome) :
    dataset.correctCount predictor =
      ∑ observed : Observation,
        dataset.outcomeMultiplicity observed (predictor observed) := by
  classical
  unfold correctCount outcomeMultiplicity
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro index _
  by_cases correct :
      predictor (dataset.observation index) = dataset.outcome index
  · rw [if_pos correct]
    rw [Finset.sum_eq_single (dataset.observation index)]
    · simp [correct]
    · intro other _ different
      simp [different.symm]
    · simp
  · rw [if_neg correct]
    symm
    apply Finset.sum_eq_zero
    intro observed _
    by_cases same : dataset.observation index = observed
    · subst observed
      have reverse :
          dataset.outcome index ≠ predictor (dataset.observation index) :=
        fun equality => correct equality.symm
      simp [reverse]
    · simp [same]

/-- A checkable oracle certificate: `capacity observed` bounds every outcome
multiplicity in that observation cell, and `oracleLabel` attains the bound. -/
structure OracleCapacityCertificate
    (dataset : FiniteObservationDataset Index Observation Outcome) where
  capacity : Observation → ℕ
  oracleLabel : Observation → Outcome
  upper : ∀ observed label,
    dataset.outcomeMultiplicity observed label ≤ capacity observed
  attained : ∀ observed,
    dataset.outcomeMultiplicity observed (oracleLabel observed) =
      capacity observed

/-- Universal empirical no-better theorem.  It quantifies over every
deterministic predictor on the fixed observation channel. -/
theorem correctCount_le_oracleCapacity
    (dataset : FiniteObservationDataset Index Observation Outcome)
    (certificate : OracleCapacityCertificate dataset)
    (predictor : Observation → Outcome) :
    dataset.correctCount predictor ≤
      ∑ observed : Observation, certificate.capacity observed := by
  rw [dataset.correctCount_eq_sum_outcomeMultiplicity predictor]
  exact Finset.sum_le_sum fun observed _ =>
    certificate.upper observed (predictor observed)

/-- The registered oracle labels attain the universal upper bound. -/
theorem oracleLabel_correctCount_eq_capacity
    (dataset : FiniteObservationDataset Index Observation Outcome)
    (certificate : OracleCapacityCertificate dataset) :
    dataset.correctCount certificate.oracleLabel =
      ∑ observed : Observation, certificate.capacity observed := by
  rw [dataset.correctCount_eq_sum_outcomeMultiplicity certificate.oracleLabel]
  exact Finset.sum_congr rfl fun observed _ => certificate.attained observed

/-- Exact optimality: no deterministic function of the registered observation
can correctly classify more frozen rows than the certified oracle. -/
theorem no_observation_predictor_beats_oracle
    (dataset : FiniteObservationDataset Index Observation Outcome)
    (certificate : OracleCapacityCertificate dataset)
    (predictor : Observation → Outcome) :
    dataset.correctCount predictor ≤
      dataset.correctCount certificate.oracleLabel := by
  rw [oracleLabel_correctCount_eq_capacity dataset certificate]
  exact dataset.correctCount_le_oracleCapacity certificate predictor

/-- Generic collision no-go.  Two rows with the same registered observation
and different outcomes rule out an exact predictor on that channel. -/
theorem observation_collision_no_everywhere_correct_predictor
    (dataset : FiniteObservationDataset Index Observation Outcome)
    (left right : Index)
    (sameObservation : dataset.observation left = dataset.observation right)
    (differentOutcome : dataset.outcome left ≠ dataset.outcome right)
    (predictor : Observation → Outcome) :
    ¬ ∀ index, predictor (dataset.observation index) = dataset.outcome index := by
  intro exactEverywhere
  have leftCorrect := exactEverywhere left
  have rightCorrect := exactEverywhere right
  apply differentOutcome
  rw [← leftCorrect, ← rightCorrect, sameObservation]

/-- A refined observation can reproduce every coarse predictor exactly by
composition with the declared coarse projection.  Therefore extra observable
coordinates cannot reduce attainable oracle accuracy; any degradation after
refinement is an estimation, support, shift or implementation effect. -/
theorem refinement_lift_preserves_correctCount
    [DecidableEq FineObservation]
    (fineDataset : FiniteObservationDataset Index FineObservation Outcome)
    (coarse : FineObservation → Observation)
    (coarseDataset : FiniteObservationDataset Index Observation Outcome)
    (observationCommutes : ∀ index,
      coarse (fineDataset.observation index) = coarseDataset.observation index)
    (outcomeCommutes : ∀ index,
      fineDataset.outcome index = coarseDataset.outcome index)
    (coarsePredictor : Observation → Outcome) :
    fineDataset.correctCount (coarsePredictor ∘ coarse) =
      coarseDataset.correctCount coarsePredictor := by
  unfold correctCount
  apply Finset.sum_congr rfl
  intro index _
  simp only [Function.comp_apply]
  simp [observationCommutes index, outcomeCommutes index]

end FiniteObservationDataset

end OCKIndividuationMSpaceComposition
