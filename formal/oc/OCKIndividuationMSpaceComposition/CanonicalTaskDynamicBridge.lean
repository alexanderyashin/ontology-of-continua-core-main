import OCKIndividuationMSpaceComposition.DynamicObservationQuotient

namespace OCKIndividuationMSpaceComposition

/-!
# Canonical task quotient × dynamics bridge

This is the first explicit cross-family composition after the separate M1 and
M3 results.  A task quotient is not automatically a dynamical state: it
supports exact future evolution precisely when the task target is a congruence
for the declared update.  The statement is the task-indexed form of the
deterministic lumpability boundary.
-/

universe uWorld uOutcome

def TaskDynamicClosure
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) (next : World → World) : Prop :=
  ∀ left right,
    target left = target right → target (next left) = target (next right)

def inducedTaskQuotientTransition
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) (next : World → World)
    (closure : TaskDynamicClosure target next) :
    TaskQuotient target → TaskQuotient target :=
  Quotient.lift (fun world => taskQuotientObservation target (next world)) (by
    intro left right sameClass
    apply Quotient.sound (s := taskEqSetoid target)
    exact closure left right sameClass)

theorem induced_task_quotient_transition_commutes
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) (next : World → World)
    (closure : TaskDynamicClosure target next) (world : World) :
    inducedTaskQuotientTransition target next closure
        (taskQuotientObservation target world) =
      taskQuotientObservation target (next world) := by
  rfl

theorem canonical_task_dynamic_exists_iff
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) (next : World → World) :
    (∃ transition : TaskQuotient target → TaskQuotient target,
      ∀ world, transition (taskQuotientObservation target world) =
        taskQuotientObservation target (next world)) ↔
      TaskDynamicClosure target next := by
  constructor
  · rintro ⟨transition, commutes⟩ left right sameTarget
    have sameClass : taskQuotientObservation target (next left) =
        taskQuotientObservation target (next right) := by
      calc
        taskQuotientObservation target (next left) =
            transition (taskQuotientObservation target left) := (commutes left).symm
        _ = transition (taskQuotientObservation target right) :=
          congrArg transition (Quotient.sound (s := taskEqSetoid target) sameTarget)
        _ = taskQuotientObservation target (next right) := commutes right
    exact (taskQuotient_is_exact target (next left) (next right)).mp sameClass
  · intro closure
    exact ⟨inducedTaskQuotientTransition target next closure,
      induced_task_quotient_transition_commutes target next closure⟩

theorem canonical_task_dynamic_transition_unique
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) (next : World → World)
    {transition₁ transition₂ : TaskQuotient target → TaskQuotient target}
    (commutes₁ : ∀ world, transition₁ (taskQuotientObservation target world) =
      taskQuotientObservation target (next world))
    (commutes₂ : ∀ world, transition₂ (taskQuotientObservation target world) =
      taskQuotientObservation target (next world)) :
    transition₁ = transition₂ := by
  funext cell
  obtain ⟨world, representative⟩ := Quotient.exists_rep cell
  calc
    transition₁ cell = transition₁ (Quotient.mk (taskEqSetoid target) world) :=
      congrArg transition₁ representative.symm
    _ = transition₁ (taskQuotientObservation target world) := rfl
    _ = taskQuotientObservation target (next world) := commutes₁ world
    _ = transition₂ (taskQuotientObservation target world) := (commutes₂ world).symm
    _ = transition₂ (Quotient.mk (taskEqSetoid target) world) := rfl
    _ = transition₂ cell := congrArg transition₂ representative

theorem canonical_task_dynamic_characterization
    {World : Type uWorld} {Outcome : Type uOutcome}
    (target : World → Outcome) (next : World → World) :
    (∃! transition : TaskQuotient target → TaskQuotient target,
      ∀ world, transition (taskQuotientObservation target world) =
        taskQuotientObservation target (next world)) ↔
      TaskDynamicClosure target next := by
  constructor
  · rintro ⟨transition, commutes, _⟩
    exact (canonical_task_dynamic_exists_iff target next).mp ⟨transition, commutes⟩
  · intro closure
    refine ⟨inducedTaskQuotientTransition target next closure,
      induced_task_quotient_transition_commutes target next closure, ?_⟩
    intro other commutes
    exact canonical_task_dynamic_transition_unique target next commutes
      (induced_task_quotient_transition_commutes target next closure)

end OCKIndividuationMSpaceComposition
