import OCKIndividuationMSpaceComposition.FiniteObservationLearning
import Mathlib.Data.Fintype.Card

namespace OCKIndividuationMSpaceComposition

/-!
# Observation-cell budget for exact finite prediction

An OC prediction is not made exact by accumulating arbitrary rows.  For a
registered finite task, the observation map partitions the world into
task-relevant cells.  Exact prediction requires that the design cover every
such cell and that the outcome be constant inside it.  This module makes the
first requirement numerical: a design with fewer independent observations
than reachable observation cells cannot cover the task.

The result is intentionally non-probabilistic.  It is the hard coverage floor
which precedes (rather than competes with) the Fano/information and
concentration bounds in the rest of the OC corpus.
-/

universe uWorld uObservation uOutcome

/-- A finite design covers every declared observation cell only if it has at
least as many observations as the number of reachable cells. -/
theorem covered_design_requires_at_least_observation_cells
    {World : Type uWorld} {Observation : Type uObservation}
    [Fintype Observation]
    {sampleSize : Nat}
    (observe : World → Observation)
    (sample : Fin sampleSize → World)
    (reachableCell : Function.Surjective observe)
    (covers : ObservationDesignCovers observe sample) :
    Fintype.card Observation ≤ sampleSize := by
  have sampleObservationSurjective : Function.Surjective
      (fun index : Fin sampleSize => observe (sample index)) := by
    intro observation
    rcases reachableCell observation with ⟨world, reachesObservation⟩
    rcases covers world with ⟨index, coversWorld⟩
    exact ⟨index, coversWorld.trans reachesObservation⟩
  simpa using Fintype.card_le_of_surjective
    (fun index : Fin sampleSize => observe (sample index))
    sampleObservationSurjective

/-- Sharp coverage no-go: below the reachable-cell count, no sample can cover
the registered observation space.  No fitting procedure can repair this
structural absence of a cell. -/
theorem too_few_samples_block_observation_coverage
    {World : Type uWorld} {Observation : Type uObservation}
    [Fintype Observation]
    {sampleSize : Nat}
    (observe : World → Observation)
    (sample : Fin sampleSize → World)
    (reachableCell : Function.Surjective observe)
    (tooFew : sampleSize < Fintype.card Observation) :
    ¬ ObservationDesignCovers observe sample := by
  intro covers
  exact (not_le_of_gt tooFew)
    (covered_design_requires_at_least_observation_cells
      observe sample reachableCell covers)

/-- Positive exactness theorem with an explicit data-design premise.  The
predictor is derived from the observed covered cell representative, not from a
hidden persistent identity. -/
theorem covered_sufficient_design_has_exact_task_predictor
    {World : Type uWorld} {Observation : Type uObservation}
    {Outcome : Type uOutcome} [Inhabited Outcome] {sampleSize : Nat}
    (observe : World → Observation) (outcome : World → Outcome)
    (sample : Fin sampleSize → World)
    (covers : ObservationDesignCovers observe sample)
    (sufficient : ∀ left right,
      observe left = observe right → outcome left = outcome right) :
    ∀ world,
      coveredSamplePredictor observe outcome sample (observe world) = outcome world :=
  covered_sufficient_sample_predictor_is_exact observe outcome sample covers sufficient

/-- The operational lower bound is task-relative: a changed observation map
or a changed outcome partition changes the cell budget.  Thus no universal
row-count is claimed by OC. -/
theorem exact_prediction_requires_cell_budget_or_stronger_structure
    {World : Type uWorld} {Observation : Type uObservation}
    [Fintype Observation]
    {sampleSize : Nat}
    (observe : World → Observation)
    (sample : Fin sampleSize → World)
    (reachableCell : Function.Surjective observe)
    (tooFew : sampleSize < Fintype.card Observation) :
    ¬ ObservationDesignCovers observe sample :=
  too_few_samples_block_observation_coverage observe sample reachableCell tooFew

end OCKIndividuationMSpaceComposition
