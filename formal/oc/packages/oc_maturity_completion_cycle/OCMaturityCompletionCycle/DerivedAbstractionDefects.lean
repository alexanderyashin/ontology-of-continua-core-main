import OCMaturityCompletionCycle.AbstractionDefect
import Mathlib.Tactic.DeriveFintype

/-!
# Defects derived from one linked abstraction

Unlike the generic comparison lemmas, every constructor here reads laws from
one `ContextualAbstraction`.  Nonmatching state/context/boundary pairs compare a
law with itself, so they contribute zero; matching encoded pairs test the exact
representative-independence requirement.
-/

namespace OCMaturityCompletionCycle

universe uState uContext uBoundary uAction uAbstractState uAbstractContext
  uAbstractBoundary uAbstractAction uOccurrence

/-- One normalized row of a primitive finite kernel. -/
def finiteTransitionProbability
    {State : Type uState}
    {Input : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Input)
    (state : State)
    (input : Input) : FiniteProbabilityMass State where
  mass := kernel.mass state input
  nonnegative := kernel.nonnegative state input
  normalized := kernel.normalized state input

structure FineStepIndex
    (State : Type uState)
    (Context : Type uContext)
    (Boundary : Type uBoundary)
    (Action : Type uAction) where
  state : State
  context : Context
  boundary : Boundary
  action : Action
  deriving Fintype

structure FineStatePairStepIndex
    (State : Type uState)
    (Context : Type uContext)
    (Boundary : Type uBoundary)
    (Action : Type uAction) where
  left : State
  right : State
  context : Context
  boundary : Boundary
  action : Action
  deriving Fintype

structure FineBoundaryPairStepIndex
    (State : Type uState)
    (Context : Type uContext)
    (Boundary : Type uBoundary)
    (Action : Type uAction) where
  state : State
  context : Context
  leftBoundary : Boundary
  rightBoundary : Boundary
  action : Action
  deriving Fintype

structure FineContextPairStepIndex
    (State : Type uState)
    (Context : Type uContext)
    (Boundary : Type uBoundary)
    (Action : Type uAction) where
  state : State
  leftContext : Context
  rightContext : Context
  boundary : Boundary
  action : Action
  deriving Fintype

/-- Fine one-step law observed through the abstraction's state map. -/
def pushedFineStepLaw
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
      AbstractState AbstractContext AbstractBoundary AbstractAction)
    (state : State) (context : Context) (boundary : Boundary) (action : Action) :
    FiniteProbabilityMass AbstractState :=
  pushforwardFiniteProbability abstraction.stateMap
    (finiteTransitionProbability abstraction.fine.transition state
      (context, boundary, action))

/-- Declared abstract one-step law at mapped inputs. -/
def declaredAbstractStepLaw
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
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction)
    (state : State) (context : Context) (boundary : Boundary) (action : Action) :
    FiniteProbabilityMass AbstractState :=
  finiteTransitionProbability abstraction.abstract.transition
    (abstraction.stateMap state)
    (abstraction.contextMap context,
      abstraction.boundaryMap boundary,
      abstraction.actionMap action)

/-- Prediction laws are derived from the fine and declared abstract kernels. -/
def derivedPredictionComparison
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype Context] [Fintype Boundary] [Fintype Action]
    [Fintype AbstractState] [DecidableEq AbstractState]
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction) :
    FiniteLawComparison (FineStepIndex State Context Boundary Action)
      AbstractState where
  reference index := pushedFineStepLaw abstraction index.state index.context
    index.boundary index.action
  abstracted index := declaredAbstractStepLaw abstraction index.state index.context
    index.boundary index.action

/-- Representative-independence comparison, derived from fine kernel rows. -/
def derivedLumpabilityComparison
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype Context] [Fintype Boundary] [Fintype Action]
    [Fintype AbstractState] [DecidableEq AbstractState]
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction) :
    FiniteLawComparison (FineStatePairStepIndex State Context Boundary Action)
      AbstractState where
  reference index := pushedFineStepLaw abstraction index.left index.context
    index.boundary index.action
  abstracted index :=
    if abstraction.stateMap index.left = abstraction.stateMap index.right then
      pushedFineStepLaw abstraction index.right index.context index.boundary index.action
    else
      pushedFineStepLaw abstraction index.left index.context index.boundary index.action

/-- Boundary congruence comparison, derived from mapped-boundary collisions. -/
def derivedBoundaryComparison
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype Context] [Fintype Boundary] [Fintype Action]
    [Fintype AbstractState] [DecidableEq AbstractState]
    [DecidableEq AbstractBoundary]
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction) :
    FiniteLawComparison (FineBoundaryPairStepIndex State Context Boundary Action)
      AbstractState where
  reference index := pushedFineStepLaw abstraction index.state index.context
    index.leftBoundary index.action
  abstracted index :=
    if abstraction.boundaryMap index.leftBoundary =
        abstraction.boundaryMap index.rightBoundary then
      pushedFineStepLaw abstraction index.state index.context
        index.rightBoundary index.action
    else
      pushedFineStepLaw abstraction index.state index.context
        index.leftBoundary index.action

/-- Context naturality comparison, derived from mapped-context collisions. -/
def derivedContextComparison
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype Context] [Fintype Boundary] [Fintype Action]
    [Fintype AbstractState] [DecidableEq AbstractState]
    [DecidableEq AbstractContext]
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction) :
    FiniteLawComparison (FineContextPairStepIndex State Context Boundary Action)
      AbstractState where
  reference index := pushedFineStepLaw abstraction index.state index.leftContext
    index.boundary index.action
  abstracted index :=
    if abstraction.contextMap index.leftContext =
        abstraction.contextMap index.rightContext then
      pushedFineStepLaw abstraction index.state index.rightContext
        index.boundary index.action
    else
      pushedFineStepLaw abstraction index.state index.leftContext
        index.boundary index.action

/-- Map every endpoint of a finite path through the state abstraction. -/
def mapFiniteStatePath
    {State : Type uState}
    {AbstractState : Type uAbstractState}
    (stateMap : State → AbstractState) :
    ∀ horizon, FiniteStatePath State horizon → FiniteStatePath AbstractState horizon
  | 0, state => stateMap state
  | horizon + 1, path =>
      (mapFiniteStatePath stateMap horizon path.1, stateMap path.2)

/-- Data needed to derive both fine and abstract experiments from one abstraction. -/
structure AlignedFinitePathData
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
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction) where
  horizon : Nat
  fineInitial : FiniteProbabilityMass State
  finePolicy : Nat → OpenControl Context Boundary Action

def AlignedFinitePathData.fineExperiment
    {State : Type uState} {Context : Type uContext} {Boundary : Type uBoundary}
    {Action : Type uAction} {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype AbstractState]
    {abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction}
    (data : AlignedFinitePathData abstraction) :
    FinitePathExperiment State Context Boundary Action where
  process := abstraction.fine
  horizon := data.horizon
  initial := data.fineInitial
  policy := data.finePolicy

def AlignedFinitePathData.abstractExperiment
    {State : Type uState} {Context : Type uContext} {Boundary : Type uBoundary}
    {Action : Type uAction} {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype AbstractState] [DecidableEq AbstractState]
    {abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction}
    (data : AlignedFinitePathData abstraction) :
    FinitePathExperiment AbstractState AbstractContext AbstractBoundary AbstractAction where
  process := abstraction.abstract
  horizon := data.horizon
  initial := pushforwardFiniteProbability abstraction.stateMap data.fineInitial
  policy step :=
    (abstraction.contextMap (data.finePolicy step).1,
      abstraction.boundaryMap (data.finePolicy step).2.1,
      abstraction.actionMap (data.finePolicy step).2.2)

/-- Stitching compares induced fine pushforward with one normalized candidate. -/
def derivedStitchingComparison
    {State : Type uState} {Context : Type uContext} {Boundary : Type uBoundary}
    {Action : Type uAction} {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype AbstractState] [DecidableEq AbstractState]
    {abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction}
    (data : AlignedFinitePathData abstraction)
    (candidate : FiniteProbabilityMass
      (FiniteStatePath AbstractState data.horizon)) :
    FiniteLawComparison Unit (FiniteStatePath AbstractState data.horizon) where
  reference _ :=
    pushforwardFiniteProbability
      (mapFiniteStatePath abstraction.stateMap data.horizon)
      (inducedFinitePathLaw data.fineExperiment)
  abstracted _ := candidate

/-- Five concrete defects computed from one abstraction and aligned path data. -/
structure DerivedAbstractionDefect where
  prediction : ℚ
  lumpability : ℚ
  boundary : ℚ
  context : ℚ
  stitching : ℚ
  memoryCost : Nat
  stateCost : Nat
  resourceCost : Nat

def derivedAbstractionDefect
    {State : Type uState} {Context : Type uContext} {Boundary : Type uBoundary}
    {Action : Type uAction} {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype Context] [Fintype Boundary] [Fintype Action]
    [Fintype AbstractState] [DecidableEq AbstractState]
    [DecidableEq AbstractContext] [DecidableEq AbstractBoundary]
    {abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction}
    (data : AlignedFinitePathData abstraction)
    (candidate : FiniteProbabilityMass
      (FiniteStatePath AbstractState data.horizon))
    (memoryCost stateCost resourceCost : Nat) : DerivedAbstractionDefect where
  prediction := (derivedPredictionComparison abstraction).defect
  lumpability := (derivedLumpabilityComparison abstraction).defect
  boundary := (derivedBoundaryComparison abstraction).defect
  context := (derivedContextComparison abstraction).defect
  stitching := (derivedStitchingComparison data candidate).defect
  memoryCost := memoryCost
  stateCost := stateCost
  resourceCost := resourceCost

def DerivedAbstractionDefect.ZeroScientificComponents
    (defect : DerivedAbstractionDefect) : Prop :=
  defect.prediction = 0 ∧ defect.lumpability = 0 ∧ defect.boundary = 0 ∧
    defect.context = 0 ∧ defect.stitching = 0

def DerivedFiveExactness
    {State : Type uState} {Context : Type uContext} {Boundary : Type uBoundary}
    {Action : Type uAction} {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype Context] [Fintype Boundary] [Fintype Action]
    [Fintype AbstractState] [DecidableEq AbstractState]
    [DecidableEq AbstractContext] [DecidableEq AbstractBoundary]
    {abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction}
    (data : AlignedFinitePathData abstraction)
    (candidate : FiniteProbabilityMass
      (FiniteStatePath AbstractState data.horizon)) : Prop :=
  (derivedPredictionComparison abstraction).Exact ∧
    (derivedLumpabilityComparison abstraction).Exact ∧
    (derivedBoundaryComparison abstraction).Exact ∧
    (derivedContextComparison abstraction).Exact ∧
    (derivedStitchingComparison data candidate).Exact

/-- Concrete derived defects vanish exactly when all five derived laws agree. -/
theorem derivedScientificDefects_zero_iff_fiveExact
    {State : Type uState} {Context : Type uContext} {Boundary : Type uBoundary}
    {Action : Type uAction} {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State] [Fintype Context] [Fintype Boundary] [Fintype Action]
    [Fintype AbstractState] [DecidableEq AbstractState]
    [DecidableEq AbstractContext] [DecidableEq AbstractBoundary]
    {abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction}
    (data : AlignedFinitePathData abstraction)
    (candidate : FiniteProbabilityMass
      (FiniteStatePath AbstractState data.horizon))
    (memoryCost stateCost resourceCost : Nat) :
    DerivedAbstractionDefect.ZeroScientificComponents
        (derivedAbstractionDefect data candidate memoryCost stateCost resourceCost) ↔
      DerivedFiveExactness data candidate := by
  simp only [DerivedAbstractionDefect.ZeroScientificComponents,
    derivedAbstractionDefect, DerivedFiveExactness]
  rw [FiniteLawComparison.defect_eq_zero_iff_exact,
    FiniteLawComparison.defect_eq_zero_iff_exact,
    FiniteLawComparison.defect_eq_zero_iff_exact,
    FiniteLawComparison.defect_eq_zero_iff_exact,
    FiniteLawComparison.defect_eq_zero_iff_exact]

/-- Joint exactness with the actual identity and path-law gates. -/
def DerivedCoherentJointExactness
    {State : Type uState} {Context : Type uContext} {Boundary : Type uBoundary}
    {Action : Type uAction} {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction} {Occurrence : Type uOccurrence}
    [Fintype State] [Fintype Context] [Fintype Boundary] [Fintype Action]
    [Fintype AbstractState] [DecidableEq AbstractState]
    [DecidableEq AbstractContext] [DecidableEq AbstractBoundary]
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction)
    (identity : IdentityPresentation Occurrence State)
    (data : AlignedFinitePathData abstraction)
    (candidate : FiniteProbabilityMass
      (FiniteStatePath AbstractState data.horizon)) : Prop :=
  IdentityStateCompatibility abstraction identity ∧
    LawRealization data.abstractExperiment candidate ∧
    DerivedFiveExactness data candidate

/--
N1 synthesis with non-arbitrary gates: under actual compatibility and actual
kernel-induced law realization, zero derived defects characterize the declared
joint exactness.
-/
theorem derivedCoherentJointExactness_iff_zeroScientificDefects
    {State : Type uState} {Context : Type uContext} {Boundary : Type uBoundary}
    {Action : Type uAction} {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction} {Occurrence : Type uOccurrence}
    [Fintype State] [Fintype Context] [Fintype Boundary] [Fintype Action]
    [Fintype AbstractState] [DecidableEq AbstractState]
    [DecidableEq AbstractContext] [DecidableEq AbstractBoundary]
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction)
    (identity : IdentityPresentation Occurrence State)
    (data : AlignedFinitePathData abstraction)
    (candidate : FiniteProbabilityMass
      (FiniteStatePath AbstractState data.horizon))
    (identityGate : IdentityStateCompatibility abstraction identity)
    (lawGate : LawRealization data.abstractExperiment candidate)
    (memoryCost stateCost resourceCost : Nat) :
    DerivedCoherentJointExactness abstraction identity data candidate ↔
      DerivedAbstractionDefect.ZeroScientificComponents
        (derivedAbstractionDefect data candidate memoryCost stateCost resourceCost) := by
  rw [derivedScientificDefects_zero_iff_fiveExact]
  constructor
  · exact fun joint => joint.2.2
  · exact fun exactFive => ⟨identityGate, lawGate, exactFive⟩

end OCMaturityCompletionCycle
