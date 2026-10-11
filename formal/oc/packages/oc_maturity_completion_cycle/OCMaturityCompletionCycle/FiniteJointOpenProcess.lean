import OCMaturityCompletionCycle.ContextualOpenDynamics
import OCMaturityCompletionCycle.FiniteTVComposition

/-!
# Finite open processes with joint state/boundary output

The primitive one-step law is normalized on `(nextState × boundaryOut)`.  This
keeps state/output correlation and distinguishes an open process from the older
controlled-input state kernel.  Every path law below is induced from that joint
kernel and a frozen input policy.
-/

namespace OCMaturityCompletionCycle

universe uState uContext uBoundaryIn uAction uBoundaryOut
  uAbstractState uAbstractContext uAbstractBoundaryIn uAbstractAction
  uAbstractBoundaryOut

/-- Context, boundary input, and intervention supplied to one joint open step. -/
abbrev JointOpenControl
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction) :=
  Context × BoundaryIn × Action

/--
A normalized finite open process whose primitive outcome preserves the joint
law of next state and emitted boundary value.
-/
structure FiniteJointOpenProcess
    (State : Type uState)
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction)
    (BoundaryOut : Type uBoundaryOut)
    [Fintype State]
    [Fintype BoundaryOut] where
  mass : State → JointOpenControl Context BoundaryIn Action →
    State × BoundaryOut → ℚ
  nonnegative : ∀ state control outcome, 0 ≤ mass state control outcome
  normalized : ∀ state control, ∑ outcome, mass state control outcome = 1

/-- The normalized joint law for one state and one open control. -/
def jointStepProbability
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut)
    (state : State)
    (control : JointOpenControl Context BoundaryIn Action) :
    FiniteProbabilityMass (State × BoundaryOut) where
  mass := process.mass state control
  nonnegative := process.nonnegative state control
  normalized := process.normalized state control

/-- State marginal of the joint open kernel. -/
def jointOpenStateMarginalKernel
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut) :
    FiniteControlledKernel State (JointOpenControl Context BoundaryIn Action) where
  mass state control target :=
    ∑ output, process.mass state control (target, output)
  nonnegative state control target :=
    Finset.sum_nonneg fun output _ =>
      process.nonnegative state control (target, output)
  normalized state control := by
    rw [← Fintype.sum_prod_type]
    exact process.normalized state control

/-- Boundary-output marginal derived from the joint step law. -/
def jointBoundaryOutputProbability
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [DecidableEq BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut)
    (state : State)
    (control : JointOpenControl Context BoundaryIn Action) :
    FiniteProbabilityMass BoundaryOut :=
  pushforwardFiniteProbability Prod.snd
    (jointStepProbability process state control)

/--
A finite path records the initial state and every joint state/output step.

The zero-horizon state is explicitly lifted into the joint path universe.  This
retains independent universes for states and boundary outputs; successor paths
remain the product of a prefix with one joint state/output outcome.
-/
def FiniteStateOutputPath
    (State : Type uState)
    (BoundaryOut : Type uBoundaryOut) : Nat → Type (max uState uBoundaryOut)
  | 0 => ULift.{uBoundaryOut, uState} State
  | horizon + 1 =>
      FiniteStateOutputPath State BoundaryOut horizon × (State × BoundaryOut)

/-- Zero-horizon paths contain exactly one lifted initial state. -/
def finiteStateOutputPathZeroEquiv
    (State : Type uState)
    (BoundaryOut : Type uBoundaryOut) :
    State ≃ FiniteStateOutputPath State BoundaryOut 0 where
  toFun := ULift.up
  invFun := ULift.down
  left_inv _ := rfl
  right_inv _ := rfl

instance finiteStateOutputPathFintype
    (State : Type uState)
    (BoundaryOut : Type uBoundaryOut)
    [Fintype State]
    [Fintype BoundaryOut] :
    ∀ horizon, Fintype (FiniteStateOutputPath State BoundaryOut horizon)
  | 0 => inferInstanceAs (Fintype (ULift.{uBoundaryOut, uState} State))
  | horizon + 1 =>
      letI : Fintype (FiniteStateOutputPath State BoundaryOut horizon) :=
        finiteStateOutputPathFintype State BoundaryOut horizon
      inferInstanceAs
        (Fintype (FiniteStateOutputPath State BoundaryOut horizon ×
          (State × BoundaryOut)))

instance finiteStateOutputPathDecidableEq
    (State : Type uState)
    (BoundaryOut : Type uBoundaryOut)
    [DecidableEq State]
    [DecidableEq BoundaryOut] :
    ∀ horizon, DecidableEq (FiniteStateOutputPath State BoundaryOut horizon)
  | 0 => inferInstanceAs (DecidableEq (ULift.{uBoundaryOut, uState} State))
  | horizon + 1 =>
      letI : DecidableEq (FiniteStateOutputPath State BoundaryOut horizon) :=
        finiteStateOutputPathDecidableEq State BoundaryOut horizon
      inferInstanceAs
        (DecidableEq (FiniteStateOutputPath State BoundaryOut horizon ×
          (State × BoundaryOut)))

/-- Last state of a finite state/output path. -/
def finiteStateOutputPathLastState
    {State : Type uState}
    {BoundaryOut : Type uBoundaryOut} :
    ∀ horizon, FiniteStateOutputPath State BoundaryOut horizon → State
  | 0, state => state.down
  | _ + 1, path => path.2.1

/-- State sequence represented by a recursive finite state/output path. -/
def finiteStateOutputPathStates
    {State : Type uState}
    {BoundaryOut : Type uBoundaryOut} :
    ∀ horizon, FiniteStateOutputPath State BoundaryOut horizon → List State
  | 0, state => [state.down]
  | horizon + 1, path =>
      finiteStateOutputPathStates horizon path.1 ++ [path.2.1]

/-- Boundary-output sequence represented by a recursive joint path. -/
def finiteStateOutputPathOutputs
    {State : Type uState}
    {BoundaryOut : Type uBoundaryOut} :
    ∀ horizon, FiniteStateOutputPath State BoundaryOut horizon → List BoundaryOut
  | 0, _ => []
  | horizon + 1, path =>
      finiteStateOutputPathOutputs horizon path.1 ++ [path.2.2]

/-- A finite open-loop experiment with no independently supplied path law. -/
structure FiniteJointOpenExperiment
    (State : Type uState)
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction)
    (BoundaryOut : Type uBoundaryOut)
    [Fintype State]
    [Fintype BoundaryOut] where
  process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut
  horizon : Nat
  initial : FiniteProbabilityMass State
  policy : Nat → JointOpenControl Context BoundaryIn Action

/-- Product-form joint path weight induced from the primitive open process. -/
def inducedJointPathWeightAt
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut)
    (initial : FiniteProbabilityMass State)
    (policy : Nat → JointOpenControl Context BoundaryIn Action) :
    ∀ horizon, FiniteStateOutputPath State BoundaryOut horizon → ℚ
  | 0, state => initial.mass state.down
  | horizon + 1, path =>
      inducedJointPathWeightAt process initial policy horizon path.1 *
        process.mass
          (finiteStateOutputPathLastState horizon path.1)
          (policy horizon) path.2

theorem inducedJointPathWeightAt_nonnegative
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut)
    (initial : FiniteProbabilityMass State)
    (policy : Nat → JointOpenControl Context BoundaryIn Action) :
    ∀ horizon path,
      0 ≤ inducedJointPathWeightAt process initial policy horizon path := by
  intro horizon
  induction horizon with
  | zero =>
      intro path
      exact initial.nonnegative path.down
  | succ prior inductionHypothesis =>
      intro path
      exact mul_nonneg (inductionHypothesis path.1)
        (process.nonnegative
          (finiteStateOutputPathLastState prior path.1)
          (policy prior) path.2)

theorem inducedJointPathWeightAt_normalized
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut)
    (initial : FiniteProbabilityMass State)
    (policy : Nat → JointOpenControl Context BoundaryIn Action) :
    ∀ horizon,
      ∑ path : FiniteStateOutputPath State BoundaryOut horizon,
        inducedJointPathWeightAt process initial policy horizon path = 1 := by
  intro horizon
  induction horizon with
  | zero =>
      calc
        (∑ path : FiniteStateOutputPath State BoundaryOut 0,
          inducedJointPathWeightAt process initial policy 0 path) =
            ∑ state : State, initial.mass state := by
          exact (Fintype.sum_equiv
            (finiteStateOutputPathZeroEquiv State BoundaryOut)
            (fun state => initial.mass state)
            (fun path =>
              inducedJointPathWeightAt process initial policy 0 path)
            (by intro state; rfl)).symm
        _ = 1 := initial.normalized
  | succ prior inductionHypothesis =>
      change
        (∑ path : FiniteStateOutputPath State BoundaryOut prior ×
            (State × BoundaryOut),
          inducedJointPathWeightAt process initial policy prior path.1 *
            process.mass
              (finiteStateOutputPathLastState prior path.1)
              (policy prior) path.2) = 1
      rw [Fintype.sum_prod_type]
      calc
        (∑ pathPrefix : FiniteStateOutputPath State BoundaryOut prior,
          ∑ outcome : State × BoundaryOut,
            inducedJointPathWeightAt process initial policy prior pathPrefix *
              process.mass
                (finiteStateOutputPathLastState prior pathPrefix)
                (policy prior) outcome) =
            ∑ pathPrefix : FiniteStateOutputPath State BoundaryOut prior,
              inducedJointPathWeightAt process initial policy prior pathPrefix *
                (∑ outcome : State × BoundaryOut,
                  process.mass
                    (finiteStateOutputPathLastState prior pathPrefix)
                    (policy prior) outcome) := by
          apply Finset.sum_congr rfl
          intro pathPrefix _
          rw [Finset.mul_sum]
        _ = ∑ pathPrefix : FiniteStateOutputPath State BoundaryOut prior,
              inducedJointPathWeightAt process initial policy prior pathPrefix := by
          apply Finset.sum_congr rfl
          intro pathPrefix _
          rw [process.normalized]
          simp
        _ = 1 := inductionHypothesis

/-- Normalized state/output path law induced by an open experiment. -/
def inducedFiniteStateOutputPathLaw
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (experiment :
      FiniteJointOpenExperiment State Context BoundaryIn Action BoundaryOut) :
    FiniteProbabilityMass
      (FiniteStateOutputPath State BoundaryOut experiment.horizon) where
  mass := inducedJointPathWeightAt experiment.process experiment.initial
    experiment.policy experiment.horizon
  nonnegative := inducedJointPathWeightAt_nonnegative experiment.process
    experiment.initial experiment.policy experiment.horizon
  normalized := inducedJointPathWeightAt_normalized experiment.process
    experiment.initial experiment.policy experiment.horizon

/-- A typed abstraction maps state, both boundary sides, context, and action. -/
structure FiniteJointContextualAbstraction
    (State : Type uState)
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction)
    (BoundaryOut : Type uBoundaryOut)
    (AbstractState : Type uAbstractState)
    (AbstractContext : Type uAbstractContext)
    (AbstractBoundaryIn : Type uAbstractBoundaryIn)
    (AbstractAction : Type uAbstractAction)
    (AbstractBoundaryOut : Type uAbstractBoundaryOut)
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut] where
  fine : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut
  abstract : FiniteJointOpenProcess AbstractState AbstractContext
    AbstractBoundaryIn AbstractAction AbstractBoundaryOut
  stateMap : State → AbstractState
  contextMap : Context → AbstractContext
  boundaryInMap : BoundaryIn → AbstractBoundaryIn
  actionMap : Action → AbstractAction
  boundaryOutMap : BoundaryOut → AbstractBoundaryOut

/-- Deterministic map on one primitive joint outcome. -/
def jointOutcomeMap
    {State : Type uState}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    (stateMap : State → AbstractState)
    (boundaryOutMap : BoundaryOut → AbstractBoundaryOut) :
    State × BoundaryOut → AbstractState × AbstractBoundaryOut :=
  fun outcome => (stateMap outcome.1, boundaryOutMap outcome.2)

/-- Recursive map on finite joint paths. -/
def mapFiniteStateOutputPath
    {State : Type uState}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    (stateMap : State → AbstractState)
    (boundaryOutMap : BoundaryOut → AbstractBoundaryOut) :
    ∀ horizon, FiniteStateOutputPath State BoundaryOut horizon →
      FiniteStateOutputPath AbstractState AbstractBoundaryOut horizon
  | 0, state => ULift.up (stateMap state.down)
  | horizon + 1, path =>
      (mapFiniteStateOutputPath stateMap boundaryOutMap horizon path.1,
        jointOutcomeMap stateMap boundaryOutMap path.2)

/-- Exact one-step commutation of the full joint state/output law. -/
def JointOpenKernelCommutes
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) : Prop :=
  ∀ state context boundary action,
    (jointStepProbability abstraction.abstract
      (abstraction.stateMap state)
      (abstraction.contextMap context,
        abstraction.boundaryInMap boundary,
        abstraction.actionMap action)).mass =
      (pushforwardFiniteProbability
        (jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap)
        (jointStepProbability abstraction.fine state
          (context, boundary, action))).mass

/-- Boundary-output law on the fine side, transported to the abstract output. -/
def transportedFineBoundaryOutputProbability
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [DecidableEq BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut)
    (state : State)
    (control : JointOpenControl Context BoundaryIn Action) :
    FiniteProbabilityMass AbstractBoundaryOut :=
  pushforwardFiniteProbability abstraction.boundaryOutMap
    (jointBoundaryOutputProbability abstraction.fine state control)

/-- Boundary-output law supplied by the abstract joint process. -/
def abstractBoundaryOutputProbability
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut)
    (state : State)
    (control : JointOpenControl Context BoundaryIn Action) :
    FiniteProbabilityMass AbstractBoundaryOut :=
  jointBoundaryOutputProbability abstraction.abstract
    (abstraction.stateMap state)
    (abstraction.contextMap control.1,
      abstraction.boundaryInMap control.2.1,
      abstraction.actionMap control.2.2)

/-- Finite family of primitive states and open inputs. -/
abbrev JointOpenComparisonIndex
    (State : Type uState)
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction) :=
  State × Context × BoundaryIn × Action

/--
Boundary defect derived from the two joint output laws.  It is not a defect of
an independently supplied boundary label.
-/
def jointBoundaryOutputDefect
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype Context]
    [Fintype BoundaryIn]
    [Fintype Action]
    [Fintype BoundaryOut]
    [DecidableEq BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) : ℚ :=
  finiteLawFamilyDefect
    (fun index : JointOpenComparisonIndex State Context BoundaryIn Action =>
      transportedFineBoundaryOutputProbability abstraction index.1
        (index.2.1, index.2.2.1, index.2.2.2))
    (fun index : JointOpenComparisonIndex State Context BoundaryIn Action =>
      abstractBoundaryOutputProbability abstraction index.1
        (index.2.1, index.2.2.1, index.2.2.2))

theorem jointBoundaryOutputDefect_eq_zero_iff_exact
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype Context]
    [Fintype BoundaryIn]
    [Fintype Action]
    [Fintype BoundaryOut]
    [DecidableEq BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) :
    jointBoundaryOutputDefect abstraction = 0 ↔
      FiniteLawFamilyExact
        (fun index : JointOpenComparisonIndex State Context BoundaryIn Action =>
          transportedFineBoundaryOutputProbability abstraction index.1
            (index.2.1, index.2.2.1, index.2.2.2))
        (fun index : JointOpenComparisonIndex State Context BoundaryIn Action =>
          abstractBoundaryOutputProbability abstraction index.1
            (index.2.1, index.2.2.1, index.2.2.2)) :=
  finiteLawFamilyDefect_eq_zero_iff_exact _ _

/-- Two experiments sharing one horizon; transport alignment is a separate gate. -/
structure AlignedJointOpenExperiments
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) where
  horizon : Nat
  fineInitial : FiniteProbabilityMass State
  abstractInitial : FiniteProbabilityMass AbstractState
  finePolicy : Nat → JointOpenControl Context BoundaryIn Action
  abstractPolicy : Nat →
    JointOpenControl AbstractContext AbstractBoundaryIn AbstractAction

/-- Exact transport of initial law and every policy input used by the horizon. -/
structure JointExperimentTransportAlignment
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    [Fintype AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointOpenExperiments abstraction) where
  initial_transport :
    data.abstractInitial.mass =
      (pushforwardFiniteProbability abstraction.stateMap data.fineInitial).mass
  policy_transport : ∀ step, step < data.horizon →
    data.abstractPolicy step =
      (abstraction.contextMap (data.finePolicy step).1,
        abstraction.boundaryInMap (data.finePolicy step).2.1,
        abstraction.actionMap (data.finePolicy step).2.2)

def AlignedJointOpenExperiments.fineExperiment
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointOpenExperiments abstraction) :
    FiniteJointOpenExperiment State Context BoundaryIn Action BoundaryOut where
  process := abstraction.fine
  horizon := data.horizon
  initial := data.fineInitial
  policy := data.finePolicy

def AlignedJointOpenExperiments.abstractExperiment
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointOpenExperiments abstraction) :
    FiniteJointOpenExperiment AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut where
  process := abstraction.abstract
  horizon := data.horizon
  initial := data.abstractInitial
  policy := data.abstractPolicy

/-- Fine joint path law transported through both state and output maps. -/
def transportedFineJointPathLaw
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointOpenExperiments abstraction) :
    FiniteProbabilityMass
      (FiniteStateOutputPath AbstractState AbstractBoundaryOut data.horizon) :=
  pushforwardFiniteProbability
    (mapFiniteStateOutputPath abstraction.stateMap abstraction.boundaryOutMap
      data.horizon)
    (inducedFiniteStateOutputPathLaw data.fineExperiment)

/-- Exact finite path-law stitching defect for aligned joint experiments. -/
def jointOpenPathStitchingDefect
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointOpenExperiments abstraction) : ℚ :=
  finiteTotalVariation (transportedFineJointPathLaw data)
    (inducedFiniteStateOutputPathLaw data.abstractExperiment)

theorem jointOpenPathStitchingDefect_eq_zero_iff_exact
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointOpenExperiments abstraction) :
    jointOpenPathStitchingDefect data = 0 ↔
      (transportedFineJointPathLaw data).mass =
        (inducedFiniteStateOutputPathLaw data.abstractExperiment).mass :=
  finiteTotalVariation_eq_zero_iff_mass_eq _ _

end OCMaturityCompletionCycle
