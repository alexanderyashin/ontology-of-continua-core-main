import OCKIndividuationMSpaceComposition.CanonicalTaskQuotient

namespace OCKIndividuationMSpaceComposition

/-!
# Exact dynamic quotient / deterministic lumpability

For a deterministic physical update `next` and an observation map `observe`,
the observed cells carry a Markov-style transition exactly when the update is
constant on every observation fibre.  This is the deterministic OC boundary
of the usual lumpability theorem: it is an iff, not merely a sufficient
contract, and the induced transition is unique because every quotient cell is
reachable by construction.
-/

universe uWorld uObservation

def ObservationEq {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) (left right : World) : Prop :=
  observe left = observe right

def observationEqSetoid {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) : Setoid World where
  r := ObservationEq observe
  iseqv := by
    constructor
    · intro world
      rfl
    · intro left right h
      exact h.symm
    · intro left middle right h₁ h₂
      exact h₁.trans h₂

def ObservationCell {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) : Type uWorld :=
  Quotient (observationEqSetoid observe)

def observationCellOf {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) : World → ObservationCell observe :=
  Quotient.mk (observationEqSetoid observe)

def DynamicClosure
    {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) (next : World → World) : Prop :=
  ∀ left right,
    observe left = observe right → observe (next left) = observe (next right)

def inducedObservationTransition
    {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) (next : World → World)
    (closure : DynamicClosure observe next) :
    ObservationCell observe → ObservationCell observe :=
  Quotient.lift (fun world => observationCellOf observe (next world)) (by
    intro left right sameCell
    apply Quotient.sound (s := observationEqSetoid observe)
    exact closure left right sameCell)

theorem induced_observation_transition_commutes
    {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) (next : World → World)
    (closure : DynamicClosure observe next) (world : World) :
    inducedObservationTransition observe next closure
        (observationCellOf observe world) =
      observationCellOf observe (next world) := by
  rfl

theorem dynamic_quotient_exists_iff_closure
    {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) (next : World → World) :
    (∃ transition : ObservationCell observe → ObservationCell observe,
      ∀ world, transition (observationCellOf observe world) =
        observationCellOf observe (next world)) ↔
      DynamicClosure observe next := by
  constructor
  · rintro ⟨transition, commutes⟩ left right sameObservation
    have nextCells : observationCellOf observe (next left) =
        observationCellOf observe (next right) := by
      calc
      Quotient.mk (observationEqSetoid observe) (next left) =
          transition (observationCellOf observe left) := (commutes left).symm
      _ = transition (observationCellOf observe right) :=
        congrArg transition (Quotient.sound (s := observationEqSetoid observe) sameObservation)
      _ = Quotient.mk (observationEqSetoid observe) (next right) := commutes right
    exact Quotient.exact (s := observationEqSetoid observe) nextCells
  · intro closure
    exact ⟨inducedObservationTransition observe next closure,
      induced_observation_transition_commutes observe next closure⟩

theorem induced_dynamic_quotient_transition_unique
    {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) (next : World → World)
    (closure : DynamicClosure observe next)
    {transition₁ transition₂ : ObservationCell observe → ObservationCell observe}
    (commutes₁ : ∀ world, transition₁ (observationCellOf observe world) =
      observationCellOf observe (next world))
    (commutes₂ : ∀ world, transition₂ (observationCellOf observe world) =
      observationCellOf observe (next world)) :
    transition₁ = transition₂ := by
  funext cell
  obtain ⟨world, representative⟩ := Quotient.exists_rep cell
  calc
    transition₁ cell = transition₁ (Quotient.mk (observationEqSetoid observe) world) :=
      congrArg transition₁ representative.symm
    _ = transition₁ (observationCellOf observe world) := rfl
    _ = observationCellOf observe (next world) := commutes₁ world
    _ = transition₂ (observationCellOf observe world) := (commutes₂ world).symm
    _ = transition₂ (Quotient.mk (observationEqSetoid observe) world) := rfl
    _ = transition₂ cell := congrArg transition₂ representative

theorem dynamic_quotient_characterization
    {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) (next : World → World) :
    (∃! transition : ObservationCell observe → ObservationCell observe,
      ∀ world, transition (observationCellOf observe world) =
        observationCellOf observe (next world)) ↔
      DynamicClosure observe next := by
  constructor
  · rintro ⟨transition, commutes, _⟩
    exact (dynamic_quotient_exists_iff_closure observe next).mp ⟨transition, commutes⟩
  · intro closure
    refine ⟨inducedObservationTransition observe next closure,
      induced_observation_transition_commutes observe next closure, ?_⟩
    intro other commutes
    exact induced_dynamic_quotient_transition_unique observe next closure commutes
      (induced_observation_transition_commutes observe next closure)

end OCKIndividuationMSpaceComposition
