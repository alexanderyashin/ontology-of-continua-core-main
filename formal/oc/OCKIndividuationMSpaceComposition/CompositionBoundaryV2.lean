import OCKIndividuationMSpaceComposition.RecursiveComposition
import Mathlib.Order.WellFounded

namespace OCKIndividuationMSpaceComposition

universe uObject

/-!
# Infinite, cyclic, and non-well-founded composition boundary

`MultiLevelDecomposition` remains the finite reflexive-transitive closure of a
local realization rule.  This additive module does not turn that inductive
closure into a coinductive final object.  Instead it records an explicitly
productive `Nat`-indexed stream of local rewrites.  Every finite prefix factors
through the existing finite theory, while well-foundedness is exactly the
extra hypothesis that excludes such a stream.

The constructions are structural.  A domain must still justify that its local
`RealizesChildren` relation means causal constitution, proper parthood, or an
empirically admissible refinement.
-/

/-- An infinite productive sequence of local decomposition rewrites. -/
structure OmegaDecomposition
    {Object : Type uObject}
    (realizes : RealizesChildren Object)
    (start : List Object) where
  stage : Nat -> List Object
  starts : stage 0 = start
  productive : forall depth,
    DecompositionStep realizes (stage depth) (stage (depth + 1))

/-- A stage is terminal exactly when no further local rewrite is admitted. -/
def IsTerminalDecomposition
    {Object : Type uObject}
    (realizes : RealizesChildren Object)
    (objects : List Object) : Prop :=
  forall next, Not (DecompositionStep realizes objects next)

namespace OmegaDecomposition

/-- Every finite prefix of an omega decomposition is in the old finite closure. -/
theorem finitePrefix
    {Object : Type uObject}
    {realizes : RealizesChildren Object}
    {start : List Object}
    (omega : OmegaDecomposition realizes start) :
    forall depth,
      MultiLevelDecomposition realizes start (omega.stage depth) := by
  intro depth
  induction depth with
  | zero => simpa [omega.starts] using
      (multiLevelDecomposition_refl realizes start)
  | succ depth inductionHypothesis =>
      exact RelationReachable.tail inductionHypothesis
        (by simpa [Nat.succ_eq_add_one] using omega.productive depth)

/-- Productivity excludes a terminal stage at every finite depth. -/
theorem noFiniteStageTerminal
    {Object : Type uObject}
    {realizes : RealizesChildren Object}
    {start : List Object}
    (omega : OmegaDecomposition realizes start)
    (depth : Nat) :
    Not (IsTerminalDecomposition realizes (omega.stage depth)) := by
  intro terminal
  exact terminal (omega.stage (depth + 1)) (omega.productive depth)

end OmegaDecomposition

/-- The descending relation corresponding to forward decomposition. -/
def DecompositionDescent
    {Object : Type uObject}
    (realizes : RealizesChildren Object) :
    List Object -> List Object -> Prop :=
  fun later earlier => DecompositionStep realizes earlier later

/--
Well-foundedness is the generic barrier to countable successor rewrite chains:
a well-founded decomposition descent admits no `Nat`-indexed omega
decomposition from any start.
-/
theorem wellFounded_excludes_omegaDecomposition
    {Object : Type uObject}
    {realizes : RealizesChildren Object}
    (wellFounded : WellFounded (DecompositionDescent realizes))
    (start : List Object) :
    IsEmpty (OmegaDecomposition realizes start) := by
  constructor
  intro omega
  let InStream : List Object -> Prop :=
    fun current =>
      (exists depth, current = omega.stage depth) -> False
  have descends : forall current,
      (forall later,
        DecompositionDescent realizes later current -> InStream later) ->
        InStream current := by
    intro current smaller
    rintro ⟨depth, same⟩
    have edge : DecompositionDescent realizes
        (omega.stage (depth + 1)) current := by
      rw [same]
      exact omega.productive depth
    exact smaller (omega.stage (depth + 1)) edge ⟨depth + 1, rfl⟩
  exact (wellFounded.induction (omega.stage 0) descends) ⟨0, rfl⟩

/--
A supplied productive omega decomposition constructively refutes
well-foundedness.  This direction performs no extraction from a negated
proposition and does not invoke classical choice.
-/
theorem OmegaDecomposition.implies_not_wellFounded
    {Object : Type uObject}
    {realizes : RealizesChildren Object}
    {start : List Object}
    (omega : OmegaDecomposition realizes start) :
    Not (WellFounded (DecompositionDescent realizes)) := by
  intro wellFounded
  exact (wellFounded_excludes_omegaDecomposition wellFounded start).false
    omega

/--
Exact global characterization: the decomposition descent is well-founded if
and only if no start presentation admits a productive omega decomposition.
The `WellFounded -> no omega` direction and the obstruction from a supplied
omega are constructive.  The reverse `no omega -> WellFounded` direction uses
Mathlib's descending-chain characterization and inherits `Classical.choice`;
it is not an algorithm extracting accessibility evidence.
-/
theorem decompositionDescent_wellFounded_iff_no_omega
    {Object : Type uObject}
    (realizes : RealizesChildren Object) :
    WellFounded (DecompositionDescent realizes) <->
      forall start : List Object,
        IsEmpty (OmegaDecomposition realizes start) := by
  constructor
  · intro wellFounded start
    exact wellFounded_excludes_omegaDecomposition wellFounded start
  · intro noOmega
    apply wellFounded_iff_isEmpty_descending_chain.mpr
    constructor
    intro chain
    exact (noOmega (chain.1 0)).false
      ({
        stage := chain.1
        starts := rfl
        productive := chain.2
      } : OmegaDecomposition realizes (chain.1 0))

/--
Classical existence form of the converse boundary.  Failure of
well-foundedness yields an explicitly productive `Nat`-indexed decomposition
from some start.  The witness extraction uses classical reasoning; the
forward theorem `wellFounded_excludes_omegaDecomposition` does not.

This is a statement about countable successor chains.  It neither constructs
an ordinal-indexed decomposition nor asserts transfinite closure.
-/
theorem not_wellFounded_iff_exists_omegaDecomposition_classical
    {Object : Type uObject}
    (realizes : RealizesChildren Object) :
    Not (WellFounded (DecompositionDescent realizes)) <->
      exists start : List Object,
        Nonempty (OmegaDecomposition realizes start) := by
  classical
  constructor
  · intro notWellFounded
    by_contra noWitness
    apply notWellFounded
    exact (decompositionDescent_wellFounded_iff_no_omega realizes).2
      (fun start =>
        {
          false := fun omega => noWitness
            (Exists.intro start (Nonempty.intro omega))
        })
  · rintro ⟨start, ⟨omega⟩⟩ wellFounded
    exact (wellFounded_excludes_omegaDecomposition wellFounded start).false
      omega

/-!
## Cyclic organization
-/

/-- A separated direct two-cycle of local decomposition rewrites. -/
structure DirectTwoCycle
    {Object : Type uObject}
    (realizes : RealizesChildren Object)
    (first second : List Object) : Prop where
  distinct : first ≠ second
  forward : DecompositionStep realizes first second
  backward : DecompositionStep realizes second first

/-- Pair-valued alternation avoids choosing equality or a parity encoding. -/
def alternatingPair
    {Object : Type uObject}
    (first second : List Object) : Nat -> Prod (List Object) (List Object)
  | 0 => (first, second)
  | depth + 1 =>
      let previous := alternatingPair first second depth
      (previous.2, previous.1)

/-- The first coordinate of the alternating pair. -/
def alternatingStage
    {Object : Type uObject}
    (first second : List Object)
    (depth : Nat) : List Object :=
  (alternatingPair first second depth).1

theorem alternatingPair_orientation
    {Object : Type uObject}
    (first second : List Object) :
    forall depth,
      alternatingPair first second depth = (first, second) \/
        alternatingPair first second depth = (second, first) := by
  intro depth
  induction depth with
  | zero => exact Or.inl rfl
  | succ depth inductionHypothesis =>
      rcases inductionHypothesis with orientation | orientation
      · exact Or.inr (by simp [alternatingPair, orientation])
      · exact Or.inl (by simp [alternatingPair, orientation])

/-- Every separated direct two-cycle unfolds to a productive omega decomposition. -/
def DirectTwoCycle.toOmega
    {Object : Type uObject}
    {realizes : RealizesChildren Object}
    {first second : List Object}
    (cycle : DirectTwoCycle realizes first second) :
    OmegaDecomposition realizes first where
  stage := alternatingStage first second
  starts := rfl
  productive := by
    intro depth
    rcases alternatingPair_orientation first second depth with
      orientation | orientation
    · simpa [alternatingStage, alternatingPair, orientation] using cycle.forward
    · simpa [alternatingStage, alternatingPair, orientation] using cycle.backward

/-- The omega stream generated by a separated two-cycle changes at every step. -/
theorem DirectTwoCycle.toOmega_nonstationary
    {Object : Type uObject}
    {realizes : RealizesChildren Object}
    {first second : List Object}
    (cycle : DirectTwoCycle realizes first second)
    (depth : Nat) :
    cycle.toOmega.stage depth ≠ cycle.toOmega.stage (depth + 1) := by
  rcases alternatingPair_orientation first second depth with
    orientation | orientation
  · simpa [DirectTwoCycle.toOmega, alternatingStage, alternatingPair,
      orientation] using cycle.distinct
  · simpa [DirectTwoCycle.toOmega, alternatingStage, alternatingPair,
      orientation] using cycle.distinct.symm

/-!
## Productive non-cyclic refinement fixture
-/

/-- Each natural-labeled object refines to its strict successor. -/
def SuccessorRealization : RealizesChildren Nat :=
  fun children parent => children = [parent + 1]

theorem successorRealization_step (depth : Nat) :
    DecompositionStep SuccessorRealization [depth] [depth + 1] := by
  simpa using
    (DecompositionStep.replace
      (realizes := SuccessorRealization)
      [] [depth + 1] [] depth rfl)

/-- A productive infinite refinement with no repeated stages. -/
def successorOmega : OmegaDecomposition SuccessorRealization [0] where
  stage := fun depth => [depth]
  starts := rfl
  productive := successorRealization_step

/-- The successor fixture is non-periodic, so productivity does not imply a cycle. -/
theorem successorOmega_stage_injective :
    Function.Injective successorOmega.stage := by
  intro first second sameStage
  simpa [successorOmega] using List.cons.inj sameStage |>.1

/-- No finite stage of the successor fixture is a terminal atom. -/
theorem successorOmega_has_no_terminal_stage :
    forall depth,
      Not (IsTerminalDecomposition SuccessorRealization
        (successorOmega.stage depth)) :=
  successorOmega.noFiniteStageTerminal

/-!
The two fixtures separate the cases required by the theory boundary:

* a finite well-founded realization has no omega chain;
* a cyclic realization may generate a nonstationary omega chain;
* a productive omega chain need not be cyclic or eventually periodic; and
* every finite prefix remains exactly an old `MultiLevelDecomposition`.

No statement selects a universal terminal atom, and no final-coalgebra or
coinductive-universality claim is made.  Ordinal-indexed chains, limit stages,
and transfinite closure are outside this module.
-/

end OCKIndividuationMSpaceComposition
