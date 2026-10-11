import OCKIndividuationMSpaceComposition.CanonicalTaskQuotient

namespace OCKIndividuationMSpaceComposition

/-!
# Reachable task factorisation and semantic identity guards

The total factor theorem in `CanonicalTaskQuotient` is intentionally guarded
by `[Nonempty World]` because it totalises unreachable observation values by
choosing a quotient representative.  The range theorem below removes that
choice entirely and is valid for an empty world.  The explicit empty-world
no-go and finite Boolean witnesses make the prose boundary machine-checkable:
task equivalence is not world identity and passive equivalence is not
continuation identity.
-/

/-- Canonical factor through the reachable observation range. -/
noncomputable def reachableTaskQuotientFactor
    {World : Type*}
    {Outcome : Type*}
    (target : World → Outcome)
    {Observation : Type*}
    (observe : World → Observation) :
    Set.range observe → TaskQuotient target := fun observed =>
  taskQuotientObservation target (Classical.choose observed.property)

/-- Exact sufficient observations always factor on their reachable range. -/
theorem sufficient_observation_has_range_quotient_factor
    {World : Type*}
    {Outcome : Type*}
    (target : World → Outcome)
    {Observation : Type*}
    (observe : World → Observation)
    (sufficient : ∀ left right,
      observe left = observe right → target left = target right) :
    ∃ factor : Set.range observe → TaskQuotient target,
      ∀ world,
        factor ⟨observe world, ⟨world, rfl⟩⟩ =
          taskQuotientObservation target world := by
  classical
  refine ⟨reachableTaskQuotientFactor target observe, ?_⟩
  intro world
  unfold reachableTaskQuotientFactor
  apply Quotient.sound (s := taskEqSetoid target)
  exact sufficient (Classical.choose (show ∃ candidate, observe candidate = observe world
      from ⟨world, rfl⟩)) world
    ((Classical.choose_spec (show ∃ candidate, observe candidate = observe world
      from ⟨world, rfl⟩)).trans rfl)

/-- The task quotient of an empty world is empty. -/
theorem taskQuotient_isEmpty_of_empty_world
    {Outcome : Type*} (target : Empty → Outcome) :
    IsEmpty (TaskQuotient target) := by
  constructor
  intro quotient
  refine Quotient.inductionOn quotient ?_
  intro world
  exact nomatch world

/-- A total factor into an empty quotient is impossible for a nonempty
observation codomain.  This is the explicit empty-world regression boundary. -/
theorem no_total_task_factor_empty_world_nonempty_observation
    {Outcome Observation : Type*}
    (target : Empty → Outcome)
    [Nonempty Observation] :
    IsEmpty (Observation → TaskQuotient target) := by
  letI : IsEmpty (TaskQuotient target) :=
    taskQuotient_isEmpty_of_empty_world target
  constructor
  intro factor
  exact isEmptyElim (factor (Classical.choice inferInstance))

/-- Task equivalence can hold for distinct world objects. -/
theorem task_equivalence_does_not_imply_world_identity :
    ∃ target : Bool → Unit,
      TaskEq target false true ∧ false ≠ true := by
  refine ⟨fun _ => (), ?_, ?_⟩
  · rfl
  · decide

/-- Passive/task equivalence can hold while a declared next map diverges. -/
theorem passive_equivalence_does_not_imply_continuation_identity :
    ∃ passive : Bool → Unit, ∃ next : Bool → Bool,
      TaskEq passive false true ∧ next false ≠ next true := by
  refine ⟨fun _ => (), id, ?_, ?_⟩
  · rfl
  · decide

end OCKIndividuationMSpaceComposition
