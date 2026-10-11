import OCMaturityCompletionCycle.DynamicsCapability
import OCMaturityCompletionCycle.FiniteProbabilityTV
import OCMaturityCompletionCycle.StochasticOpen
import Mathlib.Algebra.BigOperators.Fin

/-!
# Connected finite open-process semantics

The primitive process kernel is normalized.  A finite experiment contains an
initial probability and an open-loop policy; its path weight is computed from
those primitives and is never supplied independently.  A separately proposed
normalized path law counts as realized only when it equals this induced weight.
-/

namespace OCMaturityCompletionCycle

universe uState uContext uBoundary uAction uAbstractState uAbstractContext
  uAbstractBoundary uAbstractAction uOccurrence

/-- Context, boundary condition, and intervention supplied to one process step. -/
abbrev OpenControl
    (Context : Type uContext)
    (Boundary : Type uBoundary)
    (Action : Type uAction) :=
  Context × Boundary × Action

/-- A normalized finite controlled process with explicit open inputs. -/
structure FiniteOpenProcess
    (State : Type uState)
    (Context : Type uContext)
    (Boundary : Type uBoundary)
    (Action : Type uAction)
    [Fintype State] where
  transition : FiniteControlledKernel State (OpenControl Context Boundary Action)
  capabilities : DynamicsCapabilityProfile

/-- A typed abstraction between one fine and one normalized abstract process. -/
structure ContextualAbstraction
    (State : Type uState)
    (Context : Type uContext)
    (Boundary : Type uBoundary)
    (Action : Type uAction)
    (AbstractState : Type uAbstractState)
    (AbstractContext : Type uAbstractContext)
    (AbstractBoundary : Type uAbstractBoundary)
    (AbstractAction : Type uAbstractAction)
    [Fintype State]
    [Fintype AbstractState] where
  fine : FiniteOpenProcess State Context Boundary Action
  abstract : FiniteOpenProcess
    AbstractState AbstractContext AbstractBoundary AbstractAction
  stateMap : State → AbstractState
  /-- Context-indexed history encoder `q_chi`. -/
  historyEncoder : Context → List State → AbstractState
  contextMap : Context → AbstractContext
  boundaryMap : Boundary → AbstractBoundary
  actionMap : Action → AbstractAction

/-- Continuation evidence and identity assembly remain different relations. -/
structure IdentityPresentation
    (Occurrence : Type uOccurrence)
    (State : Type uState) where
  stateOf : Occurrence → State
  continuationEvidence : Occurrence → Occurrence → Prop
  assembledTogether : Occurrence → Occurrence → Prop

/--
Identity is compatible with the abstract state only when assembled occurrences
receive the same abstract state.  This is an independent gate.
-/
def IdentityStateCompatibility
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    {Occurrence : Type uOccurrence}
    [Fintype State]
    [Fintype AbstractState]
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction)
    (identity : IdentityPresentation Occurrence State) : Prop :=
  ∀ ⦃left right⦄,
    identity.assembledTogether left right →
      abstraction.stateMap (identity.stateOf left) =
        abstraction.stateMap (identity.stateOf right)

/-- A finite state path represented recursively by its prefix and new endpoint. -/
def FiniteStatePath (State : Type uState) : Nat → Type uState
  | 0 => State
  | horizon + 1 => FiniteStatePath State horizon × State

instance finiteStatePathFintype
    (State : Type uState)
    [Fintype State] :
    ∀ horizon, Fintype (FiniteStatePath State horizon)
  | 0 => inferInstanceAs (Fintype State)
  | horizon + 1 =>
      letI : Fintype (FiniteStatePath State horizon) :=
        finiteStatePathFintype State horizon
      inferInstanceAs (Fintype (FiniteStatePath State horizon × State))

instance finiteStatePathDecidableEq
    (State : Type uState)
    [DecidableEq State] :
    ∀ horizon, DecidableEq (FiniteStatePath State horizon)
  | 0 => inferInstanceAs (DecidableEq State)
  | horizon + 1 =>
      letI : DecidableEq (FiniteStatePath State horizon) :=
        finiteStatePathDecidableEq State horizon
      inferInstanceAs (DecidableEq (FiniteStatePath State horizon × State))

/-- Last endpoint of a recursively represented finite path. -/
def finiteStatePathLast
    {State : Type uState} :
    ∀ horizon, FiniteStatePath State horizon → State
  | 0, state => state
  | _ + 1, path => path.2

/--
A finite experiment is process + initial law + policy.  It contains no
independently selected path law.
-/
structure FinitePathExperiment
    (State : Type uState)
    (Context : Type uContext)
    (Boundary : Type uBoundary)
    (Action : Type uAction)
    [Fintype State] where
  process : FiniteOpenProcess State Context Boundary Action
  horizon : Nat
  initial : FiniteProbabilityMass State
  /-- Frozen schedule; the experiment consumes its first `horizon` entries. -/
  policy : Nat → OpenControl Context Boundary Action

/-- Recursive product-form path weight induced by one normalized kernel. -/
def inducedPathWeightAt
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    [Fintype State]
    (process : FiniteOpenProcess State Context Boundary Action)
    (initial : FiniteProbabilityMass State)
    (policy : Nat → OpenControl Context Boundary Action) :
    ∀ horizon, FiniteStatePath State horizon → ℚ
  | 0, state => initial.mass state
  | horizon + 1, path =>
      inducedPathWeightAt process initial policy horizon path.1 *
        process.transition.mass
          (finiteStatePathLast horizon path.1)
          (policy horizon)
          path.2

/-- The experiment's path weight is definitionally induced, never supplied. -/
def inducedFinitePathWeight
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    [Fintype State]
    (experiment : FinitePathExperiment State Context Boundary Action) :
    FiniteStatePath State experiment.horizon → ℚ :=
  inducedPathWeightAt experiment.process experiment.initial
    experiment.policy experiment.horizon

/-- Recursive induced path weights are nonnegative at every horizon. -/
theorem inducedPathWeightAt_nonnegative
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    [Fintype State]
    (process : FiniteOpenProcess State Context Boundary Action)
    (initial : FiniteProbabilityMass State)
    (policy : Nat → OpenControl Context Boundary Action) :
    ∀ horizon path,
      0 ≤ inducedPathWeightAt process initial policy horizon path := by
  intro horizon
  induction horizon with
  | zero =>
      intro path
      exact initial.nonnegative path
  | succ prior inductionHypothesis =>
      intro path
      exact mul_nonneg (inductionHypothesis path.1)
        (process.transition.nonnegative
          (finiteStatePathLast prior path.1)
          (policy prior) path.2)

/-- Induced finite path weights are nonnegative. -/
theorem inducedFinitePathWeight_nonnegative
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    [Fintype State]
    (experiment : FinitePathExperiment State Context Boundary Action)
    (path : FiniteStatePath State experiment.horizon) :
    0 ≤ inducedFinitePathWeight experiment path :=
  inducedPathWeightAt_nonnegative experiment.process experiment.initial
    experiment.policy experiment.horizon path

/-- The induced path weights sum to one at every finite horizon. -/
theorem inducedPathWeightAt_normalized
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    [Fintype State]
    (process : FiniteOpenProcess State Context Boundary Action)
    (initial : FiniteProbabilityMass State)
    (policy : Nat → OpenControl Context Boundary Action) :
    ∀ horizon,
      ∑ path : FiniteStatePath State horizon,
        inducedPathWeightAt process initial policy horizon path = 1 := by
  intro horizon
  induction horizon with
  | zero => exact initial.normalized
  | succ prior inductionHypothesis =>
      change
        (∑ path : FiniteStatePath State prior × State,
          inducedPathWeightAt process initial policy prior path.1 *
            process.transition.mass
              (finiteStatePathLast prior path.1) (policy prior) path.2) = 1
      rw [Fintype.sum_prod_type]
      calc
        (∑ pathPrefix : FiniteStatePath State prior,
          ∑ endpoint : State,
            inducedPathWeightAt process initial policy prior pathPrefix *
              process.transition.mass
                (finiteStatePathLast prior pathPrefix) (policy prior) endpoint) =
            ∑ pathPrefix : FiniteStatePath State prior,
              inducedPathWeightAt process initial policy prior pathPrefix *
                (∑ endpoint : State,
                  process.transition.mass
                    (finiteStatePathLast prior pathPrefix) (policy prior) endpoint) := by
          apply Finset.sum_congr rfl
          intro pathPrefix _
          rw [Finset.mul_sum]
        _ = ∑ pathPrefix : FiniteStatePath State prior,
              inducedPathWeightAt process initial policy prior pathPrefix := by
          apply Finset.sum_congr rfl
          intro pathPrefix _
          rw [process.transition.normalized]
          simp
        _ = 1 := inductionHypothesis

/-- Actual normalized path law induced by the primitive process and policy. -/
def inducedFinitePathLaw
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    [Fintype State]
    (experiment : FinitePathExperiment State Context Boundary Action) :
    FiniteProbabilityMass (FiniteStatePath State experiment.horizon) where
  mass := inducedFinitePathWeight experiment
  nonnegative := inducedFinitePathWeight_nonnegative experiment
  normalized := inducedPathWeightAt_normalized experiment.process
    experiment.initial experiment.policy experiment.horizon

/--
A normalized candidate law is realized exactly when its mass is the induced
kernel/policy path weight.  The candidate cannot bypass the primitive process.
-/
def LawRealization
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    [Fintype State]
    (experiment : FinitePathExperiment State Context Boundary Action)
    (candidate : FiniteProbabilityMass
      (FiniteStatePath State experiment.horizon)) : Prop :=
  candidate.mass = (inducedFinitePathLaw experiment).mass

/-- Exact one-step commutation for the linked normalized processes. -/
def ContextualKernelCommutes
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction) : Prop :=
  ∀ state context boundary action target,
    abstraction.abstract.transition.mass
        (abstraction.stateMap state)
        (abstraction.contextMap context,
          abstraction.boundaryMap boundary,
          abstraction.actionMap action)
        target =
      pushedMass abstraction.fine.transition abstraction.stateMap
        state (context, boundary, action) target

end OCMaturityCompletionCycle
