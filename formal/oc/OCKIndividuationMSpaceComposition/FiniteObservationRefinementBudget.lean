import OCKIndividuationMSpaceComposition.OriginFeatureObservationRefinement
import Mathlib.Data.Fintype.Card

namespace OCKIndividuationMSpaceComposition

/-!
# Finite observation-refinement budget

An observation refinement is useful only to the extent that it separates
otherwise aliased task outcomes.  This module supplies a finite, directly
measurable diagnostic: the number of ordered distinct world-pairs which remain
aliased by an observation while carrying different task outcomes.

The result is deliberately stronger than the informal claim that “more
features help”: a refinement can never *increase* this collision-pair budget,
but a deterministic recoding of the same origin observation leaves it exactly
unchanged.  Zero collisions is the precise sufficient condition for an exact
finite-task predictor; nonzero collisions are a structural no-go for exact
deterministic prediction on the registered worlds.
-/

universe uWorld uObservation uFine uOutcome uDerived

/-- Ordered pairs of distinct worlds which an observation aliases despite a
different declared task outcome. -/
def ObservationCollisionPair
    {World : Type uWorld} {Observation : Type uObservation} {Outcome : Type uOutcome}
    (observe : World → Observation) (target : World → Outcome) : Type uWorld :=
  { pair : World × World //
    pair.1 ≠ pair.2 ∧ observe pair.1 = observe pair.2 ∧ target pair.1 ≠ target pair.2 }

/-- The finite collision budget.  It is an operational quantity: on a frozen
finite registered universe it can be counted before deciding whether richer
measurements are worth acquiring. -/
noncomputable def observationCollisionPairFintype
    {World : Type uWorld} {Observation : Type uObservation} {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Observation] [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome) :
    Fintype (ObservationCollisionPair observe target) := by
  classical
  let candidates : Finset (World × World) := Finset.univ.filter (fun pair =>
    pair.1 ≠ pair.2 ∧ observe pair.1 = observe pair.2 ∧ target pair.1 ≠ target pair.2)
  exact Fintype.subtype candidates (by
    intro pair
    simp [candidates])

noncomputable def observationCollisionPairCount
    {World : Type uWorld} {Observation : Type uObservation} {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Observation] [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome) : Nat :=
  @Fintype.card _ (observationCollisionPairFintype observe target)

/-- Positive numerical theorem: an explicitly richer observation can only
remove task-relevant aliases.  It cannot create them. -/
theorem collision_pair_budget_monotone_under_refinement
    {World : Type uWorld} {Coarse : Type uObservation} {Fine : Type uFine}
    {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Coarse] [DecidableEq Fine]
    [DecidableEq Outcome]
    (coarse : World → Coarse) (fine : World → Fine) (target : World → Outcome)
    (refines : ObservationRefines coarse fine) :
    observationCollisionPairCount fine target ≤
      observationCollisionPairCount coarse target := by
  classical
  letI : Fintype (ObservationCollisionPair fine target) :=
    observationCollisionPairFintype fine target
  letI : Fintype (ObservationCollisionPair coarse target) :=
    observationCollisionPairFintype coarse target
  change Fintype.card (ObservationCollisionPair fine target) ≤
    Fintype.card (ObservationCollisionPair coarse target)
  rcases refines with ⟨forget, recovers⟩
  apply Fintype.card_le_of_injective (fun pair =>
    ⟨pair.1, pair.2.1, by
      calc
        coarse pair.1.1 = forget (fine pair.1.1) := (recovers pair.1.1).symm
        _ = forget (fine pair.1.2) := by rw [pair.2.2.1]
        _ = coarse pair.1.2 := recovers pair.1.2,
      pair.2.2.2⟩)
  intro first second equal
  apply Subtype.ext
  simpa using congrArg Subtype.val equal

/-- Outcome constancy on observation fibres is the semantic form of a zero
collision budget. -/
def OutcomeConstantOnObservationFibres
    {World : Type uWorld} {Observation : Type uObservation} {Outcome : Type uOutcome}
    (observe : World → Observation) (target : World → Outcome) : Prop :=
  ∀ left right, observe left = observe right → target left = target right

/-- A zero collision budget certifies the exact finite-task condition. -/
theorem zero_collision_pair_budget_implies_outcome_constancy
    {World : Type uWorld} {Observation : Type uObservation} {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Observation] [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (zeroBudget : observationCollisionPairCount observe target = 0) :
    OutcomeConstantOnObservationFibres observe target := by
  classical
  letI : Fintype (ObservationCollisionPair observe target) :=
    observationCollisionPairFintype observe target
  change Fintype.card (ObservationCollisionPair observe target) = 0 at zeroBudget
  intro left right sameObservation
  by_contra differentOutcome
  have nonemptyPair : Nonempty (ObservationCollisionPair observe target) :=
    ⟨⟨(left, right), by
      refine ⟨?_, sameObservation, differentOutcome⟩
      intro sameWorld
      exact differentOutcome (congrArg target sameWorld)⟩⟩
  have positive : 0 < observationCollisionPairCount observe target := by
    change 0 < Fintype.card (ObservationCollisionPair observe target)
    exact Fintype.card_pos_iff.mpr nonemptyPair
  exact (Nat.ne_of_gt positive) zeroBudget

/-- Positive completion of the finite-task chain: if the collision budget is
zero, a deterministic exact predictor exists on all registered worlds. -/
theorem zero_collision_pair_budget_has_exact_predictor
    {World : Type uWorld} {Observation : Type uObservation} {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Observation] [DecidableEq Outcome]
    [Inhabited Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (zeroBudget : observationCollisionPairCount observe target = 0) :
    ∃ predict : Observation → Outcome, ∀ world, predict (observe world) = target world := by
  classical
  have constant := zero_collision_pair_budget_implies_outcome_constancy observe target zeroBudget
  let predict : Observation → Outcome := fun observation =>
    if existsWorld : ∃ world, observe world = observation then
      target (Classical.choose existsWorld)
    else default
  refine ⟨predict, ?_⟩
  intro world
  dsimp [predict]
  split
  · apply constant
    rename_i h
    exact Classical.choose_spec h
  · rename_i impossible
    exact False.elim (impossible ⟨world, rfl⟩)

/-- A deterministic feature derived from the raw origin observation cannot
change the collision budget: it is an encoding, not an additional measurement.
-/
def derivedCollisionPairEquiv
    {World : Type uWorld} {Raw : Type uObservation} {Derived : Type uDerived}
    {Outcome : Type uOutcome}
    (raw : World → Raw) (derive : Raw → Derived) (target : World → Outcome) :
    ObservationCollisionPair (fun world => (raw world, derive (raw world))) target ≃
      ObservationCollisionPair raw target where
  toFun := fun pair =>
    ⟨pair.1, by
      rcases pair.2 with ⟨distinct, aliases, different⟩
      exact ⟨distinct, congrArg Prod.fst aliases, different⟩⟩
  invFun := fun pair =>
    ⟨pair.1, by
      rcases pair.2 with ⟨distinct, aliases, different⟩
      exact ⟨distinct, by simpa [aliases], different⟩⟩
  left_inv := by
    intro pair
    apply Subtype.ext
    rfl
  right_inv := by
    intro pair
    apply Subtype.ext
    rfl

/-- Quantitative no-go: feature engineering which is entirely deterministic
from an already available origin observation cannot reduce unresolved aliases.
Only a genuinely new measurement, or a changed target/domain, can do so. -/
theorem derived_feature_preserves_collision_pair_budget
    {World : Type uWorld} {Raw : Type uObservation} {Derived : Type uDerived}
    {Outcome : Type uOutcome}
    [Fintype World] [DecidableEq World] [DecidableEq Raw] [DecidableEq Derived]
    [DecidableEq Outcome]
    (raw : World → Raw) (derive : Raw → Derived) (target : World → Outcome) :
    observationCollisionPairCount (fun world => (raw world, derive (raw world))) target =
      observationCollisionPairCount raw target := by
  classical
  letI : Fintype (ObservationCollisionPair (fun world => (raw world, derive (raw world))) target) :=
    observationCollisionPairFintype (fun world => (raw world, derive (raw world))) target
  letI : Fintype (ObservationCollisionPair raw target) :=
    observationCollisionPairFintype raw target
  change Fintype.card (ObservationCollisionPair (fun world => (raw world, derive (raw world))) target) =
    Fintype.card (ObservationCollisionPair raw target)
  exact Fintype.card_congr (derivedCollisionPairEquiv raw derive target)

end OCKIndividuationMSpaceComposition
