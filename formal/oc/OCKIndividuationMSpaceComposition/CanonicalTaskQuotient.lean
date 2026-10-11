import OCKIndividuationMSpaceComposition.MultiTaskOpticJoin

namespace OCKIndividuationMSpaceComposition

/-!
# Canonical task quotient (finite or infinite)

The target of a task, rather than a stored identifier, induces an equivalence
relation on worlds.  The quotient by that relation is the canonical exact
task representation.  The main theorem below is a characterization: every
exactly sufficient, surjective representation admits one and only one map to
the quotient, and a representation is minimal exactly when that map is an
isomorphism.  Total factorisation over the entire observation codomain is
guarded by `[Nonempty World]` because unreachable observation values require a
chosen quotient representative; the unconditional reachable-range theorem
lives in `CanonicalTaskQuotientReachable`.  No probability, learner, or
physical identity claim is hidden in this construction.
-/

universe uWorld uOutcome uObservation

def TaskEq {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) (left right : World) : Prop :=
  target left = target right

def taskEqSetoid {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) : Setoid World where
  r := TaskEq target
  iseqv := by
    constructor
    · intro world
      rfl
    · intro left right h
      exact h.symm
    · intro left middle right h₁ h₂
      exact h₁.trans h₂

def TaskQuotient {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) : Type uWorld :=
  Quotient (taskEqSetoid target)

def taskQuotientObservation {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) : World → TaskQuotient target :=
  Quotient.mk (taskEqSetoid target)

def taskQuotientSignature {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) : TaskQuotient target → Outcome :=
  Quotient.lift target (by
    intro left right h
    exact h)

theorem taskQuotient_signature_of_world
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) (world : World) :
    taskQuotientSignature target (taskQuotientObservation target world) =
      target world := by
  rfl

def ExactTaskRepresentation
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome)
    {Observation : Type uObservation}
    (observe : World → Observation) : Prop :=
  ∀ left right, observe left = observe right ↔ target left = target right

theorem taskQuotient_is_exact
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) :
    ∀ left right,
      taskQuotientObservation target left = taskQuotientObservation target right ↔
        target left = target right := by
  intro left right
  constructor
  · intro h
    exact Quotient.exact h
  · intro h
    exact Quotient.sound (s := taskEqSetoid target) h

theorem sufficient_observation_has_quotient_factor
    {World : Type uWorld} {Outcome : Type uOutcome}
    [Nonempty World]
    (target : World → Outcome)
    {Observation : Type uObservation}
    (observe : World → Observation)
    (sufficient : ∀ left right,
      observe left = observe right → target left = target right) :
    ∃ factor : Observation → TaskQuotient target,
      ∀ world, factor (observe world) = taskQuotientObservation target world := by
  classical
  let factor : Observation → TaskQuotient target := fun observation =>
    if h : ∃ world, observe world = observation then
      taskQuotientObservation target (Classical.choose h)
    else
      Quotient.mk (taskEqSetoid target) (Classical.choice inferInstance)
  refine ⟨factor, ?_⟩
  intro world
  simp only [factor]
  have h : ∃ candidate, observe candidate = observe world := ⟨world, rfl⟩
  rw [dif_pos h]
  apply Quotient.sound (s := taskEqSetoid target)
  exact sufficient (Classical.choose h) world (Classical.choose_spec h)

theorem quotient_factor_unique_on_reachable_observations
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome)
    {Observation : Type uObservation}
    (observe : World → Observation)
    {factor₁ factor₂ : Observation → TaskQuotient target}
    (factor₁_spec : ∀ world,
      factor₁ (observe world) = taskQuotientObservation target world)
    (factor₂_spec : ∀ world,
      factor₂ (observe world) = taskQuotientObservation target world)
    (observe_surjective : Function.Surjective observe) :
    factor₁ = factor₂ := by
  funext observation
  obtain ⟨world, rfl⟩ := observe_surjective observation
  exact (factor₁_spec world).trans (factor₂_spec world).symm

theorem exact_representation_quotient_equiv
    {World : Type uWorld} {Outcome : Type uOutcome}
    [Nonempty World]
    (target : World → Outcome)
    {Observation : Type uObservation}
    (observe : World → Observation)
    (exact : ExactTaskRepresentation target observe)
    (observe_surjective : Function.Surjective observe) :
    ∃ e : Observation ≃ TaskQuotient target,
      ∀ world, e (observe world) = taskQuotientObservation target world := by
  classical
  let toQuotient : Observation → TaskQuotient target := fun observation =>
    if h : ∃ world, observe world = observation then
      taskQuotientObservation target (Classical.choose h)
    else
      Quotient.mk (taskEqSetoid target) (Classical.choice inferInstance)
  have toQuotient_spec : ∀ world,
      toQuotient (observe world) = taskQuotientObservation target world := by
    intro world
    simp only [toQuotient]
    have h : ∃ candidate, observe candidate = observe world := ⟨world, rfl⟩
    rw [dif_pos h]
    apply Quotient.sound (s := taskEqSetoid target)
    exact (exact (Classical.choose h) world).mp (Classical.choose_spec h)
  have toQuotient_injective : Function.Injective toQuotient := by
    intro left right same
    obtain ⟨worldLeft, left_spec⟩ := observe_surjective left
    obtain ⟨worldRight, right_spec⟩ := observe_surjective right
    have sameObservation : observe worldLeft = observe worldRight := by
      apply (exact worldLeft worldRight).mpr
      apply (taskQuotient_is_exact target worldLeft worldRight).mp
      calc
        taskQuotientObservation target worldLeft = toQuotient (observe worldLeft) :=
          (toQuotient_spec worldLeft).symm
        _ = toQuotient (observe worldRight) := by simpa [left_spec, right_spec] using same
        _ = taskQuotientObservation target worldRight := toQuotient_spec worldRight
    exact left_spec.symm.trans (sameObservation.trans right_spec)
  have toQuotient_surjective : Function.Surjective toQuotient := by
    intro quotient
    refine Quotient.inductionOn quotient ?_
    intro world
    exact ⟨observe world, by simpa [taskQuotientObservation] using toQuotient_spec world⟩
  refine ⟨Equiv.ofBijective toQuotient ⟨toQuotient_injective, toQuotient_surjective⟩, ?_⟩
  exact toQuotient_spec

theorem canonical_task_quotient_characterization
    {World : Type uWorld} {Outcome : Type uOutcome}
    [Nonempty World]
    (target : World → Outcome)
    {Observation : Type uObservation}
    (observe : World → Observation) :
    (ExactTaskRepresentation target observe ∧ Function.Surjective observe) ↔
      (∃ e : Observation ≃ TaskQuotient target,
        ∀ world, e (observe world) = taskQuotientObservation target world) := by
  constructor
  · rintro ⟨exact, surjective⟩
    exact exact_representation_quotient_equiv target observe exact surjective
  · rintro ⟨e, factor⟩
    constructor
    · intro left right
      constructor
      · intro sameObservation
        apply (taskQuotient_is_exact target left right).mp
        calc
          taskQuotientObservation target left = e (observe left) := (factor left).symm
          _ = e (observe right) := congrArg e sameObservation
          _ = taskQuotientObservation target right := factor right
      · intro sameTarget
        apply e.injective
        calc
          e (observe left) = taskQuotientObservation target left := factor left
          _ = taskQuotientObservation target right := (taskQuotient_is_exact target left right).mpr sameTarget
          _ = e (observe right) := (factor right).symm
    · intro observation
      obtain ⟨world, representative⟩ := Quotient.exists_rep (e observation)
      refine ⟨world, ?_⟩
      apply e.injective
      calc
        e (observe world) = taskQuotientObservation target world := factor world
        _ = e observation := representative

end OCKIndividuationMSpaceComposition
