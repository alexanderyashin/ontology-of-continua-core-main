import OCKIndividuationMSpaceComposition.FundamentalMetaMechanics
import OCKIndividuationMSpaceComposition.UniversalPredictiveDynamics
import Mathlib.Tactic.Linarith

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uLiftCarrier uLiftCandidate uRepairCandidate uOutcome uState uAction

/-!
# K/M-selected predictive model constraints

The K/M mechanism selects a rank-minimal lift that resolves a demanded
distinction.  Rank minimality alone need not choose a unique lift and does not
manufacture dynamics.  This module therefore keeps every resolving lift tied
at the selected rank as the OC structural model class and states exactly what
is possible, necessary, point-identified, or only interval-identified across
that class.

The set-valued operations are an adaptation of mature version-space and
partial-identification mathematics.  The OC-specific content is the adapter
from `SelectedPressureResolution` to the tied resolving class.
-/

/-- A resolving M-fiber member tied with the selected minimum rank. -/
def KMTiedResolvingCandidate
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (candidate : liftSearch.Candidate) : Prop :=
  liftSearch.constraints candidate ∧
  LiftResolves (liftSearch.lift candidate) d ∧
  rank candidate = rank resolution.selection.minimizer.1

/-- The selected minimizer itself belongs to the tied resolving class. -/
theorem selected_is_km_tied_resolving
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank) :
    KMTiedResolvingCandidate resolution resolution.selection.minimizer.1 := by
  exact ⟨resolution.selection.minimizer.2.1,
    resolution.selectedLiftResolves, rfl⟩

/-- Every admissible resolving candidate has rank no lower than the selected
one.  This is the exact structural prediction supplied by the K/M argmin. -/
theorem selected_rank_bounds_every_resolving_lift
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (candidate : liftSearch.Candidate)
    (eligible : liftSearch.constraints candidate ∧
      LiftResolves (liftSearch.lift candidate) d) :
    rank resolution.selection.minimizer.1 ≤ rank candidate := by
  exact resolution.selection.minimalWithinFiber ⟨candidate, eligible⟩

/-- Minimum adapter from each K/M lift candidate to a common typed dynamical
carrier.  The adapter is explicit because K/M rank does not itself specify a
transition law, initial condition, horizon, or admissibility layers. -/
structure KMPredictiveInterpretation
    {K : CurrentK}
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K) where
  State : Type uState
  Action : Type uAction
  stepOf : liftSearch.Candidate → State → Action → State → Prop
  layersOf : liftSearch.Candidate → LayeredAdmissibility State
  initial : State
  horizon : Nat

def KMPredictiveInterpretation.systemAt
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (interpretation : KMPredictiveInterpretation liftSearch)
    (candidate : liftSearch.Candidate) : PredictiveSystem where
  State := interpretation.State
  Action := interpretation.Action
  step := interpretation.stepOf candidate
  layers := interpretation.layersOf candidate

/-- Candidate-relative bounded future induced by the explicit dynamics
adapter. -/
def KMPredictiveInterpretation.targetFutureAt
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (interpretation : KMPredictiveInterpretation liftSearch)
    (candidate : liftSearch.Candidate)
    (target : interpretation.State) : Prop :=
  TargetFuture (interpretation.systemAt candidate) interpretation.initial
    interpretation.horizon target

/-- An outcome is possible when at least one tied resolving model predicts it. -/
def KMPossibleFuture
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (future : liftSearch.Candidate → Outcome → Prop)
    (outcome : Outcome) : Prop :=
  ∃ candidate, KMTiedResolvingCandidate resolution candidate ∧
    future candidate outcome

/-- An outcome is necessary when every tied resolving model predicts it. -/
def KMNecessaryFuture
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (future : liftSearch.Candidate → Outcome → Prop)
    (outcome : Outcome) : Prop :=
  ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    future candidate outcome

/-- All tied structural minima have the selected model's future behavior. -/
def KMPredictivelyCoherent
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (future : liftSearch.Candidate → Outcome → Prop) : Prop :=
  ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    ∀ outcome, future candidate outcome ↔
      future resolution.selection.minimizer.1 outcome

/-- Behavioral coherence collapses the possible future to the selected
model's future exactly. -/
theorem km_possible_future_exact_of_coherence
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (future : liftSearch.Candidate → Outcome → Prop)
    (coherent : KMPredictivelyCoherent resolution future)
    (outcome : Outcome) :
    KMPossibleFuture resolution future outcome ↔
      future resolution.selection.minimizer.1 outcome := by
  constructor
  · rintro ⟨candidate, tied, predicted⟩
    exact (coherent candidate tied outcome).mp predicted
  · intro predicted
    exact ⟨resolution.selection.minimizer.1,
      selected_is_km_tied_resolving resolution, predicted⟩

/-- Under the same coherence contract, the necessary future also equals the
selected model's future exactly. -/
theorem km_necessary_future_exact_of_coherence
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (future : liftSearch.Candidate → Outcome → Prop)
    (coherent : KMPredictivelyCoherent resolution future)
    (outcome : Outcome) :
    KMNecessaryFuture resolution future outcome ↔
      future resolution.selection.minimizer.1 outcome := by
  constructor
  · intro necessary
    exact necessary resolution.selection.minimizer.1
      (selected_is_km_tied_resolving resolution)
  · intro selectedFuture candidate tied
    exact (coherent candidate tied outcome).mpr selectedFuture

/-- Point identification means possible and necessary predictions agree for
every outcome in the declared interpretation. -/
def KMPointIdentified
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (future : liftSearch.Candidate → Outcome → Prop) : Prop :=
  ∀ outcome, KMPossibleFuture resolution future outcome ↔
    KMNecessaryFuture resolution future outcome

theorem km_coherence_implies_point_identified
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (future : liftSearch.Candidate → Outcome → Prop)
    (coherent : KMPredictivelyCoherent resolution future) :
    KMPointIdentified resolution future := by
  intro outcome
  rw [km_possible_future_exact_of_coherence resolution future coherent outcome]
  rw [km_necessary_future_exact_of_coherence resolution future coherent outcome]

/-- Concrete specialization: if all tied K/M candidates induce the same
bounded `TargetFuture` under an explicit common-carrier dynamics adapter, the
OC-derived future is point-identified. -/
theorem km_target_future_point_identified_of_dynamics_coherence
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMPredictiveInterpretation liftSearch)
    (coherent : KMPredictivelyCoherent resolution
      interpretation.targetFutureAt) :
    KMPointIdentified resolution interpretation.targetFutureAt :=
  km_coherence_implies_point_identified resolution
    interpretation.targetFutureAt coherent

/-- No-go: two tied structural minima that disagree on one outcome make the
future non-point-identified.  Rank minimality cannot select between them. -/
theorem tied_behavioral_disagreement_blocks_point_identification
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (future : liftSearch.Candidate → Outcome → Prop)
    (left right : liftSearch.Candidate) (outcome : Outcome)
    (leftTied : KMTiedResolvingCandidate resolution left)
    (rightTied : KMTiedResolvingCandidate resolution right)
    (leftPredicts : future left outcome)
    (rightRejects : ¬ future right outcome) :
    ¬ KMPointIdentified resolution future := by
  intro identified
  have possible : KMPossibleFuture resolution future outcome :=
    ⟨left, leftTied, leftPredicts⟩
  have necessary := (identified outcome).mp possible
  exact rightRejects (necessary right rightTied)

/-- A refinement is an additional evidence/assumption filter over the tied
structural class. -/
def KMRefinedPossibleFuture
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (refine : liftSearch.Candidate → Prop)
    (future : liftSearch.Candidate → Outcome → Prop)
    (outcome : Outcome) : Prop :=
  ∃ candidate, KMTiedResolvingCandidate resolution candidate ∧
    refine candidate ∧ future candidate outcome

def KMRefinedNecessaryFuture
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (refine : liftSearch.Candidate → Prop)
    (future : liftSearch.Candidate → Outcome → Prop)
    (outcome : Outcome) : Prop :=
  ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    refine candidate → future candidate outcome

/-- Adding a filter can only shrink the possible future. -/
theorem refinement_shrinks_possible_future
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (refine : liftSearch.Candidate → Prop)
    (future : liftSearch.Candidate → Outcome → Prop)
    (outcome : Outcome) :
    KMRefinedPossibleFuture resolution refine future outcome →
      KMPossibleFuture resolution future outcome := by
  rintro ⟨candidate, tied, _, predicted⟩
  exact ⟨candidate, tied, predicted⟩

/-- Adding a filter can only expand the necessary future. -/
theorem refinement_expands_necessary_future
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    {Outcome : Type uOutcome}
    (refine : liftSearch.Candidate → Prop)
    (future : liftSearch.Candidate → Outcome → Prop)
    (outcome : Outcome) :
    KMNecessaryFuture resolution future outcome →
      KMRefinedNecessaryFuture resolution refine future outcome := by
  intro necessary candidate tied _
  exact necessary candidate tied

/-- A sound and sharp numerical envelope over the tied structural class. -/
structure KMSharpPredictionBand
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (value : liftSearch.Candidate → ℚ) where
  lower : ℚ
  upper : ℚ
  valid : ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    lower ≤ value candidate ∧ value candidate ≤ upper
  lowerAttained : ∃ candidate, KMTiedResolvingCandidate resolution candidate ∧
    value candidate = lower
  upperAttained : ∃ candidate, KMTiedResolvingCandidate resolution candidate ∧
    value candidate = upper

def KMSharpPredictionBand.width
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {value : liftSearch.Candidate → ℚ}
    (band : KMSharpPredictionBand resolution value) : ℚ :=
  band.upper - band.lower

theorem km_sharp_prediction_band_nonnegative
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {value : liftSearch.Candidate → ℚ}
    (band : KMSharpPredictionBand resolution value) :
    0 ≤ band.width := by
  obtain ⟨candidate, tied, atLower⟩ := band.lowerAttained
  have bounds := band.valid candidate tied
  rw [atLower] at bounds
  exact sub_nonneg.mpr bounds.2

/-- Sharpness theorem: every sound interval for the same K/M model class must
contain both sharp endpoints.  Hence no universally valid interval can be
narrower without adding a class-refining premise or evidence. -/
theorem km_sharp_band_is_information_optimal
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {value : liftSearch.Candidate → ℚ}
    (band : KMSharpPredictionBand resolution value)
    (otherLower otherUpper : ℚ)
    (otherValid : ∀ candidate,
      KMTiedResolvingCandidate resolution candidate →
      otherLower ≤ value candidate ∧ value candidate ≤ otherUpper) :
    otherLower ≤ band.lower ∧ band.upper ≤ otherUpper := by
  obtain ⟨lowerCandidate, lowerTied, lowerAt⟩ := band.lowerAttained
  obtain ⟨upperCandidate, upperTied, upperAt⟩ := band.upperAttained
  constructor
  · simpa [lowerAt] using (otherValid lowerCandidate lowerTied).1
  · simpa [upperAt] using (otherValid upperCandidate upperTied).2

theorem km_no_sound_interval_has_smaller_width
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {value : liftSearch.Candidate → ℚ}
    (band : KMSharpPredictionBand resolution value)
    (otherLower otherUpper : ℚ)
    (otherValid : ∀ candidate,
      KMTiedResolvingCandidate resolution candidate →
      otherLower ≤ value candidate ∧ value candidate ≤ otherUpper) :
    band.width ≤ otherUpper - otherLower := by
  have containment := km_sharp_band_is_information_optimal
    band otherLower otherUpper otherValid
  dsimp [KMSharpPredictionBand.width]
  linarith

/-- Zero sharp width is exactly sufficient for one numerical prediction over
the entire tied class. -/
theorem km_zero_width_gives_exact_numeric_prediction
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {value : liftSearch.Candidate → ℚ}
    (band : KMSharpPredictionBand resolution value)
    (zeroWidth : band.width = 0) :
    ∀ candidate, KMTiedResolvingCandidate resolution candidate →
      value candidate = band.lower := by
  have endpoints : band.upper = band.lower := by
    dsimp [KMSharpPredictionBand.width] at zeroWidth
    linarith
  intro candidate tied
  have bounds := band.valid candidate tied
  rw [endpoints] at bounds
  exact le_antisymm bounds.2 bounds.1

/-- No-go: two rank-tied models with unequal numerical forecasts forbid any
single exact forecast justified by K/M structure alone. -/
theorem tied_numeric_disagreement_blocks_exact_prediction
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (value : liftSearch.Candidate → ℚ)
    (left right : liftSearch.Candidate)
    (leftTied : KMTiedResolvingCandidate resolution left)
    (rightTied : KMTiedResolvingCandidate resolution right)
    (different : value left ≠ value right) :
    ¬ ∃ exactValue : ℚ, ∀ candidate,
      KMTiedResolvingCandidate resolution candidate →
      value candidate = exactValue := by
  rintro ⟨exactValue, exactForAll⟩
  apply different
  calc
    value left = exactValue := exactForAll left leftTied
    _ = value right := (exactForAll right rightTied).symm

end OCKIndividuationMSpaceComposition
