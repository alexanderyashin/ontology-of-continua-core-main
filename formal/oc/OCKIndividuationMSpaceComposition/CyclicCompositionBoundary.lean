import OCKIndividuationMSpaceComposition.RecursiveComposition

namespace OCKIndividuationMSpaceComposition

universe uObject

/-!
# Finite paths through cyclic composition

`MultiLevelDecomposition` intentionally records reachability and therefore
forgets path length.  This additive layer restores a finite length index.  It
shows both what remains valid for a cyclic organization (every finite prefix
is a legitimate typed derivation) and what does not follow (well-foundedness
or a terminal atom).
-/

/-- A decomposition derivation with its exact number of local rewrite steps. -/
inductive ExactDecomposition
    {Object : Type uObject}
    (realizes : RealizesChildren Object) :
    Nat → List Object → List Object → Prop
  | zero (objects : List Object) :
      ExactDecomposition realizes 0 objects objects
  | succ {steps : Nat} {first middle terminal : List Object} :
      ExactDecomposition realizes steps first middle →
      DecompositionStep realizes middle terminal →
      ExactDecomposition realizes (steps + 1) first terminal

/-- Forgetting the exact length recovers the established finite multi-level
decomposition relation. -/
theorem ExactDecomposition.toMultiLevel
    {Object : Type uObject}
    {realizes : RealizesChildren Object}
    {steps : Nat} {first terminal : List Object}
    (decomposition : ExactDecomposition realizes steps first terminal) :
    MultiLevelDecomposition realizes first terminal := by
  induction decomposition with
  | zero => exact .root
  | succ previous step inductionHypothesis =>
      exact .tail inductionHypothesis step

/-- A two-state realization rule: every component is realized by its Boolean
opposite.  It is a typed cyclic organization, not an assertion about all
domains. -/
def AlternatingRealization : RealizesChildren Bool :=
  fun children parent => children = [!parent]

/-- The presentation reached after exactly `steps` alternating rewrites. -/
def alternatingObject (start : Bool) : Nat → Bool
  | 0 => start
  | steps + 1 => !alternatingObject start steps

/-- Every finite prefix of the alternating organization exists with exactly
the requested derivation length. -/
theorem alternating_has_exact_finite_prefix
    (start : Bool) :
    ∀ steps : Nat,
      ExactDecomposition AlternatingRealization steps [start]
        [alternatingObject start steps] := by
  intro steps
  induction steps with
  | zero => exact .zero [start]
  | succ steps inductionHypothesis =>
      refine .succ inductionHypothesis ?_
      simpa [AlternatingRealization, alternatingObject] using
        (DecompositionStep.replace
          (realizes := AlternatingRealization)
          [] [!alternatingObject start steps] []
          (alternatingObject start steps) rfl)

/-- A positive-length derivation relation.  Unlike reflexive reachability it
does not regard the zero-step presentation as a cycle. -/
def PositiveDecomposition
    {Object : Type uObject}
    (realizes : RealizesChildren Object) :
    List Object → List Object → Prop :=
  fun first terminal => ∃ steps, 0 < steps ∧
    ExactDecomposition realizes steps first terminal

/-- Two alternating rewrites return to the original singleton presentation. -/
theorem alternating_positive_two_step_cycle (start : Bool) :
    PositiveDecomposition AlternatingRealization [start] [start] := by
  refine ⟨2, by decide, ?_⟩
  simpa [alternatingObject] using
    (alternating_has_exact_finite_prefix start 2)

/-- A positive decomposition self-cycle makes the relation non-well-founded.
Thus a terminal-atom conclusion requires an additional acyclicity or
productivity contract; it cannot be inferred from local finite realization
rules alone. -/
theorem alternating_positive_decomposition_not_wellFounded :
    ¬ WellFounded (PositiveDecomposition AlternatingRealization) := by
  intro wellFounded
  have accessible : Acc (PositiveDecomposition AlternatingRealization) [false] :=
    wellFounded.apply [false]
  have impossible : [false] = [false] → False :=
    Acc.recOn accessible
      (motive := fun presentation _ => presentation = [false] → False)
      (by
        intro presentation predecessors inductionHypothesis presentationEq
        subst presentation
        exact inductionHypothesis [false]
          (alternating_positive_two_step_cycle false) rfl)
  exact impossible rfl

/-- The cyclic example has no terminal singleton presentation: each one admits
a nontrivial successor decomposition. -/
theorem alternating_singleton_is_not_terminal (start : Bool) :
    ∃ terminal, PositiveDecomposition AlternatingRealization [start] terminal := by
  refine ⟨[!start], 1, by decide, ?_⟩
  simpa [alternatingObject] using
    (alternating_has_exact_finite_prefix start 1)

end OCKIndividuationMSpaceComposition
